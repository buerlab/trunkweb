# encoding=utf-8
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import time
import copy
from appmodels import *
from mylog import mylog, getLogText
import json

from models import *

#打log 并加上DbServiceLog前缀
def dbserviceLog(*arg):
    prefix = tuple(["DbServiceLog:"])
    arg = prefix + arg
    mylog.getlog().info(getLogText(arg))


def dbserviceError(*arg):
    prefix = tuple(["DbServiceLog:"])
    arg = prefix + arg
    mylog.getlog().error(getLogText(arg))


billDict = {
    "billId": "str(ObjectId)",
    "billType": r"trunk/goods/",
    "senderName": "王师傅",

    "from": "深圳福田区",
    "to": "广州天河区",
    "state": "wait/finish/cancel/due",
    "billTime": "138545564554",
    "sender": "ObjectId()",  #could be None
    "receiver": "ObjectId()",
    "IDNumber": "",
    "sendTime": "138545564554",
    "visitedTimes":12200,
    "visitedChange":True,

    "inviteFrom": [{"from": "ObjectId", "state": 1}],
    "inviteTo": [{"to": "ObjectId", "state": 1}],

    "price": 1000,
    "weight": 1000,
    "material": "iron/wood",

    "trunkType": 1,
    "trunkLength": 7,
    "trunkLoad": 1500,
    "licensePlate": "粤ASH890"


}


userDict = {
    "password": "fine",
    "nickName": "张师傅",
    "phoneNum": "1357878934",
    "username": "zql",

    "driverJPushId":"",
    "ownerJPushId":"",

    "regtime": "13898394849",
    "bills": [],
    "userType": "driver/owner",

    "driverBills": [],
    "driverHistoryBills":[],

    "ownerBills": [],
    "ownerHistoryBills":[],

    #optional
    "IDNum":"440881198810086159",
    "IDNumVerified":"0", #0 未审核 1 审核中 2 审核通过 3 审核失败
    "IDNumPicFilePath":"123123.jpg",
    "driverLicense":"fdsfads",  
    "driverLicenseVerified":"0",#0 未审核 1 审核中 2 审核通过 3 审核失败
    "driverLicensePicFilePath":"123.jpeg",
    "homeLocation":"广东 深圳",
    "trunks":[
            {
            "isUsed":True,
            "licensePlate":"粤ASH890",
            "type":"东风",
            "length":7,
            "load":1500,
            "trunkLicense":"1230021992",
            "trunkLicenseVerified":"0", #0 未审核 1 审核中 2 审核通过 3 审核失败
            "trunkLicensePicFilePath":"123123.jpg",
            "trunkPicFilePaths":["123123.jpg","123123.jpg","123123.jpg"]
        },
        {
            "isUsed":False,
            "licensePlate":"粤ASH891",
            "type":"东风",
            "length":7,
            "load":1500,
            "trunkLicense":"1230021992",
            "trunkLicenseVerified":"0", #0 未审核 1 审核中 2 审核通过 3 审核失败
            "trunkLicensePicFilePath":"123123.jpg",
            "trunkPicFilePaths":["123123.jpg","123123.jpg","123123.jpg"]
        }
    ],

    "driverStars": 4,
    "driverComments": ["objectid"],

    "ownerStars": 4,
    "ownerComments": ["objectid"]
    #usersetting
}

commentDict = {
    "starNum": 0,  #0,1,2,
    "userType": "driver/owner",
    "text": "吴师傅活不错",
    "commentTime": "138545564554",
    "fromUserName": "李小姐",
    "fromUserId": "ObjectId()",
    "toUserId": "ObjectId()",
    "billId": "ObjectId()"
}

trunkDict = {
    "isUsed":False,
    "licensePlate":"粤ASH891",
    "type":"东风",
    "length":7,
    "load":1500,
    "trunkLicense":"1230021992",
    "trunkLicenseVerified":"0", #0 未审核 1 审核中 2 审核通过 3 审核失败
    "trunkLicensePicFilePath":"123123.jpg",
    "trunkPicFilePaths":["123123.jpg","123123.jpg","123123.jpg"]
}

LocationDict = {
    "userId": "ObjectId()",
    "latitude": "string",
    "longitude": "string",
    "timestamp": "138545564554"
}

class BillContainerName():
    Driver = "driverBills"
    Owner = "ownerBills"


def genBillItems(items):
    bills = []
    for item in items:
        bills.append(formatBillId(item))
    return bills


def formatBillId(item):
    if item:
        item["id"] = str(item.pop("_id"))
    return item


def formatUserId(item):
    item["userId"] = str(item.pop("_id"))
    return item


def genCommentItems(items):
    comments = []
    for item in items:
        comments.append(decoCommentId(item))
    return comments


def decoCommentId(item):
    item["commentId"] = str(item.pop("_id"))
    return item


def checkDbConn(func):
    '''this decorator should used on a DbService instance'''

    def check(self, *args, **kwargs):
        if not self.mongo:
            mylog.getlog().info("db has not connected,please use connect() before!")
            return None
        return func(self, *args, **kwargs)

    return check


class DbService(object):
    DEBUG_MODE = False
    # addr = "115.29.8.74"
    # addr = "localhost"
    addr = "115.29.8.74"
    port = 16888
    user = "zql"
    psw = "fine"

    def __init__(self):
        self.mongo = None
        self.db = None
        if self.DEBUG_MODE:
            self.addr = "localhost"
            self.port = "27017"

        try:
            with open("config.json", "r") as f:
                self.conf = json.load(f)
        except Exception, e:
            dbserviceError("config.json load error", e)
        else:
            pass
        finally:
            pass

    def connect(self):
        ''' return a bool value to indicate if exec success '''
        if self.mongo:
            mylog.getlog().info("mongo db has connected!")
            return self
        try:
            self.mongo = MongoClient(self.addr, self.port)

            if not self.DEBUG_MODE:
                self.mongo.trunkDb.authenticate(self.user, self.psw)
            self.mongo.trunkDb.regcodeCol.create_index([("timestamp", -1)])
            self.mongo.trunkDb.feedbackCol.create_index([("time", -1)])
        except:
            mylog.getlog().info("db connect error!!")
            self.mongo = None
            return None
        return self

    def close(self):
        if self.mongo:
            self.mongo.close()
            self.mongo = None

        #-----------------------
        #config
        #-----------------------

    def getConf(self, _type):
        if self.conf.has_key(_type):
            return self.conf[_type]

    @checkDbConn
    def hasUser(self, userinput):
        condition = [{"username": userinput}, {"phoneNum": userinput}]
        return bool(self.mongo.trunkDb.userCol.find_one({"$or": condition}))


    def hasUserOfId(self, userId):
        return bool(self.mongo.trunkDb.userCol.find_one({"_id":ObjectId(userId)}))

    @checkDbConn
    def addUser(self, username, phoneNum, encryptPsw):
        return self.mongo.trunkDb.userCol.insert(
            {"username": username, "phoneNum": phoneNum, "psw": encryptPsw, "regtime": time.time()})

    @checkDbConn
    def updateUser(self, userid, **kwargs):
        if kwargs and not kwargs.viewkeys() - userDict.viewkeys():
            self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$set": kwargs})
            return True
        else:
            return False

    @checkDbConn
    def addUserATrunk(self, userid, **kwargs):
        if kwargs and not bool(kwargs.viewkeys()-trunkDict.viewkeys()):
            return self.mongo.trunkDb.userCol.update({"_id":ObjectId(userid)}, {"$push":{"trunks":kwargs}}, True)

    # @checkDbConn
    # def updateUserATrunk(self, userid, **kwargs):
    #     if kwargs and not bool(kwargs.viewkeys()-trunkDict.viewkeys()):
    #
    #         licensePlate = kwargs["updateUserATrunk"]
    #         return self.mongo.trunkDb.userCol.update({"_id":ObjectId(userid),"trunks.licensePlate":licensePlate},
    #                                                  {"set":{"trunks.$":kwargs}}, True)

    @checkDbConn
    def deleteUserATrunk(self, userid, licensePlate):
        trunk = self.getUserTrunk(userid,licensePlate)
        if trunk is None:
            print "trunk is None"
            return False

        ret = self.mongo.trunkDb.userCol.update({"_id":ObjectId(userid)}, {"$pull":{"trunks":{"licensePlate":licensePlate}}}, True)    

        print "ret",ret    
        #如果当前车辆被删了，那么第一辆车为当前车辆
        if ret and trunk["isUsed"]:
            print 'trunk["isUsed"]'
            trunks = self.getUserTrunks(userid)
            trunks[0]["isUsed"] = True
            print "trunks", trunks
            ret = self.mongo.trunkDb.userCol.update({"_id":ObjectId(userid)}, {"trunks":trunks}, True)
        return ret
        

    @checkDbConn
    def getUserTrunks(self, userid):
        user = self.mongo.trunkDb.userCol.find_one({"_id":ObjectId(userid)},{"trunks":1,"_id":0})
        if not "trunks" in user:
            return None

        trunks = user["trunks"]
        return trunks

    @checkDbConn
    def getUserTrunk(self, userid,licensePlate):
        user = self.mongo.trunkDb.userCol.find_one({"_id":ObjectId(userid)},{"trunks":1,"_id":0})
        if not "trunks" in user:
            return None

        trunks = user["trunks"]
        trunk = None
        for item in trunks:
            if item["licensePlate"].encode("utf-8") == licensePlate:
                trunk = item
        return trunk

    @checkDbConn
    def updateUserATrunk(self, userid, **kwargs):
        trunks = self.getUserTrunks(userid)
        user = self.mongo.trunkDb.userCol.find_one({"_id":ObjectId(userid)})

        licensePlate = kwargs["licensePlate"]

        for item in trunks:
            print "------licensePlate",licensePlate
            print item["licensePlate"]
            print item["licensePlate"].encode("utf-8")
            if item["licensePlate"].encode("utf-8") == licensePlate:
                for v in kwargs:
                    item[v] = kwargs[v]
                print "here"
            else:
                print "can not find this trunk"

        user["trunks"] = trunks
        return self.mongo.trunkDb.userCol.update({"_id":ObjectId(userid)}, user, True)

    @checkDbConn
    def setUsedTrunk(self, userid,licensePlate):
        trunks = self.getUserTrunks(userid)
        user = self.mongo.trunkDb.userCol.find_one({"_id":ObjectId(userid)})

        for item in trunks:
            if item["licensePlate"].encode("utf-8") == licensePlate:
                item["isUsed"] = True
            else:
                item["isUsed"] = False

        user["trunks"] = trunks
        return self.mongo.trunkDb.userCol.update({"_id":ObjectId(userid)}, user, True)

    @checkDbConn
    def confirmUser(self, userinput, encryptPsw):
        print "psw", encryptPsw
        condition = [{"username": userinput, "psw": encryptPsw}, {"phoneNum": userinput, "psw": encryptPsw}]
        item = self.mongo.trunkDb.userCol.find_one({"$or": condition})
        return item["_id"] if item else False

    @checkDbConn
    def getUserBaseData(self, userid):
        userData = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)})
        return formatUserId(userData) if userData else None

    @checkDbConn
    def getNickBarData(self, userid):
            userData = self.getUserBaseData(userid)

            trunks = userData["trunks"] if "trunks" in userData else []

            data = {
                "userId" : userData["userId"],
                "driverStars": userData["driverStars"] if "driverStars" in userData else 0,
                "ownerStars": userData["ownerStars"] if "ownerStars" in userData else 0,
                "driverLicenseVerified":userData["driverLicenseVerified"] if "driverLicenseVerified" in userData else "0",
                "IDNumVerified": userData["IDNumVerified"] if "IDNumVerified" in userData else "0",
                "nickName": userData["nickName"] if "nickName" in userData else ""
            }

            for trunk in trunks:
                if "isUsed" in trunk and trunk["isUsed"]:
                    data["trunkLicenseVerified"] = trunk["trunkLicenseVerified"]

            return data

    @checkDbConn
    def getUserCompleteData(self, userid, getType):
            userData = self.getUserBaseData(userid)

            if userData is None:
                return None

            trunks = userData["trunks"] if "trunks" in userData else []

            data = {
                "userId" : userData["userId"],
                "stars": userData[getType+"Stars"] if getType+"Stars" in userData else 0,
                "IDNumVerified": userData["IDNumVerified"] if "IDNumVerified" in userData else "0",
                "nickName": userData["nickName"] if "nickName" in userData else "",
                "phoneNum":userData["phoneNum"],
                "homeLocation":userData["homeLocation"],
                "regtime":userData["regtime"],
                "userType":userData["userType"]
            }

            if getType == "driver":
                for trunk in trunks:
                    if "isUsed" in trunk and trunk["isUsed"]:
                        data["trunkLicenseVerified"] = trunk["trunkLicenseVerified"]
                        data["trunk"] = trunk

                data["driverLicenseVerified"] =userData["driverLicenseVerified"] if "driverLicenseVerified" in userData else "0"

            commentIds = self.getUserComments(userid,getType, 0, -1)
            commentDatas = [self.getCommentById(commentIds[i]) for i in xrange(len(commentIds))] if commentIds else []
            for item in commentDatas:
                if "fromUserId" in item:
                    item["nickBarData"] = self.getNickBarData(item["fromUserId"])

            data["comments"] = commentDatas
            return data

    @checkDbConn
    def getUserType(self, userid):
        userData = self.getUserBaseData(userid)
        if userData and "userType" in userData:
            return userData["userType"]
        else:
            return None

    @checkDbConn
    def getNegativeUserType(self, userid):
        userData = self.getUserBaseData(userid)
        if userData and "userType" in userData:
            if userData["userType"] == "driver":
                return "owner"
            elif userData["userType"] == "owner":
                return "driver"
            else:
                return None
        else:
            return None

    def getUserBills(self, userid, billtype, fromindex, count):
        billlist = BillContainerName.Driver if billtype == BillType.TRUNK else BillContainerName.Owner
        user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)})
        if user:
            bills = user.get(billlist)
            if bills and fromindex >= 0 and fromindex <= len(bills) and count >= -1:
                return bills[fromindex:] if count == -1 else bills[fromindex: min(fromindex + count, len(bills))]
            else:
                return []
        return []

    def getUserVisitedBills(self, userid, userType):
        '''
        this func will return all bills of user in currusertype that visitedtimes has just been updated.
        it will reset the visitedChange state also.
        :param userid:
        :param userType:
        :return:
        '''
        userData = self.getUserBaseData(userid)
        billListName = "driverBills" if userType == UserType.DRIVER else "ownerBills"
        if billListName in userData:
            #get bills of user which visitedChange is True.
            bills = self.findBills({"$or":[{"_id":ObjectId(billid), "visitedChange":True} for billid in userData[billListName]]})
            for billid in userData[billListName]:
                self.mongo.trunkDb.billCol.update({"_id": ObjectId(billid)}, {"$set":{"visitedChange":False}}, True)
            return bills
        return []

    def getDefaultHistoryBills(self, userid, usertype, num):
        user = self.getUserBaseData(userid)
        historylistName = self.__gethistorybilllist__(usertype)
        historylist = user[historylistName]
        historyLength = len(historylist)
        end = max(-1, historyLength-num-1)
        query = {"$or":[{"_id":ObjectId(bid)} for bid in historylist[historyLength-1:end:-1]]}
        return self.findBills(query)

    def getHistoryBills(self, userid, usertype, fromId, num, direction):
        user = self.getUserBaseData(userid)
        historylistName = self.__gethistorybilllist__(usertype)
        historylist = user[historylistName]
        historyLength = len(historylist)
        fromIndex = historylist.find(fromId)
        if fromIndex >=0:
            end = max(-1, fromIndex-num-1) if direction == -1 else min(historyLength, fromIndex+num)
            query = {"$or":[{"_id":ObjectId(bid)} for bid in historylist[fromIndex:end:direction]]}
            return self.findBills(query)
        else:
            return []

    @checkDbConn
    def addBill(self, userid, **kwargs):
        if not kwargs.viewkeys() - billDict.viewkeys() and kwargs.has_key("billType"):
            user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)})
            if user:
                #what if the user don't has a nickname that time but add one after?
                kwargs["senderName"] = user["nickName"] if user.has_key("nickName") else ""
                kwargs["phoneNum"] = user["phoneNum"] if user.has_key("phoneNum") else ""
                kwargs["sender"] = userid
                kwargs["sendTime"] = str(time.time())
                billid = self.mongo.trunkDb.billCol.insert(kwargs)
                billlist = BillContainerName.Driver if kwargs["billType"] == BillType.TRUNK else BillContainerName.Owner
                self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$push": {billlist: str(billid)}}, True)
            else:
                print "add bill: userid is invalid!!"
        else:
            print "add bills args error!!!!"


    @checkDbConn
    def removeBill(self, usertype, billid):
        bill = self.mongo.trunkDb.billCol.find_one({"_id": ObjectId(billid)})
        senderid = bill["sender"]
        if bill:
            self.mongo.trunkDb.userCol.update({"_id": ObjectId(senderid)}, {"$pull": {self.__getbilllist__(usertype): billid}})
            self.mongo.trunkDb.billCol.remove({"_id": ObjectId(billid)})

    @checkDbConn
    def overdueBill(self, usertype, billid):
        self.finishBillByState(BillState.OVERDUE)

    def finishBill(self, usertype,  billid):
        self.finishBillByState(usertype, billid, BillState.DONE)

    def finishBillByState(self, usertype, billid, state):
        bill = self.mongo.trunkDb.billCol.find_one({"_id": ObjectId(billid)})
        senderid = bill["sender"]
        if bill and senderid:
            billlist = self.__getbilllist__(usertype)
            historybilllist = self.__gethistorybilllist__(usertype)
            self.mongo.trunkDb.userCol.update({"_id": ObjectId(senderid)}, {"$pull": {billlist: billid}})
            self.mongo.trunkDb.userCol.update({"_id": ObjectId(senderid)}, {"$push": {historybilllist: billid}}, True)
            self.mongo.trunkDb.billCol.update({"_id": ObjectId(billid)}, {"$set":{"state":state}}, True)

    @checkDbConn
    def getBillById(self, billid):
        return formatBillId(self.mongo.trunkDb.billCol.find_one({"_id": ObjectId(billid)}))

    @checkDbConn
    def getBills(self, fromAddr=None, toAddr=None):
        query = {"from": fromAddr, "to": toAddr}
        filterQuery = dict([(k, v) for k, v in query.items() if v])
        return genBillItems(self.mongo.trunkDb.billCol.find(filterQuery))

    @checkDbConn
    def getWaitBill(self):
        return self.findBills({"state":BillState.WAIT})

    @checkDbConn
    def findBills(self, query):
        '''
        :param query:
        :return: [] empty list if no bills found
        '''
        if not isinstance(query, dict):
            return None
        return genBillItems(self.mongo.trunkDb.billCol.find(query))


    @checkDbConn
    def visitBill(self, billid):
        self.mongo.trunkDb.billCol.update({"_id": ObjectId(billid)}, {"$inc":{"visitedTimes":1}}, True)
        self.mongo.trunkDb.billCol.update({"_id": ObjectId(billid)}, {"$set":{"visitedChange":True}}, True)


    @checkDbConn
    def inviteBill(self, fromBill, toBill):
        self.mongo.trunkDb.billCol.update({"_id": fromBill}, {"$push": {"inviteTo": toBill}})
        self.mongo.trunkDb.billCol.update({"_id": toBill}, {"$push": {"inviteFrom": fromBill}})


    @checkDbConn
    def connectBills(self, sourcebill, targetbill):
        self.mongo.trunkDb.billCol.update({"_id": ObjectId(sourcebill)}, {"$set": {"connect": ObjectId(targetbill)}})
        self.mongo.trunkDb.billCol.update({"_id": ObjectId(targetbill)}, {"$set": {"connect": ObjectId(sourcebill)}})

    def __getUserTypeByBill__(self, billtype):
        return UserType.DRIVER if billtype == BillType.TRUNK else UserType.OWNER

    def __getbilllist__(self, usertype):
        return BillContainerName.Driver if usertype == UserType.DRIVER else BillContainerName.Owner

    def __gethistorybilllist__(self, usertype):
        return "driverHistoryBills" if usertype == UserType.DRIVER else "ownerHistoryBills"


    ############ 评论相关(begin) #########
    @checkDbConn
    def addComment(self, **kwargs):
        print kwargs.viewkeys() - commentDict.viewkeys()
        if not kwargs.viewkeys() - commentDict.viewkeys():
            user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(kwargs["toUserId"])})
            if user:
                #what if the user don't has a nickname that time but add one after?
                kwargs["toUserName"] = user["nickName"] if user.has_key("nickName") else ""
                userType = "driver"
                if "userType" in kwargs:
                    userType = kwargs["userType"]

                commentId = self.mongo.trunkDb.commentCol.insert(kwargs)

                if not user.has_key(userType+"Stars"):
                    user[userType+"Stars"] = 0

                if not user.has_key(userType+"Comments"):
                    user[userType+"Comments"] = []

                stars = user[userType+"Stars"]
                commentCount = len(user[userType+"Comments"])


                newStars = (stars * commentCount + int(kwargs["starNum"]) ) * 1.0 / (commentCount + 1)

                print "stars=", stars
                print "commentCount", commentCount
                print 'kwargs["starNum"]', kwargs["starNum"]
                print "newStars", newStars

                user[userType+"Stars"] = newStars
                user[userType+"Comments"].append(str(commentId))
                # self.mongo.trunkDb.userCol.update({"_id":ObjectId(kwargs["toUserId"])}, {"$push":{"driverComments":str(commentId)}})
                # update driverStars
                self.mongo.trunkDb.userCol.update({"_id": ObjectId(kwargs["toUserId"])}, user)
                return True
            else:
                dbserviceError("add driverComments: userid is invalid!!")
                return False
        else:
            dbserviceError("add driverComments args error!!!!")
            return False

    @checkDbConn
    def removeComment(self, commentId):
        comment = self.mongo.trunkDb.commentCol.find_one({"_id": ObjectId(commentId)})
        print comment
        userType = "driver"
        if "userType" in comment:
            print "in comment"
            userType = comment["userType"]

        if comment:

            user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(comment["toUserId"])})
            if user:
                if not user.has_key(userType+"Stars"):
                    user[userType+"Stars"] = 0

                if not user.has_key(userType+"Comments"):
                    user[userType+"Comments"] = []

                stars = user[userType+"Stars"]
                commentCount = len(user[userType+"Comments"])

                if commentCount <=1:
                    newStars = 0
                else:
                    newStars = (stars * commentCount - comment["starNum"] ) * 1.0 / (commentCount - 1)

                print "stars=", stars
                print "commentCount", commentCount
                print "newStars", newStars

                # update driverStars
                self.mongo.trunkDb.userCol.update({"_id": ObjectId(comment["toUserId"])}, {"$set": {user[userType+"Stars"]: newStars}})

            else:
                dbserviceError("remove driverComments: userid is invalid!!")
            # update driverStars
            self.mongo.trunkDb.commentCol.update({"_id": ObjectId(commentId)}, {"$set": {"isDeleted": True}})
            self.mongo.trunkDb.userCol.update({"_id": ObjectId(comment["toUserId"])},
                                              {"$pull": {userType+"Comments": commentId}})
            return True
        else:
            dbserviceError("remove Comment fail, the commentId is not correct. commentId is ", commentId)
            return False

    @checkDbConn
    def getCommentById(self, commentId):
        comment = self.mongo.trunkDb.commentCol.find_one({"_id": ObjectId(commentId)}, {"isDeleted": False})
        if comment:
            return decoCommentId(comment)
        else:
            return None

    @checkDbConn
    def updateComment(self, commentId, starNum, text):
        comment = self.getCommentById(commentId)

        if starNum is not None and text and commentId:
            user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(comment["toUserId"])})
            if user:
                userType = "driver"
                if "userType" in comment:
                    userType = comment["userType"]

                if not user.has_key(userType+"Stars"):
                    user[userType+"Stars"] = 0

                if not user.has_key(userType+"Comments"):
                    user[userType+"Comments"] = []

                stars = user[userType+"Stars"]
                commentCount = len(user[userType+"Comments"])

                oldStarNum = comment["starNum"]

                if commentCount==0:
                    newStars = 0
                else:
                    newStars = (stars * commentCount - oldStarNum + starNum) * 1.0 / commentCount
                self.mongo.trunkDb.userCol.update({"_id": ObjectId(comment["toUserId"])}, {"$set": {userType+"Stars": newStars}})

            self.mongo.trunkDb.commentCol.update({"_id": ObjectId(commentId)},
                                                 {"$set": {"starNum": starNum, "text": text}})
            return True
        else:
            dbserviceError("update comments args error!!!!")
            return False

    @checkDbConn
    def getUserComments(self, userid,userType, fromIndex=0, count=-1):
        comments = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)}, {userType+"Comments": 1})
        if comments and userType+"Comments" in comments:
            comments = comments[userType+"Comments"]
            if comments:
                if comments and fromIndex >= 0 and fromIndex <= len(comments) and count >= -1:
                    return comments[fromIndex:] if count == -1 else comments[
                                                                    fromIndex: min(fromIndex + count, len(comments))]
                else:
                    return None
            else:
                return None
        return None
        ############ 评论相关(end) #########

    ############ Location相关(begin) #########
    @checkDbConn
    def addLocation(self, userid, latitude, longitude, prov=None, city=None, district=None, timestamp=None):
        if userid and latitude and longitude and timestamp:
            locationId = self.mongo.trunkDb.LocationCol.insert({
                "userId": str(userid),
                "latitude": str(latitude),
                "longitude": str(longitude),
                "prov": prov,
                "city": city,
                "district": district,
                "timestamp": str(timestamp)
            })
            return True
        else:
            dbserviceError("addLocation fail the param is not correct", userid, latitude, longitude, time)
            return False

    ############ Location相关(begin) #########

    ############ admin相关(begin) #########
    @checkDbConn
    def addAdmin(self, username, encryptPsw):
        self.mongo.trunkDb.adminCol.insert({"username": username, "psw": encryptPsw, "regtime": time.time()})

    @checkDbConn
    def confirmAdmin(self, username, encryptPsw):
        condition = [{"username": username, "psw": encryptPsw}]
        item = self.mongo.trunkDb.adminCol.find_one({"$or": condition})
        return item["_id"] if item else False

    @checkDbConn
    def hasAdmin(self, username):
        condition = [{"username": username}]
        return bool(self.mongo.trunkDb.adminCol.find_one({"$or": condition}))

    ############ admin相关(end) #########
    @checkDbConn
    def getIDNumVerifyingUsers(self):
        return [item for item in self.mongo.trunkDb.userCol.find({"IDNumVerified": "1"},
                                                                 {"IDNum": 1, "_id": 1, "nickName": 1, "phoneNum": 1,
                                                                  "IDNumPicFilePath": 1})]

    @checkDbConn
    def passIDNumVerifying(self, userid):
        self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$set": {"IDNumVerified": "2"}})

    @checkDbConn
    def failIDNumVerifying(self, userid):
        self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$set": {"IDNumVerified": "3"}})

    @checkDbConn
    def getDriverLicenseVerifyingUsers(self):
        return [item for item in self.mongo.trunkDb.userCol.find({"driverLicenseVerified": "1"},
                                                                 {"IDNum": 1, "_id": 1, "nickName": 1, "phoneNum": 1,
                                                                  "driverLicense": 1, "driverLicensePicFilePath": 1})]

    @checkDbConn
    def passDriverLicenseVerifying(self, userid):
        self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$set": {"driverLicenseVerified": "2"}})

    @checkDbConn
    def failDriverLicenseVerifying(self, userid):
        self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$set": {"driverLicenseVerified": "3"}})


    @checkDbConn
    def getTrunkLicenseVerifyingUsers(self):
        trunkList = []
        for item in self.mongo.trunkDb.userCol.find({"trunks": {"$exists": True}},
                                                    {"IDNum": 1, "_id": 1, "nickName": 1, "phoneNum": 1, "trunks": 1}):
            # print item
            if item.has_key("trunks"):
                data = {}
                data["_id"] = item["_id"]
                if(data.has_key("IDNum")):
                    data["IDNum"] = item["IDNum"]

                if(data.has_key("nickName")):
                    data["nickName"] = item["nickName"]

                if(data.has_key("phoneNum")):
                    data["phoneNum"] = item["phoneNum"]

                for trunk in item["trunks"]:
                    if trunk.has_key("trunkLicenseVerified") and  trunk["trunkLicenseVerified"] == "1":
                        d = copy.copy(data)
                        if(trunk.has_key("trunkLicensePicFilePath")):
                            d["trunkLicensePicFilePath"] = trunk["trunkLicensePicFilePath"]

                        if(trunk.has_key("trunkLicense")):
                            d["trunkLicense"] = trunk["trunkLicense"]

                        if(trunk.has_key("licensePlate")):
                            d["licensePlate"] = trunk["licensePlate"]

                        trunkList.append(d)
        return trunkList

    @checkDbConn
    def passTrunkLicenseVerifying(self, userid, licensePlate):
        user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)})
        print user
        print userid
        print licensePlate
        if user and "trunks" in user:

            for trunk in user["trunks"]:
                print trunk
                # print "here"
                if trunk["licensePlate"].encode("utf-8") == licensePlate:
                    print "here"
                    trunk["trunkLicenseVerified"] = "2"
                    self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, user)
                    return True

        return False

    @checkDbConn
    def failTrunkLicenseVerifying(self, userid,licensePlate):

        user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)})
        if user and user.has_key("trunks"):
            print
            for trunk in user["trunks"]:
                if trunk["licensePlate"].encode("utf-8") == licensePlate:
                    trunk["trunkLicenseVerified"] = "3"
                    self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, user)
                    return True

        return False

    @checkDbConn
    def saveTrunkLicensePic(self, userid,licensePlate, path):
        user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)})

        if user and "trunks" in user:
            for trunk in user["trunks"]:
                print "compare"
                print licensePlate
                print trunk["licensePlate"].encode("utf-8")

                if trunk["licensePlate"].encode("utf-8") == licensePlate:
                    print "here"
                    trunk["trunkLicensePicFilePath"] = path
                    trunk["trunkLicenseVerified"] = "1"
                    self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, user)
                    return True

        return False

    @checkDbConn
    def saveTrunkPic(self, userid, licensePlate, path):
        user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)})
        if user and "trunks" in user:
            for trunk in user["trunks"]:
                print 'trunk in user["trunks"]:'
                if trunk["licensePlate"].encode("utf-8") == licensePlate:
                    print 'if trunk["licensePlate"].encode("utf-8") == licensePlate:'
                    print trunk
                    if "trunkPicFilePaths" in trunk:
                        print '"trunkPicFilePaths" in trunk:'
                        trunk["trunkPicFilePaths"].append(path)
                        print "trunk", trunk
                    else:
                        print  '"trunkPicFilePaths" not in trunk:'
                        trunk["trunkPicFilePaths"] = []
                        trunk["trunkPicFilePaths"].append(path)
                        print "trunk", trunk

                    print "user=",user
                    print self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, user)
                    print "user=",user
                    return True
        return False

    @checkDbConn
    def removeTrunkPics(self, userid,licensePlate):
        user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)})
        if user and "trunks" in user:
            for trunk in user["trunks"]:
                if trunk["licensePlate"].encode("utf-8") == licensePlate:

                    trunk["trunkPicFilePaths"] =[]
                    print self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, user)
                    return True

        return False


 ############ 验证码相关(begin) #########

    def addRegCode(self,phonenum,regcode):
        return self.mongo.trunkDb.regcodeCol.insert(
            {"phonenum": phonenum, "regcode": regcode, "timestamp": time.time()})

    def checkCode(self,phonenum,regcode):

        data = self.mongo.trunkDb.regcodeCol.find({"phonenum":phonenum,"regcode":regcode}).sort([("timestamp",-1)])
        now = time.time()
        print data.count()
        if data.count()<=0:
            return False

        data = data[0]
        # print "----------"
        # print data
        # print now - data["timestamp"]

        # 10 分钟内有效
        if data and  "timestamp" in data and  (now - data["timestamp"]< 10 * 60 ):
            return True
        else:
            return False

############ 验证码相关(end) #########

 ############ 用户反馈(begin) #########

    def getFeedback(self):
        ret = []
        for item in self.mongo.trunkDb.feedbackCol.find({}).sort([("time",-1)]):
            retItem = {}
            for v in item:
                retItem[v] = item[v]

            if "userId" in item:
                userData = self.getUserBaseData(item["userId"])
                if userData.has_key("IDNum"):
                    retItem["IDNum"] = userData["IDNum"]

                if(userData.has_key("nickName")):
                    retItem["nickName"] = userData["nickName"]

                if(userData.has_key("phoneNum")):
                    retItem["phoneNum"] = userData["phoneNum"]

            ret.append(retItem)
        return ret

    def addFeedback(self,userid,feedbackString):
        if userid is None or feedbackString is None:
            return False
        now = time.time()

        return self.mongo.trunkDb.feedbackCol.insert(
            {"userId":userid,"feedbackString":feedbackString,"time":now}
        )



 ############ 用户反馈(begin) #########