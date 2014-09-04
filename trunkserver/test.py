#encoding=utf-8
import httplib, urllib
import urllib2, cookielib
from models import *
import json
from dataprotocol import *
from dbservice import *
import time
from threading import Thread
from dbmodels import Bill
from jpush.JPushService import JPushMsgToId, createRecomendBillMsg
from billmatchcontroller import BillMatchController


# addr = "http://127.0.0.1:9288/"
addr = "http://115.29.8.74:9288/"


def test(func):
    def testFunc(*args, **kwargs):
        if not func(*args, **kwargs):
            print "***********ERROR IN PROCEEDING FUNC:", func.__name__
            raise AssertionError()
    return testFunc

def count(func):
    def countFunc(*args, **kwargs):
        begin = time.time()
        print "-------%s begin at%f----------"%(func.__name__, begin)
        result = func(*args, **kwargs)
        print "**********%s end after %f*******"%(func.__name__, time.time()-begin)
        return result
    return countFunc

def createParms(dict = None):
    parms = dict or {}
    # parms["userId"] = "53e9cd5915a5e45c43813d1c"
    parms["userType"] = UserType.OWNER

    return urllib.urlencode(parms)


def handleResult(respData):
    if respData:
        result = json.loads(respData)
        print "-----get result"
        return result
    else:
        return None


def createOpener():
    cookie = cookielib.MozillaCookieJar("cookie.txt")
    cookie.load("cookie.txt")
    handler=urllib2.HTTPCookieProcessor(cookie)
    return urllib2.build_opener(handler)


def cookieRequst(url, data):
    cookie = cookielib.MozillaCookieJar("cookie.txt")

    handler = urllib2.HTTPCookieProcessor(cookie)
    opener = urllib2.build_opener(handler)
    req = urllib2.Request(url, data)
    resp = opener.open(req)
    respData = resp.read()
    cookie.save("cookie.txt")
    return handleResult(respData)


def testUser():
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    parms = urllib.urlencode({"username":"zql","password":"fine"})
    req = urllib2.Request("http://127.0.0.1:9288/", parms, headers)
    resp = createOpener().open(req)
    print resp.read()

@test
def testRegister():
    data = urllib.urlencode({"username":"zql","password":"fine"})
    return cookieRequst(addr+"api/admin/register", data)

@test
def testLogin():
    return cookieRequst(addr+"api/admin/login", createParms())


def testMain():
    data = urllib.urlencode({"username":"zql","password":"fine"})
    cookie = cookielib.MozillaCookieJar("cookie.txt")
    handler = urllib2.HTTPCookieProcessor(cookie)
    opener = urllib2.build_opener(handler)
    req = urllib2.Request("http://127.0.0.1:9288/", data)
    resp = opener.open("http://127.0.0.1:9288")
    print resp.read()


def testBill():
    billDict = {
        "userType":"owner",
        "billType":"goods",
        "fromAddr":"海豚湾",
        "toAddr":"广州",
        "price":1000,
        "weight":1000,
        "material":"wood"
    }
    result = cookieRequst(addr+"api/bill/send", createParms(billDict))
    print result


def testGetBill():
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    data = urllib.urlencode({"username":"zql", "from":"深圳"})
    req = urllib2.Request("http://127.0.0.1:9288/bill?"+data, headers=headers)
    resp = createOpener().open(req)
    print "response:", resp.read()

@count
@test
def testGetRecomendBills():
    return cookieRequst(addr+"api/bill/recomend", createParms())

@test
def testBillCall():
    return cookieRequst(addr+"api/bill/call", createParms())

@test
def testDb():
    service = DbService()
    service.getUserHistoryBills()


def testJPush():
    bill = Bill()
    bill.id = "53fea6187938ee47dd2e8d00"
    bill.billType = BillType.TRUNK
    bill.senderName = "clajf"
    bill.fromAddr = "广州"
    bill.toAddr = "深圳"
    bill.sender = "53fea6187938ee47dd2e8d00"
    JPushMsgToId("0708483b05b", createRecomendBillMsg("53fea6187938ee47dd2e8d00", bill.to_client()), UserType.DRIVER)

class NetReq(Thread):
    def run(self):
        testGetRecomendBills()

#
def testMatchCity():

    billDocs = [{"_id":1, "fromAddr":"广东-广州-白云", "toAddr":"广东-深圳-南山", "billType":BillType.TRUNK},
             {"_id":2, "fromAddr":"广东-广州-白云", "toAddr":"广东-中山-东升", "billType":BillType.GOODS},
             {"_id":3, "fromAddr":"广东-深圳-南山", "toAddr":"广东-中山-东升", "billType":BillType.TRUNK},
             {"_id":4, "fromAddr":"a-b-c", "toAddr":"a-e-l", "billType":BillType.TRUNK},
             {"_id":5, "fromAddr":"广东-广州-白云", "toAddr":"广东-深圳-南山", "billType":BillType.GOODS},
             {"_id":6, "fromAddr":"广东-深圳-南山", "toAddr":"广东-中山-东升", "billType":BillType.GOODS},
             {"_id":7, "fromAddr":"广东-广州-白云", "toAddr":"广东-中山-东升", "billType":BillType.TRUNK}]


    result = {}
    for b in billDocs:
        BillMatchController().sendBill(Bill.from_db(b))
    BillMatchController().removeBill(Bill.from_db(billDocs[3]))
    for k, v in BillMatchController().billMatchMap.items():
            print k
            print v

def testGetMatch():
    result = cookieRequst(addr+"api/get_match", createParms())
    if not result:
        return
    data = result["data"]
    if data:
        for k, v in data.items():
            print k
            print v

def testRegular():
    regular = {
        "name": "kk",
        "phoneNum": "123456",
        "type": UserType.DRIVER,
    }

    result = cookieRequst(addr+"api/regular/add", createParms(regular))
    print result

def testRemoveRegular():
    route = json.dumps({"from":"guangdong", "to":"beijing", "probability":1})
    data = {"id":"54048d24c3666e8012e79a16"}
    result = cookieRequst(addr+"api/regular/remove", createParms(data))
    print result["msg"]

def testGetRegular():
    result = cookieRequst(addr+"api/regular/get", createParms())
    print result

if __name__ == "__main__":
    #
    # for i in range(5):
    #     # NetReq().start()
    # testGetRecomendBills()
    testRegular()


