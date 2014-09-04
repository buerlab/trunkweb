#encoding=utf-8
from dbmodels import *
from functools import wraps
import tornado
from models.backends.motorBackend import *
from motor import Op
from utils import *

__author__ = 'zhongqiling'


def ut(func):
    @coroutine
    def wrapFunc(*args, **kwargs):
        print "******** "+func.__name__+" BEGIN********"
        yield func(*args, **kwargs)
        print "******** "+func.__name__+" FINISHED********"
    return wrapFunc

@ut
@coroutineDebug
@coroutine
def testAddUser():
    kwargs = {"nickName":"小钟", "password":"fine", "userName":"zql"}
    user = User.from_db(kwargs)
    user.regtime = time.time()
    yield user.save()

@ut
@coroutine
def testSendBill():
    kwargs = {'trunkWeight':"1600.0", 'fromAddr':u'釜山', 'toAddr':u'落砂机', 'billType': BillType.TRUNK}
    bill = Bill.from_db(kwargs)
    bill.billTime = str(time.time())
    print "bill init"
    user = yield User.get("53ba3519c3666ea7c56acc2a")
    print "get user done"
    if user:
        bill2 = yield user.sendBill(bill)
        bill3 = bill2.to_client()
        print "sendbill done, get bill", bill3
        for k in bill3:
            print k+" : "+bill3[k]

@ut
@coroutine
def testRemoveBill():

    bill = yield Bill.findOne(fromAddr="北京")
    print "got bill", Bill
    if bill and bill.sender:
        yield bill.remove()
        print "remvoe done"

@ut
@coroutine
def testGetDoc():
    user = yield User.get("53ba3519c3666ea7c56acc2a")
    print user


@ut
@coroutineDebug
@coroutine
def testGetHistory():
    user = yield User.get("53ba3519c3666ea7c56acc2a")
    bills = yield user.getHistoryBill(BillType.TRUNK, ObjectId("53ba5544c3666eacbb0c8a2d"), False)
    print bills

@ut
@coroutine
def testGetBills():
    user = yield User.get("53ba3519c3666ea7c56acc2a")
    bills = yield user.getBills(BillType.TRUNK)
    returnBills = [b.to_client() for b in bills]
    print returnBills

@ut
@coroutine
def testRemoveBill():
    user = yield User.get("53bbb0c3c3666ec2b077ee8f")
    bill = yield Bill.get("53bc32abc3666eccf399e432")
    bills = yield user.removeBill(bill)
    if bills:
        print "remove ok"


def testAddrComp():
    print addr_compare("北京-昌平", "北京-昌平")
    print addr_compare("a-b", "c-d-e")
    print addr_compare("a-c", "a-d")
    print addr_compare("a-b-c", "a-b-c")
    print addr_compare("a-b-o", "a-b-c")


def testAddrAnalysis():
    addrs = ["a-b-c", "a-o-f","m-f-e","m-p","m-o","r-t-y", "a-b-p"]
    print addrsAnalysis(addrs)





@coroutine
def testCall():
    # yield testSendBill()
    testAddrAnalysis()

if __name__ == "__main__":
    testAddrAnalysis()
    # connect("mongodb://localhost:27017")
    #
    # tornado.ioloop.IOLoop.instance().add_callback(testCall)
    # tornado.ioloop.IOLoop.instance().start()