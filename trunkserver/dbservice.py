# encoding=utf-8
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import time
import copy
from appmodels import *
from mylog import mylog, getLogText
import json
import calendar
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
    "ownerComments": ["objectid"],

 #usersetting
    "ownerSettings": {
        "push":True,  #push推送
        "locate":False   #gps定位
    },
    "driverSettings":{
        "push":True,  #push推送
        "locate":True   #gps定位
    }

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
    "prov":"string",
    "city":"string",
    "district":"string",
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
            self.mongo.trunkDb.LocationCol.create_index([("timestamp", -1)])
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

                item["licensePlate"] = kwargs["licensePlate"] if "licensePlate" in kwargs else None
                item["type"] = kwargs["type"] if "type" in kwargs else None
                item["length"] = kwargs["length"] if "length" in kwargs else None
                item["load"] = kwargs["load"] if "load" in kwargs else None
                item["trunkPicFilePaths"] = kwargs["trunkPicFilePaths"] if "trunkPicFilePaths" in kwargs else None

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

            if "driverSettings" in userData and "locate" in userData["driverSettings"]:
                data["canLocate"] = userData["driverSettings"]["locate"]
            else:
                data["canLocate"] = True

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
                "phoneNum":userData["phoneNum"] if "phoneNum" in userData else "",
                "homeLocation":userData["homeLocation"] if "homeLocation" in userData else "",
                "regtime":userData["regtime"] if "regtime" in userData else "",
                "userType":userData["userType"] if "userType" in userData else "driver",
                "driverSettings":userData["driverSettings"] if "driverSettings" in userData else None,
                "ownerSettings":userData["ownerSettings"] if "ownerSettings" in userData else None
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

    @checkDbConn
    def getLastLocation(self,userId):
        if userId:
            item =self.mongo.trunkDb.LocationCol.find({"userId":userId}).sort([("timestamp",-1)]).limit(1)
            if item and item.count()>0:
                print "getLastLocation", item[0]
                return item[0]
            else:
                return None
        else:
            dbserviceError("getLastLocation fail the param is not correct", userId)
            return None

    @checkDbConn
    def getLocation(self,userId):
        if userId:
            location =self.mongo.trunkDb.LocationCol.find({"userId":userId}).sort([("timestamp",-1)])
            ret = []
            for item in location:
                ret.append(item)

            return ret

        else:
            dbserviceError("getLastLocation fail the param is not correct", userid)
            return None
    ############ Location相关(begin) #########


    ############ admin相关(begin) #########
    @checkDbConn
    def addAdmin(self, username, encryptPsw,realname,phoneNum,bankName,bankNum):
        print "addAdmin",username,encryptPsw,realname,phoneNum,bankName,bankNum
        self.mongo.trunkDb.adminCol.insert({"username": username, 
            "psw": encryptPsw, 
            "realname":realname,
            "phoneNum":phoneNum,
            "bankName":bankName,
            "bankNum":bankNum,
            "regtime": time.time(),
            "verifyPermission" : False,
            "feedbackPermission" : False,
            "addInfoPermission" : False,
            "seeInfoPermission" : False,
            "confirmInfoPermission" : False
        })

    @checkDbConn
    def updateAdmin(self, userid,realname,phoneNum,bankName,bankNum):
        user = self.mongo.trunkDb.adminCol.find_one({"_id": ObjectId(userid)})
        if user:
            if not realname is None:
                user["realname"] = realname

            if not phoneNum is None:
                user["phoneNum"] = phoneNum

            if not bankName is None:
                user["bankName"] = bankName

            if not bankNum is None:
                user["bankNum"] = bankNum

            self.mongo.trunkDb.adminCol.update({"_id": ObjectId(userid)},user)
        else:
            return False


    @checkDbConn
    def confirmAdmin(self, username, encryptPsw):
        condition = [{"username": username, "psw": encryptPsw}]
        item = self.mongo.trunkDb.adminCol.find_one({"$or": condition},{"psw": 0, "regtime": 0})
        return item if item else False

    @checkDbConn
    def getAdmin(self, userid):
        user = self.mongo.trunkDb.adminCol.find_one({"_id": ObjectId(userid)},{"psw": 0, "regtime": 0})
        return user

    @checkDbConn
    def getAdmin(self, userid):
        user = self.mongo.trunkDb.adminCol.find_one({"_id": ObjectId(userid)},{"psw": 0, "regtime": 0})
        return user

    @checkDbConn
    def hasAdmin(self, username):
        condition = [{"username": username}]
        return bool(self.mongo.trunkDb.adminCol.find_one({"$or": condition}))

    ############ admin相关(end) #########
    @checkDbConn
    def getIDNumVerifyingUsers(self):
        return [item for item in self.mongo.trunkDb.userCol.find({"IDNumVerified": 1},
                                                                 {"IDNum": 1, "_id": 1, "nickName": 1, "phoneNum": 1,
                                                                  "IDNumPicFilePath": 1})]

    @checkDbConn
    def passIDNumVerifying(self, userid):
        self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$set": {"IDNumVerified": 2}})

    @checkDbConn
    def failIDNumVerifying(self, userid):
        self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$set": {"IDNumVerified": 3}})

    @checkDbConn
    def getDriverLicenseVerifyingUsers(self):
        return [item for item in self.mongo.trunkDb.userCol.find({"driverLicenseVerified": 1},
                                                                 {"IDNum": 1, "_id": 1, "nickName": 1, "phoneNum": 1,
                                                                  "driverLicense": 1, "driverLicensePicFilePath": 1})]

    @checkDbConn
    def passDriverLicenseVerifying(self, userid):
        self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$set": {"driverLicenseVerified": 2}})

    @checkDbConn
    def failDriverLicenseVerifying(self, userid):
        self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, {"$set": {"driverLicenseVerified": 3}})


    @checkDbConn
    def getTrunkLicenseVerifyingUsers(self):
        trunkList = []
        for item in self.mongo.trunkDb.userCol.find({"trunks": {"$exists": True}},
                                                    {"IDNum": 1, "_id": 1, "nickName": 1, "phoneNum": 1, "trunks": 1}):
            print item
            if item.has_key("trunks"):
                data = {}
                data["_id"] = item["_id"]
                if(item.has_key("IDNum")):
                    data["IDNum"] = item["IDNum"]

                if(item.has_key("nickName")):
                    data["nickName"] = item["nickName"]

                if(item.has_key("phoneNum")):
                    data["phoneNum"] = item["phoneNum"]

                print "data=",data
                for trunk in item["trunks"]:
                    if trunk.has_key("trunkLicenseVerified") and  trunk["trunkLicenseVerified"] == 1:
                        print "trunk=",trunk
                        d = copy.copy(data)
                        print "d=",d
                        if(trunk.has_key("trunkLicensePicFilePath")):
                            d["trunkLicensePicFilePath"] = trunk["trunkLicensePicFilePath"]

                        if(trunk.has_key("trunkLicense")):
                            d["trunkLicense"] = trunk["trunkLicense"]

                        if(trunk.has_key("licensePlate")):
                            d["licensePlate"] = trunk["licensePlate"]

                        print "d=",d
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
                    trunk["trunkLicenseVerified"] = 2
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
                    trunk["trunkLicenseVerified"] = 3
                    self.mongo.trunkDb.userCol.update({"_id": ObjectId(userid)}, user)
                    return True

        return False

    @checkDbConn
    def saveTrunkLicensePic(self, userid,licensePlate, path,trunkLicense):
        user = self.mongo.trunkDb.userCol.find_one({"_id": ObjectId(userid)})

        if user and "trunks" in user:
            for trunk in user["trunks"]:
                print "compare"
                print licensePlate
                print trunk["licensePlate"].encode("utf-8")

                if trunk["licensePlate"].encode("utf-8") == licensePlate:
                    print "here"
                    trunk["trunkLicensePicFilePath"] = path
                    trunk["trunkLicense"] = trunkLicense
                    trunk["trunkLicenseVerified"] = 1
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
                if userData:
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

 ############ 用户反馈(end) #########

############ setting(begin) #########
#     def setPushSettings(self,userid,usertype,state):
#         userData = self.getUserBaseData(userid)
#         if userData:
#             if (usertype == "owner" or usertype == "driver") and type(state) == bool:
#                 if not usertype + "Settings" in userData:
#                     userData[usertype + "Settings"] = {}
#
#                 userData[usertype + "Settings"]["push"] = state
#                 self.mongo.trunkDb.userCol.update({"_id":ObjectId(userid)},{"$set":{usertype + "Settings": userData[usertype + "Settings"]}} , True)
#                 return True
#             return False
#         return False
#
#     def setGPSSettings(self,userid,usertype,state):
#         userData = self.getUserBaseData(userid)
#         if userData:
#             if (usertype == "owner" or usertype == "driver") and type(state) == bool:
#                 if not usertype + "Settings" in userData:
#                     userData[usertype + "Settings"] = {}
#
#                 userData[usertype + "Settings"]["gps"] = state
#                 self.mongo.trunkDb.userCol.update({"_id":ObjectId(userid)},{"$set":{usertype + "Settings": userData[usertype + "Settings"]}} , True)
#                 return True
#             return False
#         return False
#
#
# ############ setting(end) #########



 ############ Message(begin) #########

#state : wait ignore done
    def getToAddMessage(self,keyword,user):
        try:
            condition = {}

            if not keyword is None:
                query = re.compile(keyword)
                condition["$or"] = [
                    {"phonenum":query},
                    {"nickname":query},
                    {"content":query},
                    {"groupname":query},
                    {"groupid":query}
                ]
            ret = []

            # 清除环境
            for item in self.mongo.trunkDb.editingMessageCol.find({"editor":user}):
                print "editingMessageCol item", item
                toAddItem = self.mongo.trunkDb.toAddMessageCol.find_one({"_id":ObjectId(item["_id"])})
                toAddItem["state"] = "wait"
                toAddItem["editor"] = None

                print "toAddItem",toAddItem

                self.mongo.trunkDb.toAddMessageCol.update({"_id":ObjectId(item["_id"])},toAddItem)

            self.mongo.trunkDb.editingMessageCol.remove({"editor":user})

            for item in self.mongo.trunkDb.toAddMessageCol.find({"state":"wait"}).sort([("time",-1)]).limit(10):

                item["state"] = "editing"
                item["editor"] = user

                print "item groupid",item["groupid"]
                self.mongo.trunkDb.toAddMessageCol.update({"_id":ObjectId(item["_id"])},item)

                self.mongo.trunkDb.editingMessageCol.insert(item)
                ret.append(item)

            return ret
        except:
            mylog.getlog().exception(getLogText("getToAddMessage dbservice"))


    def delToAddMessage(self,id,user):
        self.mongo.trunkDb.editingMessageCol.remove({"_id": ObjectId(id)})
        mes = self.mongo.trunkDb.toAddMessageCol.find_one({"_id": ObjectId(id)})
        content = mes["content"]
        mes["state"] = "ignore"
        mes["editor"] = user
        print mes
        self.mongo.trunkDb.toAddMessageCol.update({"_id": ObjectId(id)},mes)

        # condition = {}
        # a = datetime.datetime.now()
        # a = a.replace(a.year,a.month,a.day-1,0,0,0)
        # ts = calendar.timegm(a.utctimetuple())
        # # condition["time"] = {}
        # # condition["time"]["$gt"] = ts * 1000
        # condition["state"] = {
        #     "$in" : ["wait", "editing"]
        # }
        # condition["content"] = content

        # print "condition",condition
        # for i in self.mongo.trunkDb.toAddMessageCol.find(condition):
        #     print "--------------",i["_id"]
        #     self.mongo.trunkDb.toAddMessageCol.update({"_id":i["_id"]},{"$set" :{"state":"ignore","editor":user}})


    def doneToAddMessage(self,id,user):
        self.mongo.trunkDb.editingMessageCol.remove({"_id": ObjectId(id)})
        mes = self.mongo.trunkDb.toAddMessageCol.find_one({"_id": ObjectId(id)})
        mes["state"] = "done"
        mes["editor"] = user
        print "mes",mes
        self.mongo.trunkDb.toAddMessageCol.update({"_id": ObjectId(id)},mes)


    def addToAddMessage(self,time,nickname,content,groupname,groupid,phonenum):

        if(self.toAddMessageExist(time,content)):
            return None

        return self.mongo.trunkDb.toAddMessageCol.insert(
            {"time":int(time),"nickname":nickname,"content":content,"groupid":groupid,"groupname":groupname,"phonenum": phonenum,"state":"wait"}
        )

    def toAddMessageExist(self,time,content):
        a = datetime.datetime.now()
        a = a.replace(a.year,a.month,a.day,0,0,0)
        ts = calendar.timegm(a.utctimetuple()) * 1000

        item = self.mongo.trunkDb.toAddMessageCol.find({"content":content,"time":{"$gt":ts}}).limit(1)
        if item and item.count()>0:
            # print "一天内算是重复添加", item
            # print '-------item[0]', item[0]
            # print "time.time() - item[0].sendTime",(time.time() - item[0]["time"]/1000)
            # if time.time() - item[0]["time"]/1000 < 24 * 60 * 60:
            #     return True
            # else:
            #     return False
            return True
        else:
            return False

    def sendToAddMessage(self,user, **kwargs):
        if kwargs:
            print "sendToAddMessage=",kwargs
            if self.AddedMessageExist(**kwargs):
                return False
            else:
                kwargs["sendTime"] = time.time()
                kwargs["editor"] = user
                kwargs["state"] = "confirming"
                return self.mongo.trunkDb.addedMessageCol.insert(kwargs)

    def AddedMessageExist(self, **kwargs):
        if kwargs:
            print "AddedMessageExist=",kwargs
            item = self.mongo.trunkDb.addedMessageCol.find({"fromAddr":kwargs["fromAddr"],
                                                    "toAddr":kwargs["toAddr"],
                                                    "userType":kwargs["userType"],
                                                    "state":{"$in":["confirming","confirmed"]},
                                                    "phoneNum":kwargs["phoneNum"]}).sort([("sendTime",-1)]).limit(1)
            if item and item.count()>0:
                # 一天内算是重复添加
                print "time.time() - item[0].sendTime",(time.time() - item[0]["sendTime"])
                if time.time() - item[0]["sendTime"] < 24 * 60 * 60:
                    return True
                else:
                    return False
            else:
                return False

    def deleteAddedMessage(self, **kwargs):
        if kwargs:
            print "DeleteAddedMessage=",kwargs
            item = self.mongo.trunkDb.addedMessageCol.find({"fromAddr":kwargs["fromAddr"],
                                                    "toAddr":kwargs["toAddr"],
                                                    "userType":kwargs["userType"],
                                                    "phoneNum":kwargs["phoneNum"]}).sort([("sendTime",-1)]).limit(1)
            print "item.count()",item.count()
            if item and item.count()>0:
                # 一天内算是重复添加

                print "deleteAddedMessage time.time() - item[0].sendTime",(time.time() - item[0]["sendTime"])
                if time.time() - item[0]["sendTime"] < 24 * 60 * 60:
                    self.mongo.trunkDb.addedMessageCol.remove({"_id":ObjectId(item[0]["_id"])})
                else:
                    return False
            else:
                return False

    def confirmMessage(self,id):
        return self.mongo.trunkDb.addedMessageCol.update({"_id":ObjectId(id)},{"$set":{"state":"confirmed"}})

    def giveupMessage(self,id):
        return self.mongo.trunkDb.addedMessageCol.update({"_id":ObjectId(id)},{"$set":{"state":"giveup"}})

    def modifyMessage(self,id):
        return self.mongo.trunkDb.addedMessageCol.remove({"_id":ObjectId(id)})

    def refuseMessage(self,id,reason):
        return self.mongo.trunkDb.addedMessageCol.update({"_id":ObjectId(id)},{"$set":{"state":"refuse","reason":reason}},True)

    def getRefuseMessage(self,username):
        ret = []
        for item in self.mongo.trunkDb.addedMessageCol.find({"editor":username,"state":"refuse"}):
            ret.append(item)
        return ret

    def getWeekTimeStr(self,_time):
        a = datetime.datetime.fromtimestamp(_time)
        b = a.replace(a.year,a.month,a.day- a.weekday(),0,0,0,0)
        c = a.replace(a.year,a.month,a.day +6 - a.weekday(),0,0,0,0)

        b1 = time.strftime("t-%Y-%m-%d",b.timetuple())
        c1 = time.strftime(":%Y-%m-%d",c.timetuple())
        return b1 + c1

    def getSummaryStat(self,viewmode,fromDate,toDate,editor,groupname):
        ret = {}
        ret["summary"] = {
            "toAddMessageIgnoreCount":0,
            "toAddMessageCount":0,
            "toAddMessageDoneCount":0,
            "toAddMessageWaitCount":0,
            "addedMessageCount":0,
            "confirmingMessageCount":0,
            "refuseMessageCount":0,
            "confirmedMessageCount":0,
            "giveupMessageCount":0
        }
        
        for item in self.mongo.trunkDb.toAddMessageCol.find():
            flag = True
            if not fromDate is None and int(item["time"])< int(fromDate):
                flag = False

            if not toDate is None and int(item["time"])> int(toDate) + 24 * 60 * 60 * 1000:
                flag = False
            if not editor is None and "editor" in item and editor != "all" and editor != item["editor"]:
                flag = False
            
            if not groupname is None and "groupname" in item and groupname != "all" and not groupname in item["groupname"].encode("utf-8"):
                flag = False

            if flag:
                ret["summary"]["toAddMessageCount"] = ret["summary"]["toAddMessageCount"] + 1
                if not editor is None and "editor" in item:
                    if not item["editor"] in ret["summary"]:
                        ret["summary"][item["editor"]] = {
                            "toAddMessageIgnoreCount":0,
                            "toAddMessageCount":0,
                            "toAddMessageDoneCount":0,
                            "toAddMessageWaitCount":0,
                            "addedMessageCount":0,
                            "confirmingMessageCount":0,
                            "refuseMessageCount":0,
                            "confirmedMessageCount":0,
                            "giveupMessageCount":0
                        }

                    ret["summary"][item["editor"]]["toAddMessageCount"] = ret["summary"][item["editor"]]["toAddMessageCount"] + 1

                if not groupname is None and "groupname" in item:
                    if not item["groupname"] in ret["summary"]:
                        ret["summary"][item["groupname"]] = {
                            "toAddMessageIgnoreCount":0,
                            "toAddMessageCount":0,
                            "toAddMessageDoneCount":0,
                            "toAddMessageWaitCount":0,
                            "addedMessageCount":0,
                            "confirmingMessageCount":0,
                            "refuseMessageCount":0,
                            "confirmedMessageCount":0,
                            "giveupMessageCount":0
                        }

                    ret["summary"][item["groupname"]]["toAddMessageCount"] = ret["summary"][item["groupname"]]["toAddMessageCount"] + 1

                if viewmode == "day":
                    if "time" in item:
                        timestr = time.strftime("t-%Y-%m-%d",time.localtime(int(item["time"])/1000))
                    else:
                        timestr = "t-2014-09-01"
                elif viewmode == "week":
                    print '(int(item["time"])/1000)',(int(item["time"])/1000)
                    timestr = self.getWeekTimeStr((int(item["time"])/1000))
                else:
                    timestr = time.strftime("t-%Y-%m",time.localtime(int(item["time"])/1000))

                if not timestr in ret:
                    ret[timestr] = {
                        "toAddMessageIgnoreCount":0,
                        "toAddMessageCount":0,
                        "toAddMessageDoneCount":0,
                        "toAddMessageWaitCount":0,
                        "addedMessageCount":0,
                        "confirmingMessageCount":0,
                        "refuseMessageCount":0,
                        "confirmedMessageCount":0,
                        "giveupMessageCount":0
                    }

                if not editor is None and "editor" in item:
                    if not item["editor"] in ret[timestr]:
                        ret[timestr][item["editor"]] = {
                            "toAddMessageIgnoreCount":0,
                            "toAddMessageCount":0,
                            "toAddMessageDoneCount":0,
                            "toAddMessageWaitCount":0,
                            "addedMessageCount":0,
                            "confirmingMessageCount":0,
                            "refuseMessageCount":0,
                            "confirmedMessageCount":0,
                            "giveupMessageCount":0
                        }

                if not groupname is None and "groupname" in item:
                    if not item["groupname"] in ret[timestr]:
                        ret[timestr][item["groupname"]] = {
                            "toAddMessageIgnoreCount":0,
                            "toAddMessageCount":0,
                            "toAddMessageDoneCount":0,
                            "toAddMessageWaitCount":0,
                            "addedMessageCount":0,
                            "confirmingMessageCount":0,
                            "refuseMessageCount":0,
                            "confirmedMessageCount":0,
                            "giveupMessageCount":0
                        }

                ret[timestr]["toAddMessageCount"] = ret[timestr]["toAddMessageCount"] + 1

                if not groupname is None and "groupname" in item:
                    ret[timestr][item["groupname"]]["toAddMessageCount"] = ret[timestr][item["groupname"]]["toAddMessageCount"] + 1

                if not editor is None and "editor" in item:
                    ret[timestr][item["editor"]]["toAddMessageCount"] = ret[timestr][item["editor"]]["toAddMessageCount"]+1

                if item["state"] == "ignore":
                    ret["summary"]["toAddMessageIgnoreCount"] = ret["summary"]["toAddMessageIgnoreCount"] + 1
                    ret[timestr]["toAddMessageIgnoreCount"] = ret[timestr]["toAddMessageIgnoreCount"] + 1
                    if not editor is None and "editor" in item:
                        ret[timestr][item["editor"]]["toAddMessageIgnoreCount"] = ret[timestr][item["editor"]]["toAddMessageIgnoreCount"]+1
                        ret["summary"][item["editor"]]["toAddMessageIgnoreCount"] = ret["summary"][item["editor"]]["toAddMessageIgnoreCount"]+1

                    if not groupname is None and "groupname" in item:
                        ret[timestr][item["groupname"]]["toAddMessageIgnoreCount"] = ret[timestr][item["groupname"]]["toAddMessageIgnoreCount"]+1
                        ret["summary"][item["groupname"]]["toAddMessageIgnoreCount"] = ret["summary"][item["groupname"]]["toAddMessageIgnoreCount"]+1

                elif item["state"] == "done":
                    ret["summary"]["toAddMessageDoneCount"] = ret["summary"]["toAddMessageDoneCount"] + 1
                    ret[timestr]["toAddMessageDoneCount"] = ret[timestr]["toAddMessageDoneCount"] + 1
                    if not editor is None and "editor" in item:
                        ret[timestr][item["editor"]]["toAddMessageDoneCount"] = ret[timestr][item["editor"]]["toAddMessageDoneCount"]+1
                        ret["summary"][item["editor"]]["toAddMessageDoneCount"] = ret["summary"][item["editor"]]["toAddMessageDoneCount"]+1

                    if not groupname is None and "groupname" in item:
                        ret[timestr][item["groupname"]]["toAddMessageDoneCount"] = ret[timestr][item["groupname"]]["toAddMessageDoneCount"]+1
                        ret["summary"][item["groupname"]]["toAddMessageDoneCount"] = ret["summary"][item["groupname"]]["toAddMessageDoneCount"]+1

                elif item["state"] == "wait":
                    ret["summary"]["toAddMessageWaitCount"] = ret["summary"]["toAddMessageWaitCount"] + 1
                    ret[timestr]["toAddMessageWaitCount"] = ret[timestr]["toAddMessageWaitCount"] + 1
                    if not editor is None and "editor" in item:
                        ret[timestr][item["editor"]]["toAddMessageWaitCount"] = ret[timestr][item["editor"]]["toAddMessageWaitCount"]+1
                        ret["summary"][item["editor"]]["toAddMessageWaitCount"] = ret["summary"][item["editor"]]["toAddMessageWaitCount"]+1

                    if not groupname is None and "groupname" in item:
                        # print '----------item["groupname"]',item["groupname"]
                        ret[timestr][item["groupname"]]["toAddMessageWaitCount"] = ret[timestr][item["groupname"]]["toAddMessageWaitCount"]+1
                        ret["summary"][item["groupname"]]["toAddMessageWaitCount"] = ret["summary"][item["groupname"]]["toAddMessageWaitCount"]+1

                
        for item in self.mongo.trunkDb.addedMessageCol.find():
            flag = True
            if not fromDate is None and int(item["sendTime"]) * 1000< int(fromDate):
                flag = False

            if not toDate is None and int(item["sendTime"]) * 1000>int(toDate) +  24 * 60 * 60 * 1000 :
                flag = False

            if not editor is None and "editor" in item and editor != "all" and editor != item["editor"]:
                flag = False

            if not "state" in item:
                item["state"] = "confirmed"
                self.mongo.trunkDb.addedMessageCol.update({"_id":item["_id"]}, {"$set":{"state":"confirmed"}})

            if flag:
                ret["summary"]["addedMessageCount"] = ret["summary"]["addedMessageCount"] + 1

                ret["summary"][ item["state"] + "MessageCount"] = ret["summary"][ item["state"] + "MessageCount"]  + 1

                if not editor is None and "editor" in item:
                    if not item["editor"] in ret["summary"]:
                        ret["summary"][item["editor"]] = {
                            "toAddMessageIgnoreCount":0,
                            "toAddMessageCount":0,
                            "toAddMessageDoneCount":0,
                            "toAddMessageWaitCount":0,
                            "addedMessageCount":0,
                            "confirmingMessageCount":0,
                            "refuseMessageCount":0,
                            "confirmedMessageCount":0,
                            "giveupMessageCount":0
                        }
                        
                    ret["summary"][item["editor"]]["addedMessageCount"] = ret["summary"][item["editor"]]["addedMessageCount"] + 1
                    ret["summary"][item["editor"]][ item["state"] + "MessageCount"] = ret["summary"][item["editor"]][ item["state"] + "MessageCount"]  + 1

                if(viewmode == "day"):
                    timestr = time.strftime("t-%Y-%m-%d",time.localtime(int(item["sendTime"])))
                elif viewmode == "week":
                    timestr = self.getWeekTimeStr(int(item["sendTime"]))
                else:
                    timestr = time.strftime("t-%Y-%m",time.localtime(int(item["sendTime"])))
                if not timestr in ret:
                        ret[timestr] = {
                            "toAddMessageIgnoreCount":0,
                            "toAddMessageCount":0,
                            "toAddMessageDoneCount":0,
                            "toAddMessageWaitCount":0,
                            "addedMessageCount":0,
                            "confirmingMessageCount":0,
                            "refuseMessageCount":0,
                            "confirmedMessageCount":0,
                            "giveupMessageCount":0
                        }
                ret[timestr]["addedMessageCount"] = ret[timestr]["addedMessageCount"] + 1
                ret[timestr][ item["state"] + "MessageCount"] = ret[timestr][ item["state"] + "MessageCount"] + 1

                if not editor is None and "editor" in item:
                    if not item["editor"] in ret[timestr]:
                        ret[timestr][item["editor"]] = {
                            "toAddMessageIgnoreCount":0,
                            "toAddMessageCount":0,
                            "toAddMessageDoneCount":0,
                            "toAddMessageWaitCount":0,
                            "addedMessageCount":0,
                            "confirmingMessageCount":0,
                            "refuseMessageCount":0,
                            "confirmedMessageCount":0,
                            "giveupMessageCount":0
                        }
                    ret[timestr][item["editor"]]["addedMessageCount"] = ret[timestr][item["editor"]]["addedMessageCount"] + 1
                    ret[timestr][item["editor"]][ item["state"] + "MessageCount"] = ret[timestr][item["editor"]][ item["state"] + "MessageCount"] +1
        return ret;

    def getRegionSummaryStat(self,viewmode,fromDate,toDate,region,regionmode,usertype):
        ret = {}
        for item in self.mongo.trunkDb.addedMessageCol.find():
            # print item
            flag = True
            if not fromDate is None and int(item["sendTime"]) * 1000< int(fromDate):
                print 'region != "prov" and region != "city" and region !="district"'
                flag = False

            if not toDate is None and int(item["sendTime"]) * 1000>int(toDate) +  24 * 60 * 60 * 1000 :
                print 'region != "prov" and region != "city" and region !="district"'
                flag = False

            if regionmode != "prov" and regionmode != "city" and regionmode !="district":
                print 'regionmode != "prov" and regionmode != "city" and regionmode !="district"'
                flag = False

            #根据货源来筛选
            if not usertype is None and usertype != "all" and usertype != item["userType"]:
                print 'not usertype is None and usertype != "all" and usertype != item["usertype"]:'
                flag = False

            #排除格式不对的
            if len(item["fromAddr"].split("-"))!=3 or len(item["toAddr"].split("-"))!=3:
                print 'not usertype is None and usertype != "all" and usertype != item["usertype"]:'
                flag = False

            #筛选
            if not region is None and region != "all" and (not region in item["fromAddr"].encode("utf-8") and not region in item["toAddr"].encode("utf-8")):
                print region,item["fromAddr"],item["toAddr"]
                print 'not region is None and (not region in item["fromAddr"] and not region in item["toAddr"])'
                flag = False

            # print "flag",flag
            if flag:
                if not "summary" in ret:
                    ret["summary"] = {}

                if(regionmode == "prov"):
                    fromStr = item["fromAddr"].split("-")[0]
                    toStr = item["toAddr"].split("-")[0]
                elif(regionmode == "city"):
                    fromStr = item["fromAddr"].split("-")[1]
                    toStr = item["toAddr"].split("-")[1]
                else:
                    fromStr = item["fromAddr"].split("-")[2]
                    toStr = item["toAddr"].split("-")[2]

                if(viewmode == "day"):
                    timestr = time.strftime("t-%Y-%m-%d",time.localtime(int(item["sendTime"])))
                elif viewmode == "week":
                    timestr = self.getWeekTimeStr(int(item["sendTime"]))    
                else:
                    timestr = time.strftime("t-%Y-%m",time.localtime(int(item["sendTime"])))

                if not fromStr in ret["summary"]:
                    ret["summary"][fromStr] = {
                        "from":0,
                        "to":0
                    }
                if not toStr in ret["summary"]:
                    ret["summary"][toStr] = {
                        "from":0,
                        "to":0
                    }

                ret["summary"][fromStr]["from"] = ret["summary"][fromStr]["from"] + 1
                ret["summary"][toStr]["to"] = ret["summary"][toStr]["to"] + 1

                if not timestr in ret:
                    ret[timestr] = {}

                if not fromStr in ret[timestr]:
                    ret[timestr][fromStr] = {
                        "from":0,
                        "to":0
                    }
                if not toStr in ret[timestr]:
                    ret[timestr][toStr] = {
                        "from":0,
                        "to":0
                    }

                ret[timestr][fromStr]["from"] = ret[timestr][fromStr]["from"] + 1
                ret[timestr][toStr]["to"] = ret[timestr][toStr]["to"] + 1

        return ret

    def getRouteSummaryStat(self,viewmode,fromDate,toDate,region,regionmode,usertype):
        ret = {}
        for item in self.mongo.trunkDb.addedMessageCol.find():
            # print item
            flag = True
            if not fromDate is None and int(item["sendTime"]) * 1000< int(fromDate):
                print 'region != "prov" and region != "city" and region !="district"'
                flag = False

            if not toDate is None and int(item["sendTime"]) * 1000>int(toDate) +  24 * 60 * 60 * 1000 :
                print 'region != "prov" and region != "city" and region !="district"'
                flag = False

            if regionmode != "prov" and regionmode != "city" and regionmode !="district":
                print 'regionmode != "prov" and regionmode != "city" and regionmode !="district"'
                flag = False

            #根据货源来筛选
            if not usertype is None and usertype != "all" and usertype != item["userType"]:
                print 'not usertype is None and usertype != "all" and usertype != item["usertype"]:'
                flag = False

            #排除格式不对的
            if len(item["fromAddr"].split("-"))!=3 or len(item["toAddr"].split("-"))!=3:
                print 'not usertype is None and usertype != "all" and usertype != item["usertype"]:'
                flag = False

            #筛选
            if not region is None and region != "all" and (not region in item["fromAddr"].encode("utf-8") and not region in item["toAddr"].encode("utf-8")):
                print region,item["fromAddr"],item["toAddr"]
                print 'not region is None and (not region in item["fromAddr"] and not region in item["toAddr"])'
                flag = False

            print "flag",flag
            if flag:
                if not "summary" in ret:
                    ret["summary"] = {}

                if(regionmode == "prov"):
                    fromStr = item["fromAddr"].split("-")[0]
                    toStr = item["toAddr"].split("-")[0]
                elif(regionmode == "city"):
                    fromStr = item["fromAddr"].split("-")[1]
                    toStr = item["toAddr"].split("-")[1]
                else:
                    fromStr = item["fromAddr"].split("-")[2]
                    toStr = item["toAddr"].split("-")[2]

                if(viewmode == "day"):
                    timestr = time.strftime("t-%Y-%m-%d",time.localtime(int(item["sendTime"])))
                elif viewmode == "week":
                    timestr = self.getWeekTimeStr(int(item["sendTime"]))
                else:
                    timestr = time.strftime("t-%Y-%m",time.localtime(int(item["sendTime"])))

                addrStr = fromStr + "-" + toStr

                if not addrStr in ret["summary"]:
                    ret["summary"][addrStr] = {
                        "count":0
                    }

                ret["summary"][addrStr]["count"] = ret["summary"][addrStr]["count"] + 1

                if not timestr in ret:
                    ret[timestr] = {}

                if not addrStr in ret[timestr]:
                    ret[timestr][addrStr] = {
                        "count":0
                    }

                ret[timestr][addrStr]["count"] = ret[timestr][addrStr]["count"] + 1

        return ret


    def getToAddStat(self,statemode,fromDate,toDate,keyword,page,perpage):
        condition = {}
        if not statemode is None:
            if statemode != "all":
                condition["state"] = statemode

        if not fromDate is None:
            if not "time" in condition:
                condition["time"] = {}

            condition["time"]["$gt"] = int(fromDate)

        if not toDate is None:
            if not "time" in condition:
                condition["time"] = {}
            condition["time"]["$lt"] = int(toDate) + 24 * 60 * 60 * 1000

        if not keyword is None:
            query = re.compile(keyword)
            condition["$or"] = [
                {"phonenum":query},
                {"nickname":query},
                {"content":query},
                {"groupname":query},
                {"groupid":query},
                {"editor":query}
            ]

        if page is None or page <=0:
            page = 1
        if perpage is None:
            perpage = 50

        start = (page -1) * perpage

        print "condition",condition

        data = self.mongo.trunkDb.toAddMessageCol.find(condition).skip(start)
        pageCount = int(self.mongo.trunkDb.toAddMessageCol.find(condition).count()/perpage) +1
        ret = {
            "pageCount" : pageCount,
            "curPage":page,
            "data" : []
        }
        for item in data.limit(perpage):
            ret["data"].append(item)
        return ret

    def getAddedStat(self,fromDate,toDate,keyword,page,perpage,usertype,fromAddr,toAddr,state):
        condition = {}

        if not usertype is None:
            if usertype != "all":
                condition["userType"] = usertype

        if not fromAddr is None:
            query = re.compile(fromAddr)
            condition["fromAddr"] = query

        if not toAddr is None:
            query = re.compile(toAddr)
            condition["toAddr"] = query

        if not fromDate is None:
            if not "sendTime" in condition:
                condition["sendTime"] = {}

            condition["sendTime"]["$gt"] = int(fromDate)/1000

        if not toDate is None:
            if not "sendTime" in condition:
                condition["sendTime"] = {}

            condition["sendTime"]["$lt"] = int(toDate)/1000 + 24 * 60 * 60

        if not state is None:
            if state != "all":
                condition["state"] = state

        if not keyword is None:
            query = re.compile(keyword)
            condition["$or"] = [
                {"phoneNum":query},
                {"fromAddr":query},
                {"toAddr":query},
                {"senderName":query},
                {"sendTime":query},
                {"comment":query},
                {"editor":query}
            ]

        if page is None or page <=0:
            page = 1
        if perpage is None:
            perpage = 50

        start = (page -1) * perpage

        print "condition",condition

        data = self.mongo.trunkDb.addedMessageCol.find(condition).skip(start)
        pageCount = int(self.mongo.trunkDb.addedMessageCol.find(condition).count()/perpage) +1
        ret = {
            "pageCount" : pageCount,
            "curPage":page,
            "data" : []
        }
        for item in data.limit(perpage):
            ret["data"].append(item)
        return ret
 ############ Message(end) #########


