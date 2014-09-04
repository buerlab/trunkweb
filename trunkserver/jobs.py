#encoding=utf-8

__author__ = 'zhongqiling'

from utils import *
from jpush.JPushService import *
from datetime import datetime, timedelta
import time
from billmatchcontroller import BillMatchController

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
                        print "jpush "
                        JPushMsgToId(receiver.getAttr("JPushId"), pushData, receiver.currType)


class JobHandler(object):

    def __init__(self, job):
        self.mJob = job

    def executeJob(self):
        self.mJob.execute()

    def __enter__(self):
        self.mJob.state = JobState.DOING

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mJob.state = JobState.DONE


class JobsManager(object):

    def __init__(self):
        self.jobs = [BillReqJob()]

    def update(self):
        for job in self.jobs:
            if job.state == JobState.TO_DO or job.state == JobState.DONE:
                job.state = JobState.DOING
                job.execute()
                job.state = JobState.DONE

                # with JobHandler(job) as handler:
                #     job.execute()


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






















