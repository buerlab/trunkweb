#encoding=utf-8

__author__ = 'zhongqiling'

from utils import *
from jpush.JPushService import *


class Job(object):

    def execute(self):
        pass


@coroutine
def jobsEveryMin():
    yield handleBillRequest()

@coroutineDebug
@coroutine
def handleBillRequest():
    reqs = yield PendingRequest.findMul(0, 1000, state=PendingReqState.WAITING)
    if reqs:
        print "bill request, got %d reqs,"%len(reqs)
        for req in reqs:
            print "sender:", req.reqUser, "receive:", req.respUser
            sender = yield User.get(req.reqUser)
            receiver = yield User.get(req.respUser)
            bill = yield Bill.get(req.reqBill)
            if sender and receiver:
                pushId = receiver.driverJPushId if bill.billType == BillType.TRUNK else receiver.ownerJPushId
                pushData = createBillReqMsg(sender.nickName, str(req.id))
                JPushMsgToId(pushId, pushData)
                req.state = PendingReqState.PUSHED
                yield req.save()

@coroutine
def jobsEvery5Mins():
    mylog.getlog().info("jobs start")

    yield billOverDueCheck()



@coroutineDebug
@coroutine
def billOverDueCheck():

    bills = yield Bill.findMul(0, 100, state=BillState.WAIT)
    if bills:
        overdueBills = [bill for bill in bills if bill.isOverDue()]
        if overdueBills:
            print "found bill:", len(overdueBills)
            for bill2 in overdueBills:
                if getattr(bill2, "sender", None):
                    senderUser = yield User.get(bill2.sender)
                    if senderUser:
                        if bill2.billType == BillType.TRUNK and bill2.id in senderUser.driverBills:
                            senderUser.driverBills.remove(bill2.id)
                            senderUser.driverHistoryBills.append(bill2.id)
                            yield senderUser.save()
                        elif bill2.billType == BillType.GOODS and bill2.id in senderUser.ownerBills:
                            senderUser.ownerBills.remove(bill2.id)
                            senderUser.ownerHistoryBills.append(bill2.id)
                            yield senderUser.save()
                    bill2.state = BillState.OVERDUE
                    yield bill2.save()
                    print "overdue a bill"
                else:
                    print "sendtime wrong"
    print "overdue check done"
    raise Return(None)
