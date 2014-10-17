#encoding=utf-8
__author__ = 'zhongqiling'

import tornado
from tornado.gen import coroutine
from functools import wraps
from datetime import datetime, time
from tornado.options import options
from tornado.gen import Return
from mylog import mylog, getLogText
from dbmodels import *

def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


def sync_loop_call(delta=60 * 1000):
    """
    Wait for func down then process add_timeout
    """
    def wrap_loop(func):
        @wraps(func)
        @coroutine
        def wrap_func(*args, **kwargs):
            options.logger.info("function %r start at %d" % (func.__name__, int(time.time())))
            try:
                yield func(*args, **kwargs)
            except Exception, e:
                options.logger.error("function %r error: %s" % (func.__name__, e))
            options.logger.info("function %r end at %d" % (func.__name__, int(time.time())))
            tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(milliseconds=delta), wrap_func)

        return wrap_func

    return wrap_loop

addr_whole = u"不限"

class AddrComp(object):
    INVALID = -1
    DIFFER = 0
    SAME_PROV = 1
    SAME_CITY = 2
    SAME_ADDR = 3


def addr_compare(addr1, addr2):
    if not isinstance(addr1, basestring) or not isinstance(addr2, basestring):
        return AddrComp.INVALID
    addr1List = addr1.split("-")
    addr2List = addr2.split("-")
    result = [addr1List[i] == addr2List[i] for i in range(len(addr1List)) if len(addr2List)>i]
    try:
        index = result.index(False)
        if index == 0:
            return AddrComp.DIFFER
        elif index == 1:
            return AddrComp.SAME_PROV if len(result)==3 else AddrComp.SAME_CITY
        else:
            return AddrComp.SAME_CITY
    except ValueError, e:
        return AddrComp.SAME_ADDR


def splitAddr(addr):
    try:
        return addr.split("-")
    except Exception, e:
        return []

def joinAddr(addrlist, spliter="-"):
    if isinstance(addrlist, list) and len(addrlist) > 0:
        return spliter.join(addrlist) if len(addrlist) > 1 else addrlist[0]
    return ""

def addrsAnalysis(addrs):
    result = []
    for addr in addrs:
        addrList = splitAddr(addr)
        i, length = 0, len(addrList)
        while len(addrList)>0:
            temp = "-".join(addrList) if len(addrList)>1 else addrList[0]
            if len(result) <= i:
                result.append({})
            if not temp in result[i]:
                result[i][temp] = 0
            result[i][temp] += 1
            addrList.pop()
            i += 1
    keys = ["region", "city", "prov"]
    return dict([(keys[i], calFrequence(result[i])) for i in range(len(result))])

def calFrequence(addrDict):
    sum = reduce(lambda a, b:a+b, addrDict.values())
    for k, v in addrDict.items():
        addrDict[k] = float(v)/float(sum)

    return addrDict

def getCity(addr, spliter="-"):
    addrList = splitAddr(addr)
    if len(addrList) > 1:
        addrList.pop()
        return joinAddr(addrList, spliter)
    return ""

def getProv(addr):
    addrList = splitAddr(addr)
    if len(addrList) == 3:
        return addrList[0]
    return ""

def getAddrShort(addr, spliter="-"):
    addrList = splitAddr(addr)
    if len(addrList) > 1:
        addrList.pop()
        while len(addrList) > 0:
            addr = addrList.pop()
            if not isAddrWhole(addr):
                return addr
    return ""

def isAddrWhole(addr):
    return addr == u"不限" or addr == "不限"


@coroutineDebug
@coroutine
def extractBillsFromIds(ids):
    bills = [(yield Bill.get(id)) for id in ids]
    returnBills = filter(lambda b:b, bills)
    raise Return(returnBills)


def docToParms(docCls):
    return dict([(key, unicode) for key in docCls._fields])