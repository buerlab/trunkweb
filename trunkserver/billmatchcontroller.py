#encoding=utf-8

__author__ = 'zhongqiling'

from commons import Singleton
from appmodels import BillType, BillState, oppsiteBillType
from utils import getCity
from mylog import mylog, getLogText
from dbmodels import Bill
from appconf import coroutineDebug
from tornado.gen import coroutine
from jpush.JPushService import JPushNotifyToId

def makeAddrKey(fromAddr, toAddr):
    try:
        return str(fromAddr)+"->"+str(toAddr)
    except Exception, e:
        return ""

#将一个新单匹配城市后加入map
def matchCity(result, bill):
    billType = bill.billType
    if not billType in (BillType.GOODS, BillType.TRUNK):
        return
    cityKey = makeAddrKey(getCity(bill.fromAddr), getCity(bill.toAddr))

    if cityKey:
        if not cityKey in result:
            result[cityKey] = {BillType.TRUNK: [], BillType.GOODS: []}
        result[cityKey][billType].append(str(bill.id))
    else:
        mylog.getlog().error("ADD BILL ERROR, ADDR IS INVALID")


class BillMatchController(Singleton):
    billMatchMap = {}

    @coroutineDebug
    @coroutine
    def initFromDB(self):
        self.billMatchMap = {}
        cursor = Bill.get_collection().find({"state":BillState.WAIT}, {"_id":1, "toAddr":1, "fromAddr":1, "billType":1})
        count = yield cursor.count()
        mylog.getlog().info(getLogText("BILL MATCH INIT FROM DB, GET BILL COUNT: ", str(count)))
        if count > 0:
            while (yield cursor.fetch_next):
                billDoc = cursor.next_object()
                bill = Bill.from_db(billDoc)
                matchCity(self.billMatchMap, bill)

    def sendBill(self, bill):
        matchCity(self.billMatchMap, bill)
        if self.isMatch(bill):
            #发送一个push给三星的手机
            JPushNotifyToId("0806fa24854", "找到匹配的单子了",  "driver")

    def removeBill(self, bill):
        cityKey = makeAddrKey(getCity(bill.fromAddr), getCity(bill.toAddr))
        billId = str(bill.id)
        if billId and cityKey in self.billMatchMap and billId in self.billMatchMap[cityKey][bill.billType]:
            self.billMatchMap[cityKey][bill.billType].remove(billId)

    def isMatch(self, bill):
        findType  = oppsiteBillType(bill.billType)
        addrKey = makeAddrKey(getCity(bill["fromAddr"]), getCity(bill["toAddr"]))
        return addrKey in self.billMatchMap and len(self.billMatchMap[addrKey][findType]) > 0

    #返回匹配的单子id
    def getMatchBills(self, bill):
        findType  = oppsiteBillType(bill.billType)
        addrKey = makeAddrKey(getCity(bill.fromAddr), getCity(bill.toAddr))
        if addrKey in self.billMatchMap:
            return self.billMatchMap[addrKey][findType]
        else:
            return []


    def getMatchMap(self):
        result = self.billMatchMap.copy()
        #如果结果里面司机或者货主list里面有一个是空得，应该filter掉
        delKeys = [k for k, v in result.items() for v2 in v.values() if not v2]
        for k in delKeys:
            if k in result:
                del result[k]
        return result


