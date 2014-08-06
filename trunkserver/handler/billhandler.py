#encoding=utf-8
__author__ = 'zhongqiling'

from tornado.options import define, options
from basehandler import *
from dbservice import DbService
from dataprotocol import DataProtocol
from mylog import mylog, getLogText
from appmodels import *
from dbmodels import *
from jpush.JPushService import *
from motor import Op
from utils import *
import time



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
        "billTime": unicode,
    }

    optionalParams = {
        "IDNumber": unicode,
        "price": unicode,
        "weight": unicode,
        "material": unicode,

        "trunkType": unicode,
        "trunkLength": unicode,
        "trunkLoad": unicode,
        "licensePlate": unicode,
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        print "oncall send bill:", kwargs
        if kwargs:
            bill = Bill.from_db(kwargs)
            if bill:
                print "geting user:", self.getCurrentUser()
                user = yield User.get(self.getCurrentUser())
                if user:

                    saveBill = yield user.sendBill(bill)
                    print "send bill ok"
                    self.finish(DataProtocol.getSuccessJson(saveBill.to_client()))
                else:
                    self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "CREATE BILL ERROR"))
            else:
                self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "CREATE BILL ERROR"))
        else:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "BILL ARGUMENTS ERROR"))
        return

class GetUserBillsHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")

    requiredParams = {
        "userType":unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        print "*****get user bills"
        user = yield User.get(self.getCurrentUser())
        bills = yield user.getBills(self.getBillType())
        returnBills = [b.to_client() for b in bills]
        print "***return ",len(returnBills)," bills"
        self.write(DataProtocol.getSuccessJson(returnBills))


class BillHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")

    @auth
    def get(self):
        userid = self.getCurrentUser()
        usertype = self.get_argument("userType", None)
        num = self.get_argument("num", None)
        count = self.get_argument("count", None)
        mylog.getlog().info(getLogText("get bills:username", userid, " num", num, " count", count))
        service = DbService().connect()
        if userid and usertype and num and count and service:
            billtype = BillType.TRUNK if usertype == UserType.DRIVER else BillType.GOODS
            bills = service.getUserBills(userid, billtype, int(num), int(count))
            billsData = [service.getBillById(bill) for bill in bills] if bills else []
            billsData = filter(lambda b: b, billsData)
            self.write(DataProtocol.getSuccessJson(billsData))
            return
        self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
        self.finish()

    @auth
    def post(self):
        parms = {}
        usertype = self.get_argument("userType", None)
        billtype = self.get_argument("billType", None)
        #check if usertype match billtype
        if not isbillmatchuser(usertype, billtype):
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "usertype and billtype don't match"))
            return

        billdict = None
        if billtype == BillType.GOODS:
            billdict = goodsBillDict
        elif billtype == BillType.TRUNK:
            billdict = trunkBillDict

        if billdict:
            for k in billdict.iterkeys():
                parms[k] = self.get_argument(k, None)
            #init bill state.
            parms["state"] = BillState.WAIT

            userid = self.getCurrentUser()
            service = DbService().connect()
            if userid and service:
                mylog.getlog().info(getLogText("add to ", userid, "bill:", parms))
                service.addBill(userid, **parms)
                self.write(DataProtocol.getSuccessJson(parms))
                self.finish()
            else:
                self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR), "billtype is invalid")

    @auth
    @addAllowOriginHeader
    def delete(self, billid):
        if billid:
            service = self.getDbService()
            if service:
                service.removeBill(billid)
                self.write(DataProtocol.getSuccessJson())
                self.finish()
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "some of parms are invalid!!"))
            self.finish()


class DeleteBillHandler(BaseHandler):
    def post(self):
        billid = self.get_argument("billid", None)
        if billid:
            service = self.getDbService()
            if service:
                service.removeBill(billid)
                self.write(DataProtocol.getSuccessJson())
                self.finish()
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "some of parms are invalid!!"))
            self.finish()

class RemoveBillHanlder(BaseHandler):
    requiredParams = {
        "billid":unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        print "remove bill", kwargs
        billid = kwargs["billid"]
        bill = yield Bill.get(billid)
        print "get bill"
        user = yield User.get(self.getCurrentUser())
        print "get user"
        result = yield user.removeBill(bill)
        print "remove bill done"
        if result:
            self.finish(DataProtocol.getSuccessJson())
        else:
            self.finish(DataProtocol.getJson(DataProtocol.DB_ERROR))


class UpdateBillHandler(BaseHandler):
    @auth
    def post(self):
        billId = self.get_argument("billId", None)
        service = self.getDbService();
        if billId:
            billData = service.getBillById(billId)
            self.write(DataProtocol.getSuccessJson(billData))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


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
        userid = self.getCurrentUser()
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
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "some of parms are invalid!!"))
            self.finish()

# this function is dulpricated!
class RecomendBillHandler(BaseHandler):

    @auth
    def post(self):
        mylog.getlog().info(getLogText("get recomend bills"))
        service = self.getDbService()
        userid = self.getCurrentUser()
        usertype = self.getUserType()
        if usertype and service:
            user = service.getUserBaseData(userid)
            query = {}
            query["billType"] = "goods" if usertype == UserType.DRIVER else "trunk"
            mylog.getlog().info(getLogText("find:", query["billType"]))
            bills = service.findBills(query)

            billusers = []
            for bill in bills:
                print bill
                service.visitBill(bill["id"])
                senderId = bill["sender"]
                #hack!!!!
                bill["sender"] = str(bill["sender"])
                if not senderId in billusers:
                    billusers.append(senderId)

            #push to user whose bills have visited.
            for item in billusers:
                if service.hasUserOfId(item):
                    sender = service.getUserBaseData(item)
                    if "jpushId" in sender:
                        JPushMsgToId(sender["jpushId"], createprotocol(JPushProtocal.BILL_VISITED))
                else:
                    print "billuser don't exist!!"
            print "recoment bills return :", len(bills)
            self.write(DataProtocol.getSuccessJson(bills))
        elif not usertype:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "usertype is missing!"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))


class GetRecommendBillsHandler(BaseHandler):

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        mylog.getlog().info(getLogText("get recomend bills"))
        usertype = self.getUserType()
        findtype = BillType.GOODS if usertype == UserType.DRIVER else BillType.TRUNK
        bills = yield Bill.findMul(0, 1000, billType=findtype)

        userIds = []
        for bill in bills:
            bill.visitedTimes += 1
            bill.visitedChange = True
            senderId = bill.sender
            if not senderId in userIds:
                sender = yield User.get(senderId)
                if sender and sender.getJPushId(bill.billType):
                    JPushMsgToId(sender.getJPushId(bill.billType), createprotocol(JPushProtocal.BILL_VISITED))
                userIds.append(senderId)

        print "recommend bills return:", len(bills)
        self.finish(DataProtocol.getSuccessJson([bill.to_client() for bill in bills]))


class BillCallHandler(BaseHandler):

    @auth
    def post(self):
        targetId = self.get_argument("targetId", None)
        billtype = self.get_argument("billType", None)
        usertype = usertypeofbill(billtype)
        userid = self.getCurrentUser()
        service = self.getDbService()
        print "get bill call to:", targetId, "usertype", usertype
        if not service:
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))
            return
        if not (targetId and usertype):
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "lack of target id or bill type"))
            return
        user = service.getUserBaseData(userid)
        target = service.getUserBaseData(targetId)
        if "jpushId" in target and user["nickName"]:
            print "about to msg", target["jpushId"], "from:", user["nickName"]
            JPushMsgToId(target["jpushId"], createprotocol(JPushProtocal.PHONE_CALL, user["nickName"]))
            self.write(DataProtocol.getSuccessJson())
            return


class GetVisitedBillHandler(BaseHandler):

    @auth
    def post(self):
        userid = self.getCurrentUser()
        userType = self.getUserType()
        service = self.getDbService()
        if service:
            print "get visit bill"
            bills = service.getUserVisitedBills(userid, userType)
            data = dict([(bill["billId"], bill["visitedTimes"]) for bill in bills])
            self.write(DataProtocol.getSuccessJson(data))
            return
        else:
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))


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
            user = yield User.get(self.getCurrentUser())

            historyBills = yield user.getHistoryBill(self.getUserType(), fromObjId, isPrevBool)
            toReturn = []
            for hBill in historyBills:
                sender = yield User.get(hBill.senderId)
                toReturn.append({"bill":hBill.to_client(), "senderData":sender.to_history_user_data(hBill.senderType)})

            print "return %d history bills"%len(historyBills)
            self.write(DataProtocol.getSuccessJson(toReturn))
        except ValueError:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class UpdateHistoryBillHandler(BaseHandler):

    requiredParams = {
        "fromId": unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        user = yield User.get(self.getCurrentUser())
        fromId = kwargs["fromId"]

        try:
            historyBills = user.getHistoryBillList()
            fromIndex = historyBills.index(ObjectId(fromId))



        except Exception:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


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
        user = yield User.get(self.getCurrentUser())
        req = PendingRequest()
        req.reqUser = user.id
        req.reqUserType = self.getUserType()
        if billId:
            bill = yield Bill.get(billId)
            print "pick bill, senderid:", bill.sender
            sender = yield User.get(bill.sender)
            if sender:
                req.reqBill = bill.id
                req.respUser = sender.id
                req.respUserType = bill.getSenderType()
                result = yield req.save()
                if result:
                    bill.requests.append(req.id)
                    yield bill.save()
            else:
                self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
                return
        elif toUserId:
            respUser = yield User.get(toUserId)
            req.respUser = respUser.id

            yield req.save()

        print "pickBill req save!"
        self.finish(DataProtocol.getSuccessJson())


class ConfirmBillReqHandler(BaseHandler):

    requiredParams = {
        "reqId": unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        print "get confirm request"
        req = yield PendingRequest.get(kwargs["reqId"])
        requestUser = yield User.get(req.reqUser)
        responseUser = yield User.get(req.respUser)
        reqBill = yield Bill.get(req.reqBill)

        senderHistoryBill = self.createHistoryBill(responseUser, req.respUserType, reqBill)
        shbId = yield senderHistoryBill.save()
        receiverHistoryBill = self.createHistoryBill(requestUser, req.reqUserType)
        rhbId = yield receiverHistoryBill.save()

        #add each of the users a historybill.
        if shbId and rhbId:
            historyList = requestUser.ownerHistoryBills if reqBill.billType == BillType.TRUNK else requestUser.driverHistoryBills
            historyList.append(shbId)
            yield requestUser.save()
            print "requestUser", requestUser.to_mongo()

            historyList = responseUser.ownerHistoryBills if reqBill.billType == BillType.GOODS else responseUser.driverHistoryBills
            historyList.append(rhbId)
            yield responseUser.save()
            print "responseUser:", responseUser.to_mongo()
            self.finish(DataProtocol.getSuccessJson())
        else:
            self.finish(DataProtocol.getJson(DataProtocol.DB_ERROR))


    def createHistoryBill(self, sender, senderType, bill=None):
        hBill = HistoryBill()
        hBill.nickName = sender.nickName
        hBill.senderId = sender.id
        hBill.senderType = senderType
        hBill.sendTime = time.time()

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








