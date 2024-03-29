#encoding=utf-8
__author__ = 'zhongqiling'

from tornado.options import define, options
from datetime import datetime
import time
from models.query import *

from basehandler import *
from dbservice import DbService
from dataprotocol import DataProtocol
from mylog import mylog, getLogText
from appmodels import *
from dbmodels import *
from jpush.JPushService import *
from motor import Op
from utils import *
import json
from billmatchcontroller import BillMatchController
# from billrecommend import getRecomendBills
from billanalysis import BillAnalysis


historyRetrunFragment = 5
historySearchLength = 1000


def isbillmatchuser(usertype, billtype):

    return usertype and billtype and \
           ((usertype == UserType.DRIVER and billtype == BillType.TRUNK) \
           or (usertype == UserType.OWNER and billtype == BillType.GOODS))


def usertypeofbill(billtype):
    if billtype == BillType.GOODS:
        return UserType.OWNER
    elif billtype == BillType.TRUNK:
        return UserType.DRIVER
    else:
        return None


class SendBillHandler(BaseHandler):

    requiredParams = {
        "userType":unicode,
        "billType": unicode,

        "fromAddr": unicode,
        "toAddr": unicode,

    }

    optionalParams = {
        "sender": unicode,
        "senderName":unicode,
        "phoneNum":unicode,

        "billTime": unicode,
        "validTimeSec":unicode,
        "source":unicode,
        "sendTime":unicode,

        "passAddr":unicode,
        "comment":unicode,
        "IDNumber": unicode,
        "price": unicode,
        "weight": unicode,
        "volume": unicode,
        "material": unicode,

        "trunkType": unicode,
        "trunkLength": unicode,
        "trunkLoad": unicode,
        "licensePlate": unicode,
    }

    #为什么这里 一加 @auth 就 跨域报错 而 addBillHandler没事？ 先不加了
    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        mylog.getlog().info(getLogText("--send bill, get argument: ", kwargs))
        if kwargs:
            bill = Bill.from_db(kwargs)
            if bill:
                now = time.time()
                bill.sendTime, bill.addTime = bill.sendTime or now, now
                bill.state = BillState.WAIT
                userId = self.getCurrUserId()
                print "userid"
                if userId:
                    user = (yield self.getUser()) if not bill.sender else (yield User.get(bill.sender, matchUserType(bill.billType)))
                    if user and user.currType == matchUserType(bill.billType):
                        # saveBill = yield user.sendBill(bill)
                        bill.sender = bill.sender or user.id
                        bill.senderName = bill.senderName or user.nickName
                        bill.phoneNum = bill.phoneNum or user.phoneNum
                        saveResult = yield bill.save()

                        if saveResult:
                            user.getAttr("Bills").append(bill.id)
                            yield user.save()

                            mylog.getlog().info(getLogText("--send bill success~~~"))
                            #告诉matchcontroller有新单发送，更新matchmap
                            BillMatchController().sendBill(bill)

                            self.finish(DataProtocol.getSuccessJson(bill.to_client()))
                        else:
                            self.finish(DataProtocol.getJson(DataProtocol.DB_ERROR))
                    else:
                        self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "创建订单失败"))
                else:
                    yield bill.save()
                    #告诉matchcontroller有新单发送，更新matchmap
                    BillMatchController().sendBill(bill)
                    self.finish(DataProtocol.getSuccessJson(bill.to_client()))
            else:
                self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "创建订单失败"))
        else:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
        return



class GetUserBillsHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")

    requiredParams = {
        "userType":unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        user = yield self.getUser()
        bills = yield user.getBills()
        returnBills = [b.to_client() for b in bills]
        print "---return ",len(returnBills)," bills"
        self.write(DataProtocol.getSuccessJson(returnBills))


# class GetUserRecordHandler(BaseHandler):
#
#
#
#     @auth
#     @coroutineDebug
#     @coroutine
#     def onCall(self, *args, **kwargs):



class DeleteBillHandler(BaseHandler):
    @auth
    @addAllowOriginHeader
    def post(self):
        billid = self.get_argument("billid", None)
        if billid:
            service = self.getDbService()
            if service:
                service.removeBill(billid)
                self.write(DataProtocol.getSuccessJson())
                self.finish()
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
            self.finish()

class RemoveBillHanlder(BaseHandler):

    requiredParams = {
        "billid":unicode
    }

    #讲单子变为cancelled，如果user有效，从user中得billcol转移到billrecord
    @auth
    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        print "remove bill", kwargs
        billid = kwargs["billid"]
        bill = yield Bill.get(billid)
        user = yield self.getUser()

        if bill:
            bill.state = BillState.CANCELLED
            yield bill.save()
            if user and user.currType and bill.id in user.getAttr("Bills"):
                user.getAttr("Bills").remove(bill.id)
                user.getAttr("BillsRecord").append(bill.id)
                yield user.save()

            BillMatchController().removeBill(bill)
            self.finish(DataProtocol.getSuccessJson())
        else:
            self.finish(DataProtocol.getJson(DataProtocol.BILL_NOT_OWN))



class UpdateBillHandler(BaseHandler):
    requiredParams = {
        "billId":unicode
    }

    optionalParams = {
        "comment":unicode,
        "fromAddr": unicode,
        "toAddr": unicode,
        "billTime": unicode,
        "validTimeSec":unicode,

        "IDNumber": unicode,
        "price": unicode,
        "weight": unicode,
        "material": unicode,

        "trunkType": unicode,
        "trunkLength": unicode,
        "trunkLoad": unicode,
        "licensePlate": unicode
    }


    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        billId = kwargs["billId"]
        bill = yield Bill.get(billId)
        if bill:
            bill.update(**kwargs)
            yield bill.save()
            self.finish(DataProtocol.getSuccessJson(bill.to_client()))
        else:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "订单不存在"))


class InviteBillHandler(BaseHandler):
    @auth
    def post(self):
        inviteFrom = self.get_argument("from", None)
        inviteTo = self.get_argument("to", None)
        service = self.getDbService()
        billFrom = service.getBillById(inviteFrom)
        billTo = service.getBillById(inviteTo)
        if billFrom and billTo and billFrom["billType"] != billTo["billType"] and billFrom["state"] == "wait" and \
                        billTo["state"] == "wait":
            service.inviteBill(billFrom, billTo)
            self.write(DataProtocol.getSuccessJson())
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class ConnBillHandler(BaseHandler):
    @auth
    def get(self):
        mylog.getlog().info(getLogText("find bills"))
        service = self.getDbService()
        userid = self.getCurrUserId()
        if service:
            user = service.getUserBaseData(userid)
            query = {}
            if user.has_key("userType"):
                query["billType"] = "goods" if user["userType"] == "driver" else "trunk"
                mylog.getlog().info(getLogText("find:", query["billType"]))
            bills = service.findBills(query)
            self.write(DataProtocol.getSuccessJson(bills))

    @auth
    def post(self):
        billid = self.get_argument("billid", None)
        receiver = self.get_argument("receiver", None)
        if receiver and billid:
            service = DbService()
            service.connect()
            service.connectBills(billid, receiver)
            self.write(DataProtocol.getSuccessJson())
            self.finish()
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
            self.finish()

#------------------------------
#RECOMEND
#------------------------------

#获取推荐格式单子给客户端
@coroutineDebug
@coroutine
def getRecomendBills(bills):
    returnData, sendedUsers = [], []

    for bill in bills:
            bill.visitedTimes += 1
            bill.visitedChange = True
            yield bill.save()
            senderId, sender = bill.sender, None

            if senderId:
                sender = yield User.get(senderId, matchUserType(bill.billType))
                if sender:
                    #发送给单子拥有者，更新单子访问次数
                    if not senderId in sendedUsers:
                        if sender.getAttr("JPushId"):
                            print "push to", sender.getJPushId(bill.billType), "sendertype:", sender.currType
                            JPushMsgToId(sender.getAttr("JPushId"), createprotocol(str(sender.id), JPushProtocal.BILL_VISITED), sender.currType)
                        sendedUsers.append(senderId)

            #如果是管理员的账号或者没有发送者的单子，利用已有信息fake一个
            if (sender and sender.level == UserLevel.MANAGER) or ((not sender) and bill.senderName):
                sender = User()
                sender.currType = matchUserType(bill.billType)
                sender.nickName = bill.senderName
                #fake的用户不能追踪位置
                sender.setAttr("Settings", {"locate":False})

            if sender:
                returnData.append(createRecommendBill(sender.to_user_base_data(), bill.to_client(), bill.billType))

    raise Return(returnData)


def mergeBills(bills):
        billIds, billsToRemove = [], []
        for bill in bills:
            if bill.id in billIds:
                billsToRemove.append(bill)
            else:
                billIds.append(bill.id)
        for bill in billsToRemove:
            bills.remove(bill)

#基础查询
def getQueryFromBase(userid, findtype, excludeBills, queryDict):
    query = {"billType": findtype, "state":BillState.WAIT, "sender":{"$ne":userid}}
    #排除excludeBills里面的单子
    if len(excludeBills) > 0:
        query.update({"id":{"$nin":[bill.id for bill in excludeBills]}})
    query.update(queryDict)
    return query


#获取货单的重量与货车载重匹配的条件
def getLoadMatchCondition(user, bill=None):
    if user.currType == UserType.DRIVER and user.getCurrTruck():
        return {"weight":{"$lte":float(user.getCurrTruck()["load"])}}
    elif user.currType == UserType.OWNER and bill:
        return {"trunkLoad":{"$gte":bill.weight}}
    return {}

def getAddrMatchReg(addr):
    return re.compile(r"^"+addr)

#获取可推荐的单子
@coroutineDebug
@coroutine
def getBillsToRecomend(user, config):
    returnLimit = config.recommendBillsReturnOnce
    bills, i = [], 0
    userBills = yield user.getBills()
    print "usertype:" + user.currType
    recordBills = yield extractBillsFromIds(user.getAttr("BillsRecord"))
    while len(bills) < returnLimit:
        try:
            if i == 0:
                bills.extend((yield getAddrMatchBill(userBills)))
            elif i == 1:
                bills.extend((yield getAddrNearBill(user, bills, userBills, returnLimit)))
            elif i == 2:
                bills.extend((yield getRecordMatchBill(user, bills, recordBills, returnLimit)))
            elif i == 3:
                bills.extend((yield getLocationMatchBill(user, bills, getCity(user.homeLocation), returnLimit)))
            elif i == 4:
                bills.extend((yield getLocationMatchBill(user, bills, getProv(user.homeLocation), returnLimit)))
            else:
                break

        except Exception, e:
            print e.message
            break
        mergeBills(bills)
        i += 1

    sortedByWeight = sorted([(bill, calWeight(config, user, userBills, recordBills, bill)) for bill in bills],\
                            key=lambda item:item[1], reverse=True)
    sortedSlice = sortedByWeight[0:returnLimit]
    returnBills = [b[0] for b in sortedSlice]
    raise Return(returnBills)


@coroutineDebug
@coroutine
def getAddrMatchBill(bills):
    '''
    根据用户当前有效的单据查找from，to都匹配的对应单据
    :param user:
    :param excludeBills: 之前已经找到的单据，后面查找时候就要排除掉
    :param bills:
    :return:
    '''
    if bills:
        returnBills = []
        #
        # try:
        #     conditions = []
        #     for bill in bills:
        #         cond = {"fromAddr":bill.fromAddr, "toAddr":bill.toAddr}
        #         #载重与货物重量匹配的条件
        #         cond.update(self.getLoadMatchCondition(user, bill))
        #         conditions.append(cond)
        #     limitLength = self.config.recommendBillsReturnOnce
        #     returnBills = yield Bill.objects(self.getQueryFromBase(user, excludeBills, {"$or":conditions}))\
        #                         .limit(limitLength).to_list(limitLength)
        # except Exception, e:
        #     print "QUERY ERROR :", e.message


        # 遍历用户正在等待中的单子
        for bill in bills:
            matchBills = BillMatchController().getMatchBills(bill)
            for bId in matchBills:
                if bId:
                    matchBill = yield Bill.get(bId)
                    #如果是车单，用户当前车辆的载重小于货重，或者 货单， 货重大于车单的载重就排除
                    if matchBill:
                        returnBills.append(matchBill)

        mylog.getlog().info(getLogText("----get addr match", len(returnBills)))
        raise Return(returnBills)
    else:
        raise Return([])


@coroutineDebug
@coroutine
def getAddrNearBill(user, excludeBills, bills, returnLimit):
    '''
    根据用户当前有效的单据查找from，to都在同一个城市的对应单据
    :param user:
    :param excludeBills: 之前已经找到的单据，后面查找时候就要排除掉
    :param bills:
    :return:
    '''
    if bills:
        conditions = []
        for bill in bills:
            #获取单子上面的城市名
            fromCity, toCity = getCity(bill.fromAddr), getCity(bill.toAddr)
            cond = {"fromAddr": re.compile(r"^"+fromCity), "toAddr":re.compile(r"^"+toCity)}
            cond.update(getLoadMatchCondition(user, bill))
            conditions.append(cond)
        findType = matchBillType(oppsiteUserType(user.currType))
        query = getQueryFromBase(str(user.id), findType, excludeBills, {"$or":conditions})
        returnBills = yield Bill.objects(query).limit(returnLimit)\
                                        .to_list(returnLimit)

        mylog.getlog().info(getLogText("----get addr near", len(returnBills)))
        raise Return(returnBills)
    else:
        raise Return([])

@coroutineDebug
@coroutine
def getRecordMatchBill(user, excludeBills, recordBills, returnLimit):
    '''
    根据用户以往的发送记录，计算出频率排在前面的几个城市，推送
    :param user:
    :param excludeBills:
    :param recordBills:
    :return:
    '''
    if recordBills:
        recordFrom = [bill.fromAddr for bill in recordBills]
        recordTo = [bill.toAddr for bill in recordBills]
        fromFreq = addrsAnalysis(recordFrom)
        toFreq = addrsAnalysis(recordTo)
        #取出频率至多前三位的城市
        fromCities, toCities = fromFreq["city"].keys()[0:3], toFreq["city"].keys()[0:3]

        query = {"fromAddr":{"$in":fromCities}, "toAddr":{"$in":toCities}}
        query.update(getLoadMatchCondition(user))

        findType = matchBillType(oppsiteUserType(user.currType))
        bills = yield Bill.objects(getQueryFromBase(str(user.id), findType, excludeBills, query))\
                            .limit(returnLimit).to_list(returnLimit)

        mylog.getlog().info(getLogText("----get addr record", len(bills)))
        raise Return(bills)
    else:
        raise Return([])


@coroutineDebug
@coroutine
def getLocationMatchBill(user, excludeBills, location, returnLimit):
    '''
    根据用户当前所在的城市推送相同出发地的回程单
    :param user:
    :param excludeBills:
    :param location:
    :return:
    '''
    try:
        query = {"fromAddr":re.compile(r"^"+location)}
        query.update(getLoadMatchCondition(user))

        findType = matchBillType(oppsiteUserType(user.currType))
        bills = yield Bill.objects(getQueryFromBase(str(user.id), findType, excludeBills, query))\
                                    .limit(returnLimit).to_list(returnLimit)
    except Exception, e:
        print "lOCAL EROOR:", e.message

    mylog.getlog().info(getLogText("----get location%s match"%location, len(bills)))
    raise Return(bills)

def calWeight(config, user, userBills, recordBills, bill):
    weight = 0
    weight += evalBillMatchWeight(config, userBills, bill)
    weight += evalLocationWeight(config, user, bill)
    weight += evalBillRecordWeight(config, recordBills, bill)
    weight += evalTimeWeight(config, bill)
    weight += evalStarWeight(config, user, bill)
    weight += evalTrunkVerifiedWeight(config, user)
    weight += evalTrunkPicVerifiedWeight(config, user)
    weight += evalDriverLiscenseVerifiedWeight(config, user)
    weight += evalIDVerifiedWeight(config, user)
    return weight


def evalBillMatchWeight(config, waitBills, bill):
    '''
    正在发送单据里有出发目的均匹配的
    :param historyBills:
    :param bill:
    :return:
    '''
    for userBill in waitBills:
        fromComp, toComp = addr_compare(userBill.fromAddr, bill.fromAddr), addr_compare(userBill.toAddr, bill.toAddr)
        if fromComp > AddrComp.SAME_PROV and toComp > AddrComp.SAME_PROV:
            return config.billMatchWeight+(fromComp*config.fromAddrWeight+toComp)*config.billMatchRatioWeight
    return 0

def evalLocationWeight(config, user, bill):
    fromComp = addr_compare(user.homeLocation, bill.fromAddr)
    if fromComp > AddrComp.SAME_PROV:
        return config.homeLocationWeight+fromComp*config.homeLocationRatioWeight
    return 0

def evalBillRecordWeight(config, recordBills, bill):
    if len(recordBills) > 0:
        recordFrom = [bill.fromAddr for bill in recordBills]
        recordTo = [bill.toAddr for bill in recordBills]
        fromFreq = addrsAnalysis(recordFrom)
        toFreq = addrsAnalysis(recordTo)

        fromPoint = calSingleAddrFreqPoint(fromFreq, bill.fromAddr)
        toPoint = calSingleAddrFreqPoint(toFreq, bill.toAddr)
        total = fromPoint*config.fromAddrWeight+toPoint
        return config.recordBillWeight+total*config.recordBillRatioWeight if total>0 else 0
    return 0

def calSingleAddrFreqPoint(addrsFreq, addr):
    if addr in addrsFreq["region"]:
        return 2 + addrsFreq["region"][addr]
    elif getCity(addr) in addrsFreq["city"]:
        return 1 + addrsFreq["city"][getCity(addr)]
    elif getProv(addr) in addrsFreq["prov"]:
        return addrsFreq["prov"][getProv(addr)]
    return 0

def evalTimeWeight(config, bill):
    '''
    分段函数， 有效期内得到全分，有效期之前减函数
    :param user:
    :param bill:
    :return:
    '''
    if bill.billTime:
        delta = datetime.fromtimestamp(bill.billTime) - datetime.now()
        deltaSec = delta.total_seconds()
        if deltaSec > 0:
            return config.timeBaseWeight - int(deltaSec/3600)*config.timePerHourWeight
        elif abs(deltaSec) < bill.validTimeSec:
            return config.timeBaseWeight
    elif bill.sendTime:
        delta = datetime.now() - datetime.fromtimestamp(bill.sendTime)
        deltaSec = delta.total_seconds()
        if deltaSec > 0:
            return config.timeBaseWeight - int(deltaSec/3600)*config.timePerHourWeight

    return 0

def evalStarWeight(config, user, bill):
    stars = user.getStars(bill.getContraryType()) or 0
    return stars*config.starWeight

def evalTrunkVerifiedWeight(config, user):
    for trunk in user.trunks:
        if trunk["isUsed"] and trunk["trunkLicenseVerified"]:
            return config.trunkLicenseVerifiedWeight
    return 0

def evalTrunkPicVerifiedWeight(config, user):
    for trunk in user.trunks:
        if trunk["isUsed"] and "trunkPicFilePaths" in trunk and trunk["trunkPicFilePaths"]:
            return config.trunkPicVerifiedWeight
    return 0

def evalDriverLiscenseVerifiedWeight(config, user):
    return config.driverLiscenseVerifiedWeight if user.driverLicenseVerified else 0

def evalIDVerifiedWeight(config, user):
    return config.IDVerifiedWeight if user.IDNumVerified else 0




class GetRecommendBillsHandler(BaseHandler):

    config = None
    userBills = None
    userHistoryBills = None
    recordBills = []

    #每次返回的单据数量
    returnBillsNum = 3

    #兼容前面的一些版本，临时做得format，有的话返回最新的格式的数据
    optionalParams = {
        "format": unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        mylog.getlog().info(getLogText("get recomend bills"))
        usertype = self.getUserType()
        user = yield self.getUser()
        if not user:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
            raise Return(None)

        self.findtype = matchBillType(oppsiteUserType(usertype))

        self.config = yield Config.shared()
        self.userBills = yield user.getBills()
        for id in user.getAttr("BillsRecord")[0:10]:
            bill = yield Bill.get(id)
            self.recordBills.append(bill)

        bills = yield getBillsToRecomend(user, self.config)

        if "format" in kwargs and kwargs["format"] == "ids":
            #slice
            sortBills, returnBillIds = bills[0:self.returnBillsNum], []
            returnBills = yield getRecomendBills(sortBills)
            if len(bills)>self.returnBillsNum:
                returnBillIds = [str(b.id) for b in bills[self.returnBillsNum:len(bills)]]

            returnData = {"bills":returnBills, "ids":returnBillIds}
        else:
            returnData = yield getRecomendBills(bills)


            # if we want to find trucks then return some local drivers.
            if self.findtype == BillType.TRUNK:
                gap = self.config.recommendBillsReturnOnce - len(returnData)
                if gap > 0:
                    localBills = yield self.getLocalTruckBill(getCity(user.homeLocation), gap)
                    returnData.extend(localBills)

        mylog.getlog().info(getLogText("recommend bills return:", len(bills)))
        self.finish(DataProtocol.getSuccessJson(returnData))


    @coroutineDebug
    @coroutine
    def perform(self, query):
        limitLength = self.config.recommendBillsReturnOnce
        bills = yield Bill.objects(query).sort({"sendTime":-1}).limit(limitLength).to_list(limitLength)
        raise Return(bills)



    @coroutineDebug
    @coroutine
    def getLocalTruckBill(self, location, num):
        drivers = yield User.objects({"id":{"$ne":ObjectId(self.getCurrUserId())}, "trunks":{"$not":{"$size":0}}, \
                                      "homeLocation":re.compile(r"^"+location)}).limit(num).to_list(num)

        mylog.getlog().info(getLogText("-----recommend local:", len(drivers)))
        returnBills = []
        if drivers:
            for driver in drivers:
                currTruck = driver.getCurrTruck()
                if currTruck:
                    bill = Bill()
                    bill.trunkType = currTruck["type"]
                    bill.trunkLength = currTruck["length"]
                    bill.trunkLoad = currTruck["load"]
                    driver.currType = UserType.DRIVER
                    driverData = driver.to_user_base_data()
                    # print "driver:", driver.ids
                    driverLocs = yield Location.objects({"userId":str(driver.id)}).sort([("timestamp", -1)]).limit(1).to_list(1)
                    # driverLoc = yield Location.get_collection().find_one({"userId":str(driver.id)})
                    if driverLocs:
                        driverData.update({"location":driverLocs[0].to_client()})
                    returnBills.append(createRecommendBill(driverData, bill.to_client(), RecomendBillType.LOCAL))

        raise Return(returnBills)




class GetRecommendBillsDataHandler(BaseHandler):

    requiredParams = {
        "billIds":unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        returnData, sendedUsers = [], []
        try:
            billIds = json.loads(kwargs["billIds"])
        except Exception, e:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
            raise Return(None)
        bills = [(yield Bill.get(id)) for id in billIds]
        returnData = yield getRecomendBills(bills)

        self.finish(DataProtocol.getSuccessJson(returnData))


# def createRecomendBills(billIds):
#     tempUsers = []
#     for id in billIds:
#         bill = yield Bill.get(id)
#         bill.visitedTimes += 1
#         bill.visitedChange = True
#         yield bill.save()
#         senderId, sender = bill.sender, None
#         if senderId:
#             sender = yield User.get(senderId, matchUserType(bill.billType))
#             if sender:
#                 #发送给单子拥有者，更新单子访问次数
#                 if not senderId in tempUsers:
#                     if sender.getAttr("JPushId"):
#                         print "push to", sender.getJPushId(bill.billType), "sendertype:", sender.currType
#                         JPushMsgToId(sender.getAttr("JPushId"), createprotocol(str(sender.id), JPushProtocal.BILL_VISITED), sender.currType)
#                     tempUsers.append(senderId)
#         #如果是管理员的账号或者没有发送者的单子，利用已有信息fake一个
#         if (sender and sender.level == UserLevel.MANAGER) or ((not sender) and bill.senderName):
#             sender = User()
#             sender.currType = matchUserType(bill.billType)
#             sender.nickName = bill.senderName
#             #fake的用户不能追踪位置
#             sender.setAttr("Settings", {"locate":False})
#
#         if sender:
#             returnData.append(createRecommendBill(sender.to_user_base_data(), bill.to_client(), bill.billType))


class GetRecommendTrunkHandler(BaseHandler):

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
         pass


class BillCallHandler(BaseHandler):

    requiredParams = {
        "billId": unicode
    }

    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        print "get bill confirm:", kwargs["billId"]
        bill = yield Bill.get(kwargs["billId"])
        if not bill:
            self.finish(DataProtocol.getJson(DataProtocol.BILL_REMOVED))
        elif bill.state == BillState.WAIT:
            self.finish(DataProtocol.getSuccessJson())
        else:
            self.finish(DataProtocol.getJson(DataProtocol.BILL_NOT_WAIT))


    # @auth
    # def post(self):
    #     targetId = self.get_argument("targetId", None)
    #     billtype = self.get_argument("billType", None)
    #     usertype = usertypeofbill(billtype)
    #     userid = self.getCurrUserId()
    #     service = self.getDbService()
    #     print "get bill call to:", targetId, "usertype", usertype
    #     if not service:
    #         self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))
    #         return
    #     if not (targetId and usertype):
    #         self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "lack of target id or bill type"))
    #         return
    #     user = service.getUserBaseData(userid)
    #     target = service.getUserBaseData(targetId)
    #     if "jpushId" in target and user["nickName"]:
    #         print "about to msg", target["jpushId"], "from:", user["nickName"]
    #         JPushMsgToId(target["jpushId"], createprotocol(str(target.id), JPushProtocal.PHONE_CALL, user["nickName"]))
    #         self.write(DataProtocol.getSuccessJson())
    #         return


class GetVisitedBillHandler(BaseHandler):

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        # userid = self.getCurrentUser()
        # userType = self.getUserType()
        # service = self.getDbService()
        # if service:
        #     print "get visit bill"
        #     bills = service.getUserVisitedBills(userid, userType)
        #     data = dict([(bill["billId"], bill["visitedTimes"]) for bill in bills])
        #     self.write(DataProtocol.getSuccessJson(data))
        #     return
        # else:
        #     self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))

        user = yield self.getUser()
        bills = yield user.getBills()
        billsToReturn = []
        for bill in bills:
            if bill.visitedChange:
                billsToReturn.append(bill)
                bill.visitedChange = False
                yield bill.save()
        returnDict = dict([(str(b.id), b.visitedTimes) for b in billsToReturn])
        self.finish(DataProtocol.getSuccessJson(returnDict))


class GetHistoryBillHandler(BaseHandler):

    optionalParams = {
        "isPrev":unicode,
        "fromId":unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        fromId = self.get_argument("fromId", None)
        isPrev = self.get_argument("isPrev", None)
        try:
            fromObjId = ObjectId(fromId) if fromId else None
            isPrevBool = bool(isPrev) and bool(str(isPrev).lower()=="true")
            print "get history:", fromId, "is prev:", isPrev
            user = yield self.getUser()

            historyBills = yield user.getHistoryBill(self.getUserType(), fromObjId, isPrevBool)
            toReturn = []
            for hBill in historyBills:
                #如果历史单据是正常的用户发送的，返回用户数据，否则返回一个临时用户的数据
                sender = (yield User.get(hBill.senderId, hBill.senderType)) if hBill.senderId else None
                senderData = sender.to_user_base_data() if sender else None
                hBill = createReturnHistoryBill(hBill, senderData)
                toReturn.append(hBill)

            print "return %d history bills"%len(toReturn)
            self.write(DataProtocol.getSuccessJson(toReturn))
        except ValueError:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))

#如果不传senderdata，就会用historybill里面的默认数据做一个临时的user返回，客户端将无法查看该user的详情
def createReturnHistoryBill(historybill, senderData=None):
    if not senderData:
        sender = User()
        sender.currType = historybill.senderType
        sender.nickName = historybill.nickName
        #fake的用户不能追踪位置
        sender.setAttr("Settings", {"locate":False})
        senderData = sender.to_user_base_data()
    return {"bill":historybill.to_client(), "senderData":senderData}

class UpdateHistoryBillHandler(BaseHandler):

    requiredParams = {
        "fromId": unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        user = yield self.getUser()
        fromId = kwargs["fromId"]

        try:
            historyBills = user.getHistoryBillList()
            fromIndex = historyBills.index(ObjectId(fromId))



        except Exception:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class GetRecordBillHandler(BaseHandler):

    returnOnce = 5
    returnLimit = 50

    optionalParams = {
        "fromId": unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        mylog.getlog().info(getLogText("get record bills"))
        user = yield self.getUser()
        fromId = self.get_argument("fromId", None)
        fromObjId = ObjectId(fromId) if fromId else None
        record = user.getAttr("BillsRecord")
        record.reverse()
        fromIndex = 0
        try:
            if fromObjId:
                fromIndex = record.index(fromObjId)+1
        except Exception, e:
            pass
        mylog.getlog().info(getLogText("from index: ", fromIndex))
        slice = record[fromIndex:fromIndex+self.returnOnce] if fromIndex<len(record) else []
        bills = [(yield Bill.get(id)) for id in slice]
        billsToReturn = [bill.to_client() for bill in bills if bill]
        self.finish(DataProtocol.getSuccessJson(billsToReturn))


class PickBillHandler(BaseHandler):

    optionalParams = {
        "billId":unicode,
        "toUserId":unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        billId = self.get_argument("billId", None)
        toUserId = self.get_argument("toUserId", None)

        if not billId and not toUserId:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
            return

        user = yield self.getUser()
        req = PendingRequest()
        req.reqType = RequestType.Bill
        req.reqUser = user.id
        req.reqUserType = self.getUserType()
        if billId:
            #通过单发送请求
            print "request bill id:", billId
            bill = yield Bill.objects({"id":billId, "state":BillState.WAIT}).one()
            if bill:
                sender = None
                if bill.sender:
                    sender = yield User.get(bill.sender)
                    if not sender:
                        self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
                        return

                    elif sender.level != UserLevel.MANAGER:
                        req.reqBill = bill.id
                        req.respUser = sender.id
                        req.respUserType = bill.getSenderType()

                        print "pickBill req save!"
                        yield req.save()

                #####？bill没有sender 或者是管理员发送的单子的话就利用bill上面的数据来生成历史单据
                if not sender or (sender and sender.level == UserLevel.MANAGER):
                    sender = User()
                    sender.nickName = bill.senderName
                    sender.currType = matchUserType(bill.billType)
                    historyBill = createHistoryBill(sender, bill)
                    hbid = yield historyBill.save()
                    user.getAttr("HistoryBills").append(hbid)
                    yield user.save()
                    yield bill.remove()
                    BillMatchController().removeBill(bill)
                    #返回不是有效的对象，告诉客户端直接存历史，不需要发请求给对方
                    self.finish(DataProtocol.getJson(DataProtocol.USER_INVALID, "bill from manager", createReturnHistoryBill(historyBill)))
                    return
            else:
                # 发送请求给本地司机
                print "bill removed"
                self.finish(DataProtocol.getJson(DataProtocol.BILL_REMOVED))
                return

        elif toUserId:
            respUser = yield User.get(toUserId)
            req.respUser = respUser.id
            yield req.save()

        self.finish(DataProtocol.getSuccessJson())


class ConfirmBillReqHandler(BaseHandler):

    requiredParams = {
        "reqId": unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        print "************get confirm request id:", kwargs["reqId"]
        req = yield PendingRequest.get(kwargs["reqId"])
        req.state = PendingReqState.FINISHED
        yield req.save()
        reqBill = yield Bill.objects({"id":req.reqBill, "state":BillState.WAIT}).one()
        if reqBill:
            requestUser = yield User.get(req.reqUser, req.reqUserType)
            responseUser = yield User.get(req.respUser, req.respUserType)

            if requestUser and responseUser:
                config = yield Config.shared()
                locateValidSec = config.locateValidSec
                #根据请求的信息生成双方的历史单据
                senderHistoryBill = createHistoryBill(responseUser, reqBill, locateValidSec)
                shbId = yield senderHistoryBill.save()
                receiverHistoryBill = createHistoryBill(requestUser, reqBill, locateValidSec)
                rhbId = yield receiverHistoryBill.save()

                #add each of the users a historybill.
                if shbId and rhbId:
                    #双方添加历史单据
                    requestUser.getAttr("HistoryBills").append(shbId)
                    yield requestUser.save()

                    responseUser.getAttr("HistoryBills").append(rhbId)
                    yield responseUser.save()
                    yield responseUser.billDone(reqBill)
                    BillMatchController().removeBill(reqBill)
                    #反馈成功的信息给之前发起请求的一方
                    if requestUser.getAttr("JPushId"):
                        msg = createBillConfirmMsg(str(requestUser.id), responseUser.nickName, str(reqBill.id))
                        print "---push confirm...", requestUser.getAttr("JPushId"), "msg: ", msg
                        JPushToId(requestUser.getAttr("JPushId"), None, msg, req.reqUserType)

                    self.finish(DataProtocol.getSuccessJson(reqBill.to_client()))
                else:
                    self.finish(DataProtocol.getJson(DataProtocol.DB_ERROR))
            else:
                self.finish(DataProtocol.getJson(DataProtocol.DB_ERROR, "can'find user"))
        else:
            self.finish(DataProtocol.getJson(DataProtocol.BILL_REMOVED))

        yield req.remove()


def createHistoryBill(sender, bill=None, locateValidSec=0):
    hBill = HistoryBill()
    hBill.nickName = sender.nickName
    hBill.senderType = sender.currType
    hBill.sendTime = time.time()
    hBill.state = BillState.WAIT
    hBill.locateValidSec = locateValidSec
    #
    if sender.id:
        hBill.senderId = sender.id

    if bill:
        hBill.fromAddr = bill.fromAddr
        hBill.toAddr = bill.toAddr
        if bill.billType == BillType.TRUNK:
            hBill.billType = HistoryBillType.TRUNK
        elif bill.billType == BillType.GOODS:
            hBill.billType = HistoryBillType.GOODS
            hBill.price = bill.price
            hBill.weight = bill.weight
            hBill.material = bill.material
    else:
        hBill.billType = HistoryBillType.USER

    return hBill


class FinishHistoryBillHandler(BaseHandler):

    requiredParams = {
        "billId":unicode,
        "toUserId":unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        billId = self.get_argument("billId", None)
        toUserId = self.get_argument("toUserId", None)

        user = yield self.getUser()

        #通过单发送请求
        print "request bill id:", billId
        hBill = yield HistoryBill.objects({"id":billId, "state":BillState.WAIT}).one()
        if hBill:
            if hBill.senderId:
                sender = yield User.get(hBill.senderId)
                if not sender:
                    self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
                    return

                elif sender.level != UserLevel.MANAGER:
                    req = PendingRequest()
                    req.reqType = RequestType.HistoryBill
                    req.reqUser = user.id
                    req.reqUserType = self.getUserType()
                    req.reqBill = hBill.id
                    req.respUser = sender.id
                    req.respUserType = hBill.senderType

                    print "pickBill req save!"
                    yield req.save()
                    self.finish(DataProtocol.getSuccessJson())
        self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class ConfirmHistoryBillHandler(BaseHandler):

    requiredParams = {
        "reqId":unicode
    }

    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        req = yield PendingRequest.get(kwargs["reqId"])
        req.state = PendingReqState.FINISHED
        yield req.save()
        sender = yield User.get(req.reqUser, req.reqUserType)
        receiver = yield User.get(req.respUser, req.respUserType)
        if sender and sender.getAttr("JPushId"):
            bill = yield HistoryBill.get(req.reqBill)
            if bill:
                bill.state = BillState.DONE
                yield bill.save()
            msg = createHistoryBillConfirmMsg(str(sender.id), receiver.nickName, str(req.reqBill))
            print "---push history confirm...", sender.getAttr("JPushId"), "msg: ", msg
            JPushToId(sender.getAttr("JPushId"), None, msg, sender.currType)
            self.finish(DataProtocol.getSuccessJson())
        self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class getMatchBillMapHandler(BaseHandler):

    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        result = BillMatchController().getMatchMap()
        self.finish(DataProtocol.getSuccessJson(result,"json"))


class getMatchBillHandler(BaseHandler):

    requiredParams = {
        "billId": unicode,
    }

    optionalParams = {
        "full": unicode
    }

    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        bill = yield Bill.get(kwargs["billId"])
        #full字段表示是传回完整的dict（包括matcher和id），如果不传full， 则传回一个bill id的list
        if "full" in kwargs and kwargs["full"]:
            result = BillMatchController().getMatchDict(bill)
        else:
            result = BillMatchController().getMatchBills(bill)
        self.finish(DataProtocol.getSuccessJson(result))


class GetBillHandler(BaseHandler):

    requiredParams = {
        "billId": unicode
    }

    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        print "GetBillHandler"
        billId = kwargs["billId"]
        bill = yield Bill.get(billId)
        if bill:
            self.finish(DataProtocol.getSuccessJson(bill.to_client()))
        self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class GetBillsHandler(BaseHandler):

    requiredParams = {
        "billIds": unicode
    }

    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        print "get bills", kwargs["billIds"]
        try:
            billIds = json.loads(kwargs["billIds"])
            bills = []
            for id in billIds:
                bill = yield Bill.get(id)
                if bill:
                    bills.append(bill.to_client())
            self.finish(DataProtocol.getSuccessJson(bills))

        except Exception, e:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
            raise Return(None)


#-----------------------------
#分析billCol
#-----------------------------

_billanalysis = BillAnalysis()

@coroutineDebug
@coroutine
def initBillAnalysis():

    cursor = yield Bill.get_collection().find()
    while (yield cursor.fetch_next):
        billDoc = cursor.next_object()
        bill = Bill.from_db(billDoc)
        _billanalysis.addBill(bill)


class BillAnayliseHandler(BaseHandler):


    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        self.finish(DataProtocol.getSuccessJson(_billanalysis.getGeneral()))

class BillAnalysePhoneNumHandler(BaseHandler):

    requiredParams = {
        "phoneNum" : unicode
    }

    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        phoneNum = kwargs["phoneNum"]
        self.finish(DataProtocol.getSuccessJson(_billanalysis.analyseOne(phoneNum)))
