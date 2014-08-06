#encoding=utf-8
import httplib, urllib
import urllib2, cookielib
from models import *
import json
from dataprotocol import *
from dbservice import *

addr = "http://127.0.0.1:9288/"
# addr = "http://115.29.8.74:9288/"


def test(func):
    def testFunc(*args, **kwargs):
        if not func(*args, **kwargs):
            print "***********ERROR IN PROCEEDING FUNC:", func.__name__
            raise AssertionError()
    return testFunc


def createParms(dict = None):
    parms = dict or {}
    parms["userId"] = "5383f03fc3666e506894b080"
    parms["userType"] = UserType.OWNER
    parms["username"] = "zql"
    parms["password"] = "fine"
    return urllib.urlencode(parms)


def handleResult(respData):
    if respData:
        result = json.loads(respData)
        print result
        return result["code"] == DataProtocol.SUCCESS
    else:
        return False


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


@test
def testBill():
    billDict = {
        "userType":"owner",
        "billType":"goods",
        "fromAddr":"深圳",
        "toAddr":"广州",
        "price":1000,
        "weight":1000,
        "material":"wood"
    }
    return cookieRequst(addr+"api/bill/send", createParms(billDict))


def testGetBill():
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    data = urllib.urlencode({"username":"zql", "from":"深圳"})
    req = urllib2.Request("http://127.0.0.1:9288/bill?"+data, headers=headers)
    resp = createOpener().open(req)
    print "response:", resp.read()

def testGetRecomendBills():
    return cookieRequst(addr+"api/bill/recomend", createParms())

@test
def testBillCall():
    return cookieRequst(addr+"api/bill/call", createParms())

@test
def testDb():
    service = DbService()
    service.getUserHistoryBills()


testRegister()
testLogin()
# testGetRecomendBills()
testBill()

