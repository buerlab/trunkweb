#encoding=utf-8
__author__ = 'zhongqiling'


from tornado.options import options
from models import *
from appmodels import *
from datetime import datetime, timedelta


class Bill(Document):
    db_alias = "trunkDb"
    col_name = "billCol"

    billType = StringField(regex=BillType.GOODS+"|"+BillType.TRUNK, required=True)
    sender = ObjectIdField(default="")
    senderName = StringField(default="")
    phoneNum = StringField(regex="^[0-9]*$", default="")

    fromAddr = StringField()
    toAddr = StringField()
    state = StringField(default=BillState.WAIT, innerData=True)
    billTime = TimeStampField()

    receiver = StringField(default="")
    IDNumber = StringField()
    sendTime = TimeStampField()
    visitedTimes = IntField(default=0)
    visitedChange = BooleanField(default=False, innerData=True)

    price = FloatField(default=0.0, min_value=0)
    weight = FloatField(default=0.0, min_value=0)
    material = StringField()

    trunkType = StringField()
    trunkLength = FloatField(default=0, min_value=0)
    trunkLoad = FloatField(default=0, min_value=0)
    licensePlate = StringField()

    #restore all the pending request that point to this bill
    requests = ListField(ObjectIdField())

    def getSenderType(self):
        return UserType.DRIVER if self.billType == BillType.TRUNK else UserType.OWNER

    @coroutine
    def remove(self):
        if not self.sender and not self.requests:
            resp = yield super(Bill, self).remove()
            raise Return(resp)
        raise Return(None)


    @classmethod
    @coroutine
    def getWaitBills(cls):
        bills = yield cls.get_collection().find({"state":BillState.WAIT})
        raise Return(bills)


    def isOverDue(self):
        if self.sendTime:
            try:
                orgTime = datetime.fromtimestamp(float(self.billTime))
                return datetime.now()-orgTime > timedelta(minutes=options.billDueMins)
            except Exception, e:
                print "overdue error", e.message
                return False
        return False


class User(Document):
    db_alias = "trunkDb"
    col_name = "userCol"

    nickName = StringField()
    phoneNum = StringField(regex="^[0-9]*$", default="")
    username = StringField()
    psw = StringField(innerData=True)

    regtime = TimeStampField()
    bills = ListField(StringField)
    userType = StringField()

    driverJPushId = StringField()
    driverBills = ListField(ObjectIdField())
    driverHistoryBills = ListField(ObjectIdField())

    ownerJPushId = StringField()
    ownerBills = ListField(ObjectIdField())
    ownerHistoryBills = ListField(ObjectIdField())

    #optional
    IDNum = StringField()
    IDNumVerified = IntField() #0 未审核 1 审核中 2 审核通过 3 审核失败
    IDNumPicFilePath = StringField()
    driverLicense = StringField()
    driverLicenseVerified = IntField()#0 未审核 1 审核中 2 审核通过 3 审核失败
    driverLicensePicFilePath = StringField()
    homeLocation = StringField()
    trunks = ListField(DictField())

    driverStars = IntField()
    driverComments = ListField(StringField())

    ownerStars = IntField()
    ownerComments = ListField(StringField())

    pendingRequest = ListField(ObjectIdField())


    def getHistoryBillList(self, billType):
        return self.driverHistoryBills if billType == BillType.TRUNK else self.ownerHistoryBills

    def getJPushId(self, billType):
        return self.driverJPushId if billType == BillType.TRUNK else self.ownerJPushId

    def to_history_user_data(self, userType):
        data = {}
        data["userId"] = str(self.id)
        data["nickName"] = self.nickName
        data["IDNumVerified"] = self.IDNumVerified
        data["phoneNum"] = self.phoneNum
        if userType == UserType.DRIVER:
            data["driverStars"] = self.driverStars
            data["driverLicenseVerified"] = self.driverLicenseVerified
            if self.trunks:
                for trunk in self.trunks:
                    if "isUsed" in trunk and trunk["isUsed"]:
                        data["trunkLicenseVerified"] = trunk["trunkLicenseVerified"]
        elif userType == UserType.OWNER:
            data["ownerStars"] = self.ownerStars

        return data

    @coroutineDebug
    @coroutine
    def getBills(self, billType):
        billListName = "driverBills" if billType == BillType.TRUNK else "ownerBills"
        if getattr(self, billListName, None):
            query = OrQNode(ListQNode([BaseQNode(id=i) for i in self[billListName]]))
            bills = yield Bill.query(0, 1000, query)
            raise Return(bills)
        raise Return([])

    @coroutineDebug
    @coroutine
    def sendBill(self, bill):
        if not isinstance(bill, Bill):
            print "bill invalid"
            raise Return(None)
        if not self.id:
            print "sender with id is not allow to add bill"
            raise Return(None)
        bill.sender = self.id
        bill.senderName = self.nickName
        bill.sendTime = time.time()
        bill.phoneNum = self.phoneNum
        bill.state = BillState.WAIT
        yield bill.save()
        if bill.billType == BillType.TRUNK:
            self.driverBills.append(bill.id)
        elif bill.billType == BillType.GOODS:
            self.ownerBills.append(bill.id)
        yield self.save()
        raise Return(bill)

    @coroutineDebug
    @coroutine
    def removeBill(self, bill):
        if not isinstance(bill, Bill):
            print "bill invalid"
            raise Return(None)
        if not self.id:
            print "sender with id is not allow to add bill"
            raise Return(None)
        listName = self.getBillsListName(bill.billType)
        historylistName = self.getHistoryBill(bill.billType)
        if getattr(self, listName, None) and self[listName].count(bill.id)>0:
            self[listName].remove(bill.id)
            bill.sender = ""
            result = yield bill.remove()
            if result and result["ok"]:
                self.save()
            raise Return(result)
        elif getattr(self, historylistName, None) and self[historylistName].count(bill.id)>0:
            self[historylistName].remove(bill.id)
            bill.sender = ""
            result = yield bill.remove()
            if result and result["ok"]:
                self.save()
            raise Return(result)

    @coroutineDebug
    @coroutine
    def getHistoryBill(self, userType, fromBillId=None, isPrev=True):
        returnpiece = options.historyReturnPieces
        billListName = "driverHistoryBills" if userType == UserType.DRIVER else "ownerHistoryBills"
        if getattr(self, billListName, None) and len(self[billListName]) > 0:
            billLength = len(self[billListName])
            print "list length :", billLength
            fromIndex = billLength
            billIds = []
            if not fromBillId:
                #return the default history bill
                billIds = self[billListName][max(0, fromIndex-returnpiece):fromIndex]
                billIds.reverse()
            elif isinstance(fromBillId, ObjectId):
                try:
                    fromIndex = self[billListName].index(fromBillId)
                    print "get history bills from index", fromIndex
                    if isPrev:
                        #return the prev bills from the index.
                        if fromIndex > 0:
                            toIndex = max(0, fromIndex-returnpiece)
                            billIds = self[billListName][toIndex:fromIndex]
                            billIds.reverse()
                    elif fromIndex < billLength-1:
                        #return the later bills
                        toIndex = min(billLength, fromIndex+returnpiece+1)
                        billIds = self[billListName][fromIndex+1:toIndex]
                        billIds.reverse()
                except ValueError:
                    pass
            else:
                raise AssertionError("fromBillId shoule be a instance of ObjectId")

            if billIds:
                print "billid num:", len(billIds)
                query = OrQNode(ListQNode([BaseQNode(id=i) for i in billIds]))
                bills = yield HistoryBill.query(0, 1000, query)
                raise Return(bills)

        raise Return([])

    def getBillsListName(self, billType):
        return "driverBills" if billType == BillType.TRUNK else "ownerBills"

    def getBillHistoryListName(self, billType):
        return "driverHistoryBills" if billType == BillType.TRUNK else "ownerHistoryBills"


class HistoryBill(Document):
    db_alias = "trunkDb"
    col_name = "historyCol"

    billType = StringField()
    nickName = StringField()
    senderId = ObjectIdField()
    senderType = StringField()
    sendTime = TimeStampField()

    fromAddr = StringField()
    toAddr = StringField()

    fromTime = TimeStampField()
    toTime = TimeStampField()

    price = FloatField(default=0.0, min_value=0)
    weight = FloatField(default=0.0, min_value=0)
    material = StringField()


class PendingRequest(Document):
    db_alias = "trunkDb"
    col_name = "requestCol"

    reqUser = ObjectIdField()
    reqUserType = StringField()
    reqBill = ObjectIdField()

    respUser = ObjectIdField()
    respUserType = StringField()
    state = StringField(default=PendingReqState.WAITING)


    def to_client(self):
        data = {}
        data["reqId"] = str(self["id"])
        data["reqUserId"] = str(self.reqUser)
        data["reqBillId"] = str(self.reqBill)
        return data




