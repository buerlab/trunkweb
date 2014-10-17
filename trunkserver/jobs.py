#encoding=utf-8

__author__ = 'zhongqiling'

from utils import *
from jpush.JPushService import *
import time
from datetime import datetime, timedelta
from datetime import time as dTime
from billmatchcontroller import BillMatchController
from commons import singleton
from jpush.YunPianRegCodeService import YunPianMsgMatch2
from dbmodels import BillMatchMsgRecord
from Queue import Queue
from wechatserver import wechatComander, SendTextComand

from httplib import HTTPConnection
from urllib import urlencode

class JobState(object):
    TO_DO = "todo"
    DOING = "doing"
    DONE = "done"

class Job(object):

    state = JobState.TO_DO

    def execute(self):
        pass

class BillReqJob(Job):

    @coroutineDebug
    @coroutine
    def execute(self):
        if self.state != JobState.DOING:
            self.state = JobState.DOING
            cursor = PendingRequest.get_collection().find({"state":PendingReqState.WAITING})
            count = yield cursor.count()
            if count > 0:
                while (yield cursor.fetch_next):
                    reqDoc = cursor.next_object()
                    req = PendingRequest.from_db(reqDoc)
                    req.state = PendingReqState.PUSHED
                    yield req.save()

                    print "----handle request", req.id
                    sender = yield User.get(req.reqUser, req.reqUserType)
                    receiver = yield User.get(req.respUser, req.respUserType)
                    if sender and receiver:
                        pushData = None
                        if req.reqType == RequestType.Bill:
                            count = yield Bill.objects({"_id":req.reqBill}).count()
                            pushData = createBillReqMsg(str(receiver.id), sender.nickName, str(req.id))
                        elif req.reqType == RequestType.HistoryBill:
                            count = yield HistoryBill.objects({"_id":req.reqBill}).count()
                            pushData = createHistoryBillReqMsg(str(receiver.id), sender.nickName, str(req.id), req.reqBill)

                        if count >0 and pushData and receiver.getAttr("JPushId"):
                            JPushMsgToId(receiver.getAttr("JPushId"), pushData, receiver.currType)
            self.state = JobState.DONE


@singleton
class BillMatchPushJob(Job):

    def __init__(self):
        self.pushedDict = {}
        #两次发送的最小间隔（分钟）
        self.sendIntervalMin = 2
        #每个push消息的从添加到队列算起的可以等待的有效时间
        self.msgValidMin = 20

    def execute(self):
        now = datetime.now()
        msgQueue = BillMatchController().pushQueue
        msgToPush, msgToWait = None, Queue()

        while not msgToPush:
            if msgQueue.empty():
                break

            msg = msgQueue.get()
            key = msg["userId"]+msg["userType"]

            if not key in self.pushedDict:
                self.pushedDict[key] = datetime.fromtimestamp(0)

            if now - self.pushedDict[key] >= timedelta(minutes=self.sendIntervalMin):
                self.pushedDict[key] = now
                msgToPush = msg
            #如果push消息在有效期内，继续排队
            elif now - datetime.fromtimestamp(msg["addTime"]) <= timedelta(minutes=self.msgValidMin):
                msgToWait.put(msg)

        while not msgToWait.empty():
            msgQueue.put(msgToWait.get())

        if msgToPush and msgToPush["jpushId"] and msgToPush["userId"] and msgToPush["userType"]:
            mylog.getlog().info(getLogText("---push msg to", msgToPush["jpushId"], " userid", msgToPush["userId"]))
            JPushMsgToId(msgToPush["jpushId"], createGetMatchBillMsg(msgToPush["userId"]), msgToPush["userType"])


@singleton
class BillMatchSendMsgJob(Job):

    def __init__(self):
        self.sentDict = {}
        with open("sendmsg", "r") as f:
            try:
                print "get dict"
                self.sentDict = json.load(f)
            except Exception, e:
                print "load dict error,", e.message

        #指单子发送时间后的一段时间内才发送推荐短信(小时)
        self.billValidHours = 1
        #两次发送的最小间隔（分钟）
        self.sendIntervalMin = 5
         #每个push消息的从添加到队列算起的可以等待的有效时间，对象CD没有结束会继续排队等候
        self.msgValidMin = 40
        #每个单子最大可以推送的短信数量
        self.numLimitPerBill = 3
        #每个单子最大的可以被推送的数量
        self.exposeNumLimitPerBill = 4
        #推送的时间段
        self.timePeriodFrom = dTime(5)
        self.timePeriodTo = dTime(22)
        #每天总共可以发送的数量
        self.numlimitTotal = 500
        self.sendMsgNumCount = 0

    def execute(self):
        if self.state != JobState.DOING:
            self.state = JobState.DOING

            now = datetime.now()
            msgQueue = BillMatchController().textMsgQueue
            msgToPush, msgToWait = None, Queue()

            #删除所有过期单子的记录
            for k,v in self.sentDict.items():
                if datetime.fromtimestamp(v["dueTime"]) < now:
                    del self.sentDict[k]

            while not msgToPush:
                if msgQueue.empty():
                    break

                msg = msgQueue.get()
                #在正常的作息时间内才发送短信
                if self.timePeriodFrom < now.time() < self.timePeriodTo and self.sendMsgNumCount < self.numlimitTotal:

                    if not msg["billId"] in self.sentDict:
                        self.sentDict[msg["billId"]] = {"last": datetime.fromtimestamp(0), "total": 0, "expose": 0, "dueTime":0}

                    if not msg["recomendBillId"] in self.sentDict:
                        self.sentDict[msg["recomendBillId"]] = {"last": datetime.fromtimestamp(0), "total": 0, "expose":0, "dueTime":0}

                    record = self.sentDict[msg["billId"]]
                    recomendBillRecord = self.sentDict[msg["recomendBillId"]]

                    #满足 有效时间内，发送指定对象短信的总数在限制内， 距上一次时间间隔在规定的间隔之外
                    if datetime.fromtimestamp(msg["sendTime"])+timedelta(hours=self.billValidHours) >= now:
                        #当对象发送的总次数在限度内，且被推荐的单子被推荐的总次数在限度内
                        if record["total"] < self.numLimitPerBill and recomendBillRecord["expose"] < self.exposeNumLimitPerBill:
                            #距离上次发送的时间在规定的限度内
                            if now - record["last"] >= timedelta(minutes=self.sendIntervalMin):
                                record["last"] = now
                                record["total"] += 1
                                record["dueTime"] = msg["sendTime"]+msg["validTimeSec"]

                                recomendBillRecord["expose"] += 1
                                self.sendMsgNumCount += 1
                                msgToPush = msg
                            #如果发送对象等待时间还没到，且单子的还在有效时间之内，放回队列继续排队
                            elif now - datetime.fromtimestamp(msg["addTime"]) <= timedelta(minutes=self.msgValidMin):
                                msgToWait.put(msg)

            while not msgToWait.empty():
                msgQueue.put(msgToWait.get())

            if msgToPush and msgToPush["sendTo"] and msgToPush["phonenum"]:
                _type = matchUserType(msgToPush["type"])
                self.recordToDb(msgToPush, _type)
                fromAddr, toAddr = getAddrShort(msgToPush["from"], " "), getAddrShort(msgToPush["to"], " ")
                mylog.getlog().info(getLogText("id: ", msgToPush["billId"], "fromaddr", fromAddr, "toAddr", toAddr))
                YunPianMsgMatch2().send(msgToPush["sendTo"], _type, u"你好", fromAddr, toAddr, msgToPush["comment"])

            self.state = JobState.DONE


    @coroutineDebug
    @coroutine
    def recordToDb(self, msgToPush, _type):
        record = BillMatchMsgRecord()
        record.sendTo, record.recPhoneNum, record.nickName = msgToPush["sendTo"], msgToPush["phonenum"], msgToPush["nickname"]
        record.fromAddr, record.toAddr, record.type = msgToPush["from"],msgToPush["to"], _type
        record.billId, record.comment = msgToPush["billId"], msgToPush["comment"]
        record.addTime = time.time()
        yield record.save()


def wechatMsgHandle():

    msgQueue = BillMatchController().wechatMsgQueue
    if not msgQueue.empty():
        msg = msgQueue.get()
        print "handle wechat msg:", msg
        wechatComander.addComand(SendTextComand(msg["wechatId"], msg["content"]))
        # query = {"token": "buerlab", "wechatId":msg["wechatId"], "content": msg["content"]}
        # data = urlencode(query)
        #
        # conn = HTTPConnection("localhost:80")
        # conn.request("GET", "/wechat/send?"+data)
        # resp = conn.getresponse()
        # print resp.read()


billReqJob = BillReqJob()
billMatchPushJob = BillMatchPushJob()
billMatchSendMsgJob = BillMatchSendMsgJob()

prevDay = datetime.now().date().day
def jobsUpdate():
    global prevDay

    billReqJob.execute()
    billMatchPushJob.execute()
    billMatchSendMsgJob.execute()
    wechatMsgHandle()
    wechatComander.execute()

    now = datetime.now()
    if now.date().day != prevDay:
        jobsEveryDay()
    prevDay = now.date().day


@coroutine
def jobsEveryMin():
    # yield handleBillRequest()
    pass

def jobsEvery5Mins():
    mylog.getlog().info("--5 mins jobs start")
    overDueBills()
    finishRequest()


@coroutineDebug
@coroutine
def jobsEvery5Hours():
    mylog.getlog().info("==5 hours jobs start")


def jobsEveryDay():
    mylog.getlog().info("==every day job start")
    billMatchSendMsgJob.numlimitTotal = 0


def jobsStop():
    with open("sendmsg", "w") as f:
        json.dump(BillMatchSendMsgJob().sentDict, f)


@coroutineDebug
@coroutine
def overDueBills():
    cursor = Bill.get_collection().find({"state":BillState.WAIT})
    count = 0
    while (yield cursor.fetch_next):
        billDoc = cursor.next_object()
        bill = Bill.from_db(billDoc)
        if bill.isOverDue():
            if bill.sender:
                bill.state = BillState.OVERDUE
                yield bill.save()
            else:
                yield bill.remove()
            BillMatchController().removeBill(bill)
            count += 1
    if count > 0:
        mylog.getlog().info("--%d""bills are overdued!!"%count)


@coroutineDebug
@coroutine
def finishRequest():
    yield PendingRequest.objects({"state":PendingReqState.FINISHED}).remove()






















