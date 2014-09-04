#encoding=utf-8
__author__ = 'zhongqiling'


from tornado.options import options
from models.document import *
from appmodels import *
from datetime import datetime, timedelta
from mylog import mylog


class Bill(Document):
    db_alias = "trunkDb"
    col_name = "billCol"

    billType = StringField(regex=BillType.GOODS+"|"+BillType.TRUNK, required=True)
    sender = ObjectIdField()
    senderName = StringField(default="")
    phoneNum = StringField(regex="^[0-9]*$", default="")

    fromAddr = StringField(default="")
    toAddr = StringField(default="")
    passAddr = ListField(StringField())
    state = StringField(default=BillState.WAIT, innerData=True)
    billTime = TimeStampField()
    validTimeSec = IntField(default=8*60*60)
    source = StringField()

    receiver = StringField(default="")
    IDNumber = StringField(default="")
    sendTime = TimeStampField()
    visitedTimes = IntField(default=0)
    visitedChange = BooleanField(default=False, innerData=True)

    comment = StringField(default="")   #备注

    price = FloatField(default=0.0, min_value=0)
    weight = FloatField(default=0.0, min_value=0)  #吨
    material = StringField(default="")

    trunkType = StringField(default="")
    trunkLength = FloatField(default=0, min_value=0)
    trunkLoad = FloatField(default=0, min_value=0)
    licensePlate = StringField()

    random = IntField()


    def getSenderType(self):
        return UserType.DRIVER if self.billType == BillType.TRUNK else UserType.OWNER

    def getContraryType(self):
        return BillType.TRUNK if self.billType == BillType.GOODS else BillType.GOODS

    @coroutine
    def remove(self):
        if not self.sender:
            resp = yield super(Bill, self).remove()
            raise Return(resp)
        else:
            sender = yield User.get(self.sender, matchUserType(self.billType))
            sender.removeBill(self)


    @classmethod
    @coroutine
    def getWaitBills(cls):
        bills = yield cls.get_collection().find({"state":BillState.WAIT})
        raise Return(bills)


    def isOverDue(self):
        if self.sendTime or self.billTime:
            try:
                refTime = self.billTime or self.sendTime
                orgTime = datetime.fromtimestamp(float(refTime))
                return datetime.now()-orgTime > timedelta(seconds=self.validTimeSec)
            except Exception, e:
                print "overdue error", e.message
                return False
        return False


class User(Document):
    db_alias = "trunkDb"
    col_name = "userCol"
    currType = ""

    level = StringField(default=UserLevel.NORMAL, innerData=True)
    nickName = StringField()
    phoneNum = StringField(regex="^[0-9]*$", default="")
    username = StringField()
    psw = StringField(innerData=True)

    bonus = IntField(default=0)

    regtime = TimeStampField()
    bills = ListField(StringField)
    userType = StringField()

    driverJPushId = StringField(default="", innerData=True)
    driverBills = ListField(ObjectIdField(), innerData=True)
    driverHistoryBills = ListField(ObjectIdField(), innerData=True)
    driverBillsRecord = ListField(ObjectIdField(), innerData=True)

    ownerJPushId = StringField(default="", innerData=True)
    ownerBills = ListField(ObjectIdField(), innerData=True)
    ownerHistoryBills = ListField(ObjectIdField(), innerData=True)
    ownerBillsRecord = ListField(ObjectIdField(), innerData=True)

    #optional
    IDNum = StringField()
    IDNumVerified = IntField() #0 未审核 1 审核中 2 审核通过 3 审核失败
    IDNumPicFilePath = StringField()
    driverLicense = StringField()
    driverLicenseVerified = IntField()#0 未审核 1 审核中 2 审核通过 3 审核失败
    driverLicensePicFilePath = StringField()
    homeLocation = StringField(default="")
    currLocationIndex = IntField(default=0)
    trunks = ListField(DictField())

    driverStars = FloatField(default=0.0)
    driverComments = ListField(StringField(), innerData=True)

    ownerStars = FloatField(default=0.0)
    ownerComments = ListField(StringField(), innerData=True)

    #settings
    ownerSettings = DictField(default={})
    driverSettings = DictField(default={})

    ownerCanPush = BooleanField(default=True)
    driverCanPush = BooleanField(default=True)

    ownerCanLocate = BooleanField(default=True)
    driverCanLocate = BooleanField(default=True)


    def __init__(self, _username=None, _phoneNum=None, _psw=None):
        super(User, self).__init__()
        self.currType = ""
        self.username, self.phoneNum, self.psw = _username, _phoneNum, _psw

    @classmethod
    @coroutineDebug
    @coroutine
    def get(cls, str_id, userType=""):
        user = yield super(User, cls).get(str_id)
        if user and (userType == UserType.DRIVER or userType == UserType.OWNER):
            user.currType = userType
        raise Return(user)

    def getAttr(self, attrName):
        try:
            return self[self.currType+str(attrName)]
        except Exception, e:
            mylog.getlog().info("user get attr error:"+e.message)
            raise ValueError("get attr error!!!")

    def setAttr(self, attrName, value):
        try:
            self[self.currType+str(attrName)] = value
        except Exception, e:
            raise ValueError("USER SET ATTR ERROR"+e.message)

    def getHistoryBillList(self, billType):
        return self.driverHistoryBills if billType == BillType.TRUNK else self.ownerHistoryBills

    def getJPushId(self, billType):
        return self.driverJPushId if billType == BillType.TRUNK else self.ownerJPushId

    def getStars(self, billType):
        return self.driverStars if billType == BillType.TRUNK else self.ownerStars

    def to_user_base_data(self, _userType=None):
        userType = _userType or self.currType
        data = {}
        if userType:
            data["userType"] = userType
            if self.id:
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
                            if "trunkPicFilePaths" in trunk:
                                data["trunkPicFilePaths"] = trunk["trunkPicFilePaths"]
                if self.getAttr("Settings") and "locate" in self.getAttr("Settings"):
                    data["canLocate"] = self.getAttr("Settings")["locate"]
                else:
                    data["canLocate"] = True
            elif userType == UserType.OWNER:
                data["ownerStars"] = self.ownerStars
                data["canLocate"] = False

        return data

    @coroutineDebug
    @coroutine
    def getBills(self):
        '''
        return all the on wait bill and put the invalid bill into record.
        :return:
        '''
        if self.currType and self.getAttr("Bills"):
            billsReturn, billsRemove, billIds = [], [], self.getAttr("Bills")
            for bId in billIds:
                bill = yield Bill.get(bId)
                if bill.state == BillState.WAIT:
                    billsReturn.append(bill)
                else:
                    billsRemove.append(bId)
            if billsRemove:
                for removeId in billsRemove:
                    self.getAttr("BillsRecord").append(removeId)
                    billIds.remove(removeId)
                yield self.save()
            raise Return(billsReturn)
        else:
            raise Return([])

    @coroutineDebug
    @coroutine
    def sendBill(self, bill):
        if not self.currType:
            raise Return(None)
        if not isinstance(bill, Bill):
            print "bill invalid"
            raise Return(None)
        if not self.id:
            print "sender with id is not allow to add bill"
            raise Return(None)
        bill.sender = self.id
        bill.senderName = self.nickName
        bill.phoneNum = self.phoneNum
        yield bill.save()
        self.getAttr("Bills").append(bill.id)
        yield self.save()
        raise Return(bill)

    @coroutineDebug
    @coroutine
    def removeBill(self, bill):
        if bill.id in self.getAttr("Bills"):
            self.getAttr("Bills").remove(bill.id)
            yield self.save()
            bill.sender = ""
            yield bill.remove()

    @coroutineDebug
    @coroutine
    def billDone(self, bill):
        bill.state = BillState.DONE
        yield bill.save()
        if bill.id in self.getAttr("Bills"):
            self.getAttr("Bills").remove(bill.id)
            self.getAttr("BillsRecord").append(bill.id)
            yield self.save()
        else:
            mylog.getlog().error("attend to done a bill that is not belonged to self")

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
                query = QOr(*[BaseQNode(id=i) for i in billIds])
                bills = yield HistoryBill.query(0, 1000, query)
                raise Return(bills)

        raise Return([])

    def getBillsListName(self, billType):
        return "driverBills" if billType == BillType.TRUNK else "ownerBills"

    def getBillHistoryListName(self, billType):
        return "driverHistoryBills" if billType == BillType.TRUNK else "ownerHistoryBills"

    def getCurrTruck(self):
        for truck in self.trunks:
            if truck["isUsed"]:
                try:
                    truck["load"] = float(truck["load"])
                    truck["length"] = float(truck["length"])
                    return truck
                except Exception, e:
                    return None
        return None


class HistoryBill(Document):
    db_alias = "trunkDb"
    col_name = "historyCol"

    billType = StringField()
    nickName = StringField()
    senderId = ObjectIdField()
    senderType = StringField()
    sendTime = TimeStampField()
    state = StringField(default=BillState.WAIT)
    locateValidSec = IntField(default=24*60*60)

    fromAddr = StringField()
    toAddr = StringField()

    fromTime = TimeStampField()
    toTime = TimeStampField()

    price = FloatField(default=0.0, min_value=0)
    weight = FloatField(default=0.0, min_value=0)
    material = StringField()

    hasCommented = BooleanField(default=False)


class PendingRequest(Document):
    db_alias = "trunkDb"
    col_name = "requestCol"

    reqType = StringField(default="")

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


class Config(Document):
    db_alias = "trunkDb"
    col_name = "confCol"

    #司机地理位置可跟踪的有效期
    locateValidSec = IntField(default=24*60*60)

    #地理位置上报的频率
    locationReportFreq = IntField(default=5*60*1000)
    locationArchDays = IntField(default=10)
    locationArchIntervalHours = IntField(default=2)
    locationCacheHours = IntField(default=10)

    currUse = BooleanField(default=False)
    recommendBillsReturnOnce = IntField(default=10)
    #出发地相对于目的地的权重
    fromAddrWeight = FloatField(default=1.5)
    #发单与浏览单from to吻合 10,000,000
    billMatchWeight = IntField(default=10000000)
    billMatchRatioWeight = IntField(default=1000000)
    #相同常在地址来源权重 1,000,000
    homeLocationWeight = IntField(default=1000000)
    homeLocationRatioWeight = IntField(default=100000)
    #根据历史单的情况
    recordBillWeight = IntField(default=5000000)
    recordBillRatioWeight = IntField(default=100000)
    #时间有效期 基础权重 100,000
    timeBaseWeight = IntField(default=100000)
    #开始时间距离现在的时长系数
    timePerHourWeight = IntField(default=100)
    #评星系数
    starWeight = IntField(default=1000)
    intimeLocationWeight = IntField(default=100)
    trunkLicenseVerifiedWeight = IntField(default=100)
    trunkPicVerifiedWeight = IntField(default=100)
    driverLiscenseVerifiedWeight = IntField(default=100)
    IDVerifiedWeight = IntField(default=100)

    # locationCacheDay = IntField(default=15)
    # locationCacheHourInterval = IntField(default=1)

    @classmethod
    @coroutineDebug
    @coroutine
    def shared(cls):
        config = yield cls.objects({"currUse":True}).one()
        if not config:
            config = Config()
            config.currUse = True
            yield config.save()
        raise Return(config)

class Location(Document):
    db_alias = "trunkDb"
    col_name = "locationCol"

    index = IntField(default=0)
    isArchived = BooleanField(default=False, innerData=True)
    userId = StringField()
    latitude = StringField()
    longitude = StringField()
    prov = StringField()
    city = StringField()
    district = StringField()
    timestamp = TimeStampField()



class Regular(Document):
    db_alias = "trunkDb"
    col_name = "regularCol"


    nickName = StringField()
    phoneNum = StringField()
    userType = StringField()
    comment = StringField()
    qqgroupid = StringField()
    qqgroup = StringField()
    editor = StringField()
    time = IntField()
    role = StringField()
    
    trunkType = StringField()
    trunkLoad = StringField()
    # route dict should be like below:
    # {"fromAddr":"", "toAddr":"", "probability":1}
    routes = ListField(DictField())
