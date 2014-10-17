#encoding=utf-8

__author__ = 'zhongqiling'

from commons import Singleton, singleton
from appmodels import BillType, BillState, UserLevel, oppsiteBillType, matchUserType
from utils import getCity
from mylog import mylog, getLogText
from dbmodels import Bill, User
from models.defines import coroutineDebug
from tornado.gen import coroutine
from Queue import Queue
import time

from wechatUtils import billToWechat
from jpush.JPushService import JPushNotifyToId, JPushMsgToId, createGetMatchBillMsg

# from jobs import PushRecomendBillJob

def makeAddrKey(fromAddr, toAddr):
    try:
        fromCity, toCity = getCity(fromAddr), getCity(toAddr)
        return fromAddr+"->"+toAddr if fromCity == toCity else fromCity+"->"+toCity
    except Exception, e:
        print "error", e.message
        return ""

#将一个新单匹配城市后加入map
def matchCity(result, bill):
    billType = bill.billType
    if not billType in (BillType.GOODS, BillType.TRUNK):
        return
    cityKey = makeAddrKey(bill.fromAddr, bill.toAddr)
    if cityKey:
        if not cityKey in result:
            result[cityKey] = {BillType.TRUNK: [], BillType.GOODS: []}
        result[cityKey][billType].append({"id": str(bill.id), "matcher": BillMatcher(bill)})
    else:
        mylog.getlog().error("ADD BILL ERROR, ADDR IS INVALID")

#length:(trunkload, trunkVolume)
trunkData = {
    4.2: (5, 18),
    4.3: (5, 18),
    4.6: (5, 15),
    5.2: (8, 20),
    5.8: (10, 26),
    6.2: (10, 30),
    6.5: (12, 35),
    6.8: (15, 35),
    7.6: (15, 45),
    9.6: (25, 60)
}


class BillMatcher(object):
    value = None
    volumeExtra = 5

    def __init__(self, bill):
        self.type = bill.billType
        if self.type == BillType.GOODS:
            self.value = [bill.weight, bill.volume, bill.trunkLength]
        elif self.type == BillType.TRUNK:
            self.value = [bill.trunkLength, bill.trunkLoad, bill.trunkType]

    def match(self, targetMatcher):
        if self.type == targetMatcher.type:
            return -1
        print self.value, " match: ", targetMatcher.value
        if self.type == BillType.TRUNK:
            return BillMatcher.getMark(self.value, targetMatcher.value)
        elif self.type == BillType.GOODS:
            return BillMatcher.getMark(targetMatcher.value, self.value)
        return -1

    @staticmethod
    def getMark(trunkValue, goodsValue):
        '''
        如果重量和体积，如果有一个参数为空，则得分为0， 否则返回一个按间隔大小的减函数或者，任一个不匹配的返回-1
        :param trunkValue:
        :param goodsValue:
        :return:
        '''
        trunkweight, trunkvolume, trunklength = trunkValue[1], None, trunkValue[0]
        goodsweight, goodsvolume, goodsReqLength = goodsValue[0], goodsValue[1], goodsValue[2]

        #如果车长有效，则根据车长来估算载重和容积的默认值
        if trunkValue[0] and trunkValue[0] in trunkData:
            data = trunkData[trunkValue[0]]
            #如果是非厢车，可以加上额外的容积
            extra = BillMatcher.volumeExtra if trunkValue[2] != u"厢车" else 0
            #优先使用传入的载重，否则用根据车长估计的载重
            trunkweight, trunkvolume = trunkValue[1] or data[0], data[1]+extra

        #这里计算权值用2的负指数函数，因为需要一个支持x为0，当x>0，函数值永远大于0的减函数
        if trunkweight and goodsweight:
            wMark = 2**(goodsweight-trunkweight) if trunkweight >= goodsweight else -1
        else:
            wMark = 0

        if trunkvolume and goodsvolume:
            vMark = 2**(goodsvolume-trunkvolume) if trunkvolume >= goodsvolume else -1
        else:
            vMark = 0

        if trunklength and goodsReqLength:
            lMark = 2**(goodsReqLength-trunklength) if trunklength >= goodsReqLength else -1
        else:
            lMark = 0

        return wMark + vMark + lMark if wMark >= 0 and vMark >= 0 and lMark >= 0 else -1



class PushRecomendBillQueue(Queue):

    def sendMsg(self, jpushId, userId, userType):
        try:
            if jpushId and userId and userType:
                self.put({"jpushId":jpushId, "userId":str(userId), "userType":userType, "addTime": time.time()})
        except Exception, e:
            pass

class TextMsgQueue(Queue):

    def sendMsg(self, billId, recommendBillId, sendTime, validTimeSec, sendTo, phonenum, nickname, _from, _to, _type, comment):
        try:
            if sendTo and phonenum and _from and _to and _type:
                print "textmsg queue send text msg", billId, "from", _from, "to ", _to
                self.put({"billId":billId, "recomendBillId": recommendBillId, "sendTime":sendTime, "validTimeSec": validTimeSec, "sendTo":sendTo, "phonenum":phonenum,\
                          "nickname":nickname, "from":_from, "to": _to, "type":_type, "addTime":time.time(), "comment":comment})
        except Exception, e:
            pass


class WechatMsgQueue(Queue):

    def sendMsg(self, wechatId, content):
        self.put({"wechatId":wechatId, "content":content})

@singleton
class BillMatchController(object):
    billMatchMap = {}
    # pushQueue = PushRecomendBillQueue()
    # textMsgQueue = TextMsgQueue()

    def __init__(self):
        self.pushQueue = PushRecomendBillQueue()
        self.textMsgQueue = TextMsgQueue()
        self.wechatMsgQueue = WechatMsgQueue()

    @coroutineDebug
    @coroutine
    def initFromDB(self):
        self.billMatchMap = {}
        cursor = Bill.get_collection().find({"state":BillState.WAIT})
        count = yield cursor.count()
        mylog.getlog().info(getLogText("BILL MATCH INIT FROM DB, GET BILL COUNT: ", str(count)))
        if count > 0:
            while (yield cursor.fetch_next):
                billDoc = cursor.next_object()
                bill = Bill.from_db(billDoc)
                matchCity(self.billMatchMap, bill)
        print self.billMatchMap


    @coroutineDebug
    @coroutine
    def sendBill(self, bill):
        mylog.getlog().info("----bill match controller send bill")
        matchCity(self.billMatchMap, bill)
        matchBillIds = self.getMatchBills(bill)
        if len(matchBillIds) > 0:
            mylog.getlog().info("----%d match"%len(matchBillIds))
            self.readyToJPush(bill)

            for billId in matchBillIds:
                iterBill = yield Bill.get(billId)
                if iterBill:
                    self.readyToJPush(iterBill)
                    if bill.phoneNum and iterBill.phoneNum and bill.phoneNum != iterBill.phoneNum:
                        mylog.getlog().info("----send bill and ready to text msg")
                        self.readyToTextMsg(bill, iterBill)
                        self.readyToTextMsg(iterBill, bill)


            #发送一个push给三星的手机
            # JPushNotifyToId("0806fa24854", "找到匹配的单子了",  "driver")


    @coroutineDebug
    @coroutine
    def readyToJPush(self, bill):
        mylog.getlog().info("----process bill id: %s"%bill.id)
        if bill.sender:
            sender = yield User.get(bill.sender, matchUserType(bill.billType))
            if sender and sender.level == UserLevel.NORMAL and sender.getAttr("JPushId"):
                mylog.getlog().info(getLogText("--process bill send msg ",sender.getAttr("JPushId"), sender.id, sender.currType))
                self.pushQueue.sendMsg(sender.getAttr("JPushId"), sender.id, sender.currType)


    @coroutineDebug
    @coroutine
    def readyToTextMsg(self, targetBill, recommendBill):
        sender = None
        if targetBill.sender:
            sender = yield User.get(targetBill.sender, matchUserType(targetBill.billType))
            phone1 = targetBill.phoneNum or targetBill.wechatPhoneNum
            phone2 = recommendBill.phoneNum or recommendBill.wechatPhoneNum
            if (sender and sender.level == UserLevel.MANAGER and phone1 and phone2) or not sender:
                self.textMsgQueue.sendMsg(targetBill.id, recommendBill.id, targetBill.sendTime, targetBill.validTimeSec, phone1, \
                                          phone2, targetBill.senderName, recommendBill.fromAddr, \
                                          recommendBill.toAddr, targetBill.billType, recommendBill.comment)
            elif sender and sender.level == UserLevel.WECHAT and phone2:
                print "send test to wechat~~~~"
                # self.wechatMsgQueue.sendMsg(sender.wechatId, "hello world")
                self.wechatMsgQueue.sendMsg(sender.wechatId, "找到匹配单子:\n"+billToWechat(recommendBill))


    def removeBill(self, bill):
        mylog.getlog().info(getLogText("--bill match control remove bill: "))
        cityKey = makeAddrKey(bill.fromAddr, bill.toAddr)
        billId = str(bill.id)
        if billId and cityKey in self.billMatchMap:
            for item in self.billMatchMap[cityKey][bill.billType]:
                if billId == item["id"]:
                    self.billMatchMap[cityKey][bill.billType].remove(item)
                    break

    def isMatch(self, bill):
        return len(self.getMatchBills(bill)) > 0

    #返回匹配的单子id
    def getMatchBills(self, bill):
        matchBillDict = self.getMatchDict(bill)
        return [item[1] for item in matchBillDict]

    def getMatchDict(self, bill):
        findType  = oppsiteBillType(bill.billType)
        addrKey = makeAddrKey(bill.fromAddr, bill.toAddr)
        if addrKey in self.billMatchMap and len(self.billMatchMap[addrKey][findType])>0:
            # print "billmatch map", self.billMatchMap
            matchResult = [(BillMatcher(bill).match(item["matcher"]), item["id"]) for item in self.billMatchMap[addrKey][findType]]

            matchResult = filter(lambda item: item[0] >= 0, matchResult)
            if len(matchResult) > 0:
                matchResult = sorted(matchResult, key=lambda item: item[0], reverse=True)
            print "match result", matchResult
            return matchResult
        else:
            return []

    def getMatchMap(self):
        mylog.getlog().info(getLogText("get match map "))
        #如果结果里面司机或者货主list里面有一个是空得，应该filter掉
        result = {}
        for k, v in self.billMatchMap.iteritems():
            branch = {}
            for k2, v2 in v.iteritems():
                if not v2:
                    branch = {}
                    break
                branch[k2] = [item["id"] for item in v2]
            if branch:
                result[k] = branch

        return result



