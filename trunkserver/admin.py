#encoding=utf-8
import tornado.ioloop
import tornado.web
from dbservice import DbService, trunkDict
from dataprotocol import DataProtocol
import md5
import time
from datetime import datetime, timedelta
import json
from mylog import mylog,getLogText
import StringIO
import sys,os
from urllib import unquote
from  jpush.YunPianRegCodeService import YunPianMsgMatch
try:
    from PIL import Image
except:
    raise EnvironmentError('Must have the PIL (Python Imaging Library).')

# service.addUser("admin", "12345678900", encryptPassword("hust430074"))  #id = 53e9cd5915a5e45c43813d1c

#打log 并加上DbServiceLog前缀
# def adminLog(*arg):
#     prefix = tuple(["admin:"])
#     arg = prefix + arg
#     mylog.getlog().info(getLogText(arg))
goodsBillDict = {
    "billType":r"trunk/goods",
    "from":"深圳福田区",
    "to":"广州天河区",
    "billTime":"138545564554",
    "IDNumber":"",

    "price":1000,
    "weight":1000,
    "material":"iron/wood",
}

trunkBillDict = {
    "billType":r"trunk/goods",
    "from":"深圳福田区",
    "to":"广州天河区",
    "billTime":"138545564554",
    "IDNumber":"",

    "trunkType":1,
    "trunkLength":7,
    "trunkLoad":1500,
    "licensePlate":"粤ASH890",
}


userDict = {
    "password":"fine",
    "nickName":"张师傅",
    "phoneNum":"1357878934",
    "username":"zql",

    "regtime":"13898394849",
    "bills":[],
    "userType":"driver/owner",
    "stars":4,

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

    "comments":["objectid"]

    #usersetting
}


#format list is for android jsonobject can't parse python list directly.
def formatList(source):
    return dict([(i, source[i]) for i in xrange(len(source))])


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


commentDict = {
    "starNum":0, #0,1,2,3
    "text":"吴师傅活不错",
    "commentTime":"138545564554",
    "fromUserName":"李小姐",
    "fromUserId":"ObjectId()",
    "toUserId":"ObjectId()",
    "billId":"ObjectId()"
}


biilDict = {
    "userType":unicode,
    "billType": unicode,

    "fromAddr": unicode,
    "toAddr": unicode,
    "billTime": unicode,
    "validTimeSec":unicode,

    "senderName":unicode,
    "phoneNum":unicode,

    "price": unicode,
    "weight": unicode,
    "material": unicode,

    "trunkType": unicode,
    "trunkLength": unicode,
    "trunkLoad": unicode,
    "licensePlate": unicode,

    "qqgroup":"",
    "qqgroupid":"",
    "editor":""
}

def encryptPassword(psw):
    return md5.new("hello"+ psw + "world").hexdigest()

def getMark(userid):
    return md5.new("buerlab"+ str(userid)).hexdigest() +"time:"+str(time.time()) 

def checkMark(userid,mark):
    if not userid or not mark:
        return False

    markArray = mark.split("time:")
    if len(markArray)<1:
        return False

    delta = timedelta(days=7) # 7天的有效期

    markTime = datetime.utcfromtimestamp(float(markArray[1]))
    today = datetime.utcfromtimestamp(time.time())

    if markTime + delta < today:
        # 已经超过期限
        return False

    # print "getMark(userid)", getMark(userid)
    if getMark(userid).split("time:")[0] == markArray[0]:
        return True 
    else:
        return False


def auth(func):
    def check(self, *args, **kwargs):
        username = self.getCurrentUser()
        
        mark = self.getMark()
        # mylog.getlog().info(getLogText("get connect username:", username, "mark:", mark))

        if username and mark and checkMark(username, mark):
            return func(self, *args, **kwargs)

        self.clear_cookie("mark")
        self.clear_cookie("username")
        self.write(DataProtocol.getJson(DataProtocol.AUTH_ERROR,"AUTH_ERROR"))
        self.finish()
        return None
        
    return check

def permission(permissionType):
    def _permission(func):
        def check(self, *args, **kwargs):
            userid = self.getCurrentUser()
            service = self.getDbService()
            user = service.getAdmin(userid)

            if permissionType in user and user[permissionType] == True:
                return func(self, *args, **kwargs)

            self.write(DataProtocol.getJson(DataProtocol.PERMISSION_DENY,"没有权限，请向管理员申请"))
            self.finish()
            return None
        
        return check

    return _permission

def authPage(func):
    def check(self, *args, **kwargs):
        username = self.getCurrentUser()
        mylog.getlog().info(getLogText("get connect username:", username))
        mark = self.getMark()
        print "authPage"
        print username,mark
        if username and mark and checkMark(username, mark):
            return func(self, *args, **kwargs)
        self.clear_cookie("mark")
        self.clear_cookie("username")
        self.redirect("/login.html")
        return None
        
    return check

def addAllowOriginHeader(func):
    def retFuc(self, *args, **kwargs):
        self.add_header("Access-Control-Allow-Origin","*")
        return func(self, *args, **kwargs)

    return retFuc

def addLog(func):
    def retFuc(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except:
            mylog.getlog().exception(getLogText("get a exception"))      
    return retFuc


class BaseHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")
    def getCurrentUser(self):
        return self.get_secure_cookie("userid")

    def getCurrentUsername(self):
        return self.get_secure_cookie("username")

    def getMark(self):
        return self.get_secure_cookie("mark")

    def getDbService(self):
        service = DbService().connect()
        
        if not service:
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"db connect error"))
            mylog.getlog().info(getLogText(DataProtocol.DB_ERROR,"db connect error"))
        return service

    def options(self):
        self.add_header("Access-Control-Allow-Methods","POST, GET, OPTIONS,DELETE,HEAD,PATCH,PUT")
        self.add_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept,X-Requested-With")

class LoginHandler(BaseHandler):
    @addLog
    def post(self):
        userinput = self.get_argument("username", None)
        psw = self.get_argument("password", None)
        service = self.getDbService()
        print "service",service
        #valid cookie or username and password can login
        if userinput and psw:
            user = service.confirmAdmin(userinput, encryptPassword(psw))
            # print 'self.get_cookie("username")', self.get_cookie("username")

            if user:

                self.set_secure_cookie("userid", str(user["_id"]))
                self.set_secure_cookie("username", str(user["username"]))
                self.set_secure_cookie("mark", getMark(user["_id"]))

                self.write(DataProtocol.getSuccessJson(user,"json"))
            else:
                self.write(DataProtocol.getJson(DataProtocol.AUTH_ERROR))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class LogoutHandler(BaseHandler):
    @addLog
    def post(self):
        self.clear_cookie("mark")
        self.clear_cookie("userid")
        self.clear_cookie("username")
        self.write(DataProtocol.getSuccessJson())


class RegisterHandler(BaseHandler):
    @addLog
    def post(self):
        username = self.get_argument("username", None)
        psw = self.get_argument("password", None)
        realname = self.get_argument("realname", None)
        bankName = self.get_argument("bankName", None)
        phoneNum = self.get_argument("phoneNum", None)
        bankNum = self.get_argument("bankNum", None)

        mylog.getlog().info(getLogText("RegisterHandler", username,psw,realname,phoneNum,bankName,bankNum))
        if username and psw:
            service = self.getDbService()

            # self.set_secure_cookie("mark", getmark(user))

            #开放注册的flag
            if False:
                self.write(DataProtocol.getJson(DataProtocol.USER_EXISTED_ERROR,"不允许注册了，请与管理员联系"))
                return
            else:
                if not service.hasAdmin(username):
                    # print "register new admin:", username
                    service.addAdmin(username, encryptPassword(psw),realname,phoneNum,bankName,bankNum)

                    #注册后顺便登录
                    user = service.confirmAdmin(username, encryptPassword(psw))
                    if user:
                        self.set_secure_cookie("userid", str(user["_id"]))
                        self.set_secure_cookie("username", str(user["username"]))
                        self.set_secure_cookie("mark", getMark(user["_id"]))

                    # print str(username)
                    # print getMark(username)
                    self.write(DataProtocol.getSuccessJson(user,"json"))

                else:
                    self.write(DataProtocol.getJson(DataProtocol.USER_EXISTED_ERROR,"管理员已经存在"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"missing username or password"))


class EditAdminHandler(BaseHandler):
    @addLog
    @auth
    def post(self):
        realname = self.get_argument("realname", None)
        bankName = self.get_argument("bankName", None)
        phoneNum = self.get_argument("phoneNum", None)
        bankNum = self.get_argument("bankNum", None)

        service = self.getDbService()
        userid = self.getCurrentUser()
        if userid:
            service.updateAdmin(userid,realname,phoneNum,bankName,bankNum)
            self.write(DataProtocol.getSuccessJson())
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))

class GetAdminHandler(BaseHandler):
    @addLog
    @auth
    def get(self):
        service = self.getDbService()
        userid = self.getCurrentUser()
        user = service.getAdmin(userid)
        mylog.getlog().info(getLogText( "GetAdminHandler user",user))

        if user:
            self.write(DataProtocol.getSuccessJson(user,"json"))
        else: 
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))

#######################Page Hanlder#######################
class LoginPageHandler(BaseHandler):
    @addLog
    def get(self):
        username = self.getCurrentUser()
        mark = self.getMark()
        if username and mark and checkMark(username, mark):
            self.redirect("/")
        else:
           self.render(rel_static_path+"/login.html")


class AddInfoHandler(BaseHandler):
    @addLog
    @authPage
    def get(self):
        self.render(rel_static_path+self.request.path)


class LoginVerifyHander(BaseHandler):
    @addLog
    @authPage
    def get(self):
        self.render(rel_static_path+self.request.path)

class LoginVerifyWithRegexHander(BaseHandler):
    @addLog
    @authPage
    def get(self,param):
        self.render(rel_static_path+self.request.path)


#TODO
class SecretPicHander(BaseHandler):
    @addLog
    @authPage
    def get(self,param):
        self.render(rel_static_path+self.request.path)

class IndexHandler(BaseHandler):
    @addLog
    def get(self):
        self.render(rel_static_path+"/index.html")

class MainPageHandler(BaseHandler):
    @addLog
    @authPage
    def get(self):
        self.render(rel_static_path+"/main.html")

class UploadIDNumHandler(BaseHandler):
    @addLog
    def post(self):
        img = self.request.files["file"][0]["body"]
        filename = self.request.files['file'][0]["filename"]

        mylog.getlog().info(getLogText("UploadIDNumHandler filename",filename))

        image = Image.open(StringIO.StringIO(buf=img))
        size = image.size
        type = image.format
        mylog.getlog().info(getLogText( "size",size))
        mylog.getlog().info(getLogText( "type",type))
        filepath = "/secret/IDNumPic/"+filename+"_" + str(int(time.time()) ) + "."+type.lower()
        image.save(static_path +filepath)
        userid = filename.split("_")[1]
        mylog.getlog().info(getLogText( userid))
        service = self.getDbService()
        service.updateUser(userid,**dict({"IDNumPicFilePath":filepath}))

        mylog.getlog().info(getLogText( "ok"))
        self.write(DataProtocol.getSuccessJson("ok","json"))

class UploadDriverLicenseHandler(BaseHandler):
    @addLog
    def post(self):
        img = self.request.files["file"][0]["body"]
        filename = self.request.files['file'][0]["filename"]
        mylog.getlog().info(getLogText( "filename",filename))

        image = Image.open(StringIO.StringIO(buf=img))
        size = image.size
        type = image.format
        mylog.getlog().info(getLogText( "size",size))
        mylog.getlog().info(getLogText( "type",type))

        filepath = "/secret/driverLicensePic/"+filename+"_" + str(int(time.time()) ) +"."+type.lower()
        image.save(static_path +filepath)
        userid = filename.split("_")[1]
        mylog.getlog().info(getLogText( userid))
        service = self.getDbService()
        service.updateUser(userid,**dict({"driverLicensePicFilePath":filepath}))
        mylog.getlog().info(getLogText( "ok"))
        self.write(DataProtocol.getSuccessJson("ok","json"))

class UploadTrunkLicenseHandler(BaseHandler):
    @addLog
    def post(self):
        img = self.request.files["file"][0]["body"]
        filename = self.request.files['file'][0]["filename"]
        mylog.getlog().info(getLogText( "filename", filename))

        image = Image.open(StringIO.StringIO(buf=img))
        size = image.size
        type = image.format


        filepath = "/secret/trunkLicensePic/"+ str(int(time.time()) ) +"."+type.lower()
        image.save(static_path + filepath)
        names = filename.split("_")
        userid = names[1]
        licensePlate = unquote(names[0].encode("utf-8"))
        trunkLicense = unquote(names[2].encode("utf-8"))
        mylog.getlog().info(getLogText( names))
        service = self.getDbService()
        service.saveTrunkLicensePic(userid,licensePlate,filepath,trunkLicense)
        mylog.getlog().info(getLogText( "ok"))
        self.write(DataProtocol.getSuccessJson("ok","json"))


class VerifyIDNumHandler(BaseHandler):
    @addLog
    @auth
    @permission("verifyPermission")
    def get(self):
        service = self.getDbService()
        usrs = service.getIDNumVerifyingUsers()
        # print usrs
        self.write(DataProtocol.getSuccessJson(usrs,"json"))

    @addLog
    @auth
    @permission("verifyPermission")
    def post(self):
        service = self.getDbService()
        userid = self.get_argument("userid",None)
        op = self.get_argument("op",None)

        if userid and op:
            if op == "pass":
                service.passIDNumVerifying(userid)
                self.write(DataProtocol.getSuccessJson("ok","json"))
            elif op== "fail":
                service.failIDNumVerifying(userid)
                self.write(DataProtocol.getSuccessJson("ok","json"))
            else:
                self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"op must be pass or fail"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"userid or op is invaill"))



class VerifyDriverLicenseHandler(BaseHandler):
    @addLog
    @auth
    @permission("verifyPermission")
    def get(self):
        service = self.getDbService()
        usrs = service.getDriverLicenseVerifyingUsers()
        self.write(DataProtocol.getSuccessJson(usrs,"json"))

    @addLog
    @auth
    @permission("verifyPermission")
    def post(self):
        service = self.getDbService()
        userid = self.get_argument("userid",None)
        op = self.get_argument("op",None)

        if userid and op:
            if op == "pass":
                service.passDriverLicenseVerifying(userid)
                self.write(DataProtocol.getSuccessJson("ok","json"))
            elif op== "fail":
                service.failDriverLicenseVerifying(userid)
                self.write(DataProtocol.getSuccessJson("ok","json"))
            else:
                self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"op must be pass or fail"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"userid or op is invaill"))

class VerifyTrunkLicenseHandler(BaseHandler):
    @addLog
    @auth
    @permission("verifyPermission")
    def get(self):
        service = self.getDbService()
        usrs = service.getTrunkLicenseVerifyingUsers()
        self.write(DataProtocol.getSuccessJson(usrs,"json"))

    @addLog
    @auth
    @permission("verifyPermission")
    def post(self):
        service = self.getDbService()
        userid = self.get_argument("userid",None)
        licensePlate = self.get_argument("licensePlate",None)
        op = self.get_argument("op",None)

        if userid and op:
            if op == "pass":
                ret = service.passTrunkLicenseVerifying(userid,licensePlate)
                if ret:
                    self.write(DataProtocol.getSuccessJson("ok","json"))
                else:
                    self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"系统出错"))
            elif op== "fail":
                ret = service.failTrunkLicenseVerifying(userid,licensePlate)
                if ret:
                    self.write(DataProtocol.getSuccessJson("ok","json"))
                else:
                    self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"系统出错"))
               
            else:
                self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"op must be pass or fail"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"userid or op is invaill"))

class UserFeedbackHandler(BaseHandler):
    @addLog
    @auth
    @permission("feedbackPermission")
    def get(self):
        service = self.getDbService()
        data = service.getFeedback()
        self.write(DataProtocol.getSuccessJson(data,"json"))

    @addLog
    def post(self):
        service = self.getDbService()
        userId = self.get_argument("userId",None)
        feedbackString = self.get_argument("feedbackString",None)


        if userId and feedbackString:
            #最长一万个字符
            if len(feedbackString)>10000:
                feedbackString = feedbackString[0:10000]

            ret = service.addFeedback(userId,feedbackString)

            if ret:
                self.write(DataProtocol.getSuccessJson())
            else:
                self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"反馈失败，请稍后再试"))

        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"userid or op is invaill"))


class AddMessageHandler(BaseHandler):
    @addLog
    def post(self):
        service = self.getDbService()
        time = self.get_argument("time",None)
        nickname = self.get_argument("nickname",None)
        content = self.get_argument("content",None)
        groupname = self.get_argument("groupname",None)
        groupid = self.get_argument("groupid",None)
        phonenum = self.get_argument("phonenum",None)
        wcUserId = self.get_argument("wcUserId",None)
        service.addToAddMessage(time,nickname,content,groupname,groupid,phonenum,wcUserId)
        self.write(DataProtocol.getSuccessJson())


class DeleteMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")
    def post(self):
        service = self.getDbService()
        id = self.get_argument("id",None)
        if(not id is None):
            mylog.getlog().info(getLogText( "id", id))
            username = self.getCurrentUsername()
            ret = service.delToAddMessage(id,username)
            self.write(DataProtocol.getSuccessJson("ok","json"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"id is invaill"))


class DoneMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")
    def post(self):
        service = self.getDbService()
        id = self.get_argument("id",None)
        if(not id is None):
            mylog.getlog().info(getLogText( "id", id))
            username = self.getCurrentUsername()
            service.doneToAddMessage(id,username)
            self.write(DataProtocol.getSuccessJson("ok","json"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"id is invaill"))

class GetMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")
    def get(self):
        service = self.getDbService()
        keyword = self.get_argument("keyword",None)
        username = self.getCurrentUsername()
        self.write(DataProtocol.getSuccessJson(service.getToAddMessage(keyword,username),"json"))


sendBillDict = {
    "userType":unicode,
    "billType": unicode,

    "fromAddr": unicode,
    "toAddr": unicode,
    "billTime": unicode,
    "validTimeSec":unicode,

    "senderName":unicode,
    "phoneNum":unicode,
    "comment":unicode,
    "IDNumber": unicode,
    "price": unicode,
    "weight": unicode,
    "material": unicode,
    "volume": unicode,
    
    "trunkType": unicode,
    "trunkLength": unicode,
    "trunkLoad": unicode,
    "licensePlate": unicode,

    "qqgroupid":"",
    "qqgroup":"",
    "wcUserId":"",
    "rawText":""
}

class SendMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")
    def post(self):

        toSave = dict([(key, self.get_argument(key, None)) for key in sendBillDict.iterkeys() if self.get_argument(key, None)])
        # mylog.getlog().info(getLogText("toSave", toSave))
        
        service = self.getDbService()
        # mylog.getlog().info(getLogText("SendMessageHandler toSave=",toSave))
        if toSave:
            ret = service.sendToAddMessage(self.getCurrentUsername(),**toSave)
            if ret:
                self.write(DataProtocol.getSuccessJson())
            else:
                self.write(DataProtocol.getJson(DataProtocol.MESSAGE_DUPLICATE_ERROR,"数据重复添加"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"args is invalid"))

# class ModifyMessageHandler(BaseHandler):
#     @auth
#     @addAllowOriginHeader
#     @permission("addInfoPermission")
#     def post(self):
#         toSave = dict([(key, self.get_argument(key, None)) for key in sendBillDict.iterkeys() if self.get_argument(key, None)])
#         service = self.getDbService()
#         print "toSave=",toSave
#         if toSave:
#             ret = service.sendToAddMessage(self.getCurrentUsername(),**toSave)
#             if ret:
#                 self.write(DataProtocol.getSuccessJson())
#             else:
#                 self.write(DataProtocol.getJson(DataProtocol.MESSAGE_DUPLICATE_ERROR,"数据重复添加"))
#         else:
#             self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"args is invalid"))

class ModifyMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")
    def post(self):
        service = self.getDbService()
        id = self.get_argument("id", None)
        if not id is None:
            ret = service.modifyMessage(id)
            self.write(DataProtocol.getSuccessJson())
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"args is invalid"))  

class GiveupMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")
    def post(self):
        service = self.getDbService()
        id = self.get_argument("id", None)
        ret = service.giveupMessage(id)
        if ret:
            self.write(DataProtocol.getSuccessJson())
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"args is invalid"))        

class GetVerifyingMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")
    def get(self):
        username = self.get_argument("username", None)
        self.write(DataProtocol.getSuccessJson())


class DeleteAddedMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")
    def post(self):
        #todo
        phoneNum = self.get_argument("phoneNum",None)
        fromAddr = self.get_argument("fromAddr",None)
        toAddr = self.get_argument("toAddr",None)
        userType = self.get_argument("userType",None)
        if phoneNum is None or fromAddr is None or toAddr is None or userType is None:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"args is invalid"))
        else:
            param = {
                "phoneNum" : phoneNum,
                "fromAddr" : fromAddr,
                "toAddr" : toAddr,
                "userType" : userType,
            }
            service = self.getDbService()
            service.deleteAddedMessage(**param)
            self.write(DataProtocol.getSuccessJson())

class GetSummaryStatHandler(BaseHandler):
    @addLog
    @auth
    @permission("seeInfoPermission")
    def get(self):
        viewmode = self.get_argument("viewmode","day")
        fromDate = self.get_argument("from",None)
        toDate =  self.get_argument("to",None)
        editor = self.get_argument("editor",None)
        groupname = self.get_argument("groupname",None)
        region = self.get_argument("region",None)
        regionmode = self.get_argument("regionmode",None)
        usertype = self.get_argument("usertype",None)
        routemode = self.get_argument("routemode",None)
        service = self.getDbService()
        if regionmode is None:
            data = service.getSummaryStat(viewmode,fromDate,toDate,editor,groupname)
        else:

            if routemode is None:
                data = service.getRegionSummaryStat(viewmode,fromDate,toDate,region,regionmode,usertype)
            else:
                data = service.getRouteSummaryStat(viewmode,fromDate,toDate,region,regionmode,usertype)

        self.write(DataProtocol.getSuccessJson(data,"json"))

class GetWorkLoadHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")
    def get(self):
        viewmode = self.get_argument("viewmode","day")
        fromDate = self.get_argument("from",None)
        toDate =  self.get_argument("to",None)
        editor = self.get_argument("editor",None)
        service = self.getDbService()
        data = service.getSummaryStat(viewmode,fromDate,toDate,editor,None)
        self.write(DataProtocol.getSuccessJson(data,"json"))


class GetToAddStatHandler(BaseHandler):
    @addLog
    @auth
    @permission("seeInfoPermission")
    def get(self):
        statemode = self.get_argument("statemode","all")
        fromDate = self.get_argument("from",None)
        toDate =  self.get_argument("to",None)
        keyword = self.get_argument("keyword",None)
        page = self.get_argument("page",None)
        perpage = self.get_argument("perpage",50)

        if not page is None:
            page = int(page)

        if not perpage is None:
            perpage = int(perpage)

        service = self.getDbService()

        print statemode,fromDate,toDate,keyword,page,perpage

        data = service.getToAddStat(statemode,fromDate,toDate,keyword,page,perpage)

        self.write(DataProtocol.getSuccessJson(data,"json"))

class GetAddedStatHandler(BaseHandler):
    @addLog
    @auth
    @permission("seeInfoPermission")
    def get(self):
        fromDate = self.get_argument("from",None)
        toDate =  self.get_argument("to",None)
        keyword = self.get_argument("keyword",None)
        page = self.get_argument("page",None)
        perpage = self.get_argument("perpage",50)
        usertype = self.get_argument("usertype",None)
        fromAddr = self.get_argument("fromAddr",None)
        toAddr = self.get_argument("toAddr",None)

        if not page is None:
            page = int(page)

        if not perpage is None:
            perpage = int(perpage)

        service = self.getDbService()

        print fromDate,toDate,keyword,page,perpage,fromAddr,toAddr

        data = service.getAddedStat(fromDate,toDate,keyword,page,perpage,usertype,fromAddr,toAddr,None)

        self.write(DataProtocol.getSuccessJson(data,"json"))

class GetVerifyingMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("confirmInfoPermission")
    def get(self):
        fromDate = self.get_argument("from",None)
        toDate =  self.get_argument("to",None)
        keyword = self.get_argument("keyword",None)
        page = self.get_argument("page",None)
        perpage = self.get_argument("perpage",50)
        usertype = self.get_argument("usertype",None)
        state = self.get_argument("state",None)

        if not page is None:
            page = int(page)

        if not perpage is None:
            perpage = int(perpage)

        service = self.getDbService()

        print fromDate,toDate,keyword,page,perpage,state

        data = service.getAddedStat(fromDate,toDate,keyword,page,perpage,usertype,None,None,state)

        self.write(DataProtocol.getSuccessJson(data,"json"))

class ConfirmMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("confirmInfoPermission")
    def post(self):
        id = self.get_argument("id",None)
        if id:
            service = self.getDbService()            
            ret = service.confirmMessage(id)
            self.write(DataProtocol.getSuccessJson(ret,"string"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"args is invalid"))

class RefuseMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("confirmInfoPermission")
    def post(self):
        id = self.get_argument("id",None)
        reason = self.get_argument("reason",None)
        if id:
            service = self.getDbService()         
            print "reason",reason   
            ret = service.refuseMessage(id,reason)
            self.write(DataProtocol.getSuccessJson(ret,"string"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"args is invalid"))

class GetRefuseMessageHandler(BaseHandler):
    @addLog
    @auth
    @permission("addInfoPermission")   
    def get(self):
        username = self.getCurrentUsername()

        if username:
            service = self.getDbService()
            ret = service.getRefuseMessage(username)
            self.write(DataProtocol.getSuccessJson(ret,"json"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"args is invalid"))

class GetLogHandler(BaseHandler):
    def cur_file_dir(self):
        #获取脚本路径
        path = sys.path[0]
        if os.path.isdir(path):
            return path
        elif os.path.isfile(path):
            return os.path.dirname(path)

    @permission("getLogPermission")  
    @addLog
    @auth
    def get(self):
        filename = self.get_argument("filename",None)
        keyword = self.get_argument("keyword",None)
        if filename is None:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"args is invalid"))
            return

        
        filePath =self.cur_file_dir() + "/log/" + filename
        print "GetLogHandler", filename,keyword,filePath
        if os.path.isfile(filePath):
            try:
                fp = open(filePath,"r")
                ret = fp.readlines()
                self.write(DataProtocol.getSuccessJson(ret,"json"))
                fp.close()
            except:
                self.write(DataProtocol.getJson(DataProtocol.FILE_ERROR))
                mylog.getlog().exception(getLogText("GetLogHandler exception"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.FILE_ERROR,"文件不存在"))



class GetLogListHandler(BaseHandler):

    def cur_file_dir(self):
        #获取脚本路径
        path = sys.path[0]
        if os.path.isdir(path):
            return path
        elif os.path.isfile(path):
            return os.path.dirname(path)

    @permission("getLogPermission") 
    @addLog
    @auth 
    def get(self):
        ret =  os.listdir(self.cur_file_dir() + "/log")
        self.write(DataProtocol.getSuccessJson(ret,"json"))

#【天天回程车】#nickname# 刚好有从 #from# 到 #to# 的 #type#，他的电话是#phonenum# 更多货源车源，尽在天天回程车，点击下载 #url#回T退订
class SendMatchMsgHandler(BaseHandler):
    @addLog
    @auth
    def post(self):
        sendTo = self.get_argument("sendTo",None)
        phonenum = self.get_argument("phonenum",None)
        nickname = self.get_argument("nickname","你好")
        _from = self.get_argument("from",None)
        _to = self.get_argument("to",None)
        usertype = self.get_argument("usertype","driver")
        comment = self.get_argument("comment",None)
        print phonenum,nickname,_from,_to

        if usertype is None or sendTo is None or phonenum is None or nickname is None or _from is None or _to is None:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
            return

        regcodeObject = YunPianMsgMatch()
        regcodeStr = regcodeObject.send(sendTo,phonenum,usertype,nickname,_from,_to,comment)

        mylog.getlog().info(regcodeStr)
        self.write(DataProtocol.getSuccessJson())

class GrabPhonenumHandler(BaseHandler):
    def post(self):
        data = self.get_argument("data",None)
        data = data.encode("utf-8")
        if data:
            dataJSON = json.loads(data)

        service = self.getDbService();
        for item in dataJSON:
            service.grabPhonenum(**item)

        self.write(DataProtocol.getSuccessJson())

class GrabBaixingUrlHandler(BaseHandler):
    def post(self):
        data = self.get_argument("data",None)
        data = data.encode("utf-8")
        if data:
            dataJSON = json.loads(data)

        service = self.getDbService();
        for url in dataJSON:
            service.saveBaixingUrl(url)

        self.write(DataProtocol.getSuccessJson())

class GetBaixingUrlHandler(BaseHandler):
    def get(self):
        service = self.getDbService();
        item = service.mongo.trunkDb.baixingUrl.find_one({"read":{'$ne':1}})
        if item:
            item["read"] = 1
            service.mongo.trunkDb.baixingUrl.update({"_id":item["_id"]},item)
            self.write(DataProtocol.getSuccessJson(item["url"],"string"))
        else:
            self.write(DataProtocol.getSuccessJson("nothing","string"))

class GrabGanjiUrlHandler(BaseHandler):
    def post(self):
        data = self.get_argument("data",None)
        data = data.encode("utf-8")
        if data:
            dataJSON = json.loads(data)

        service = self.getDbService();
        for url in dataJSON:
            service.saveGanjiUrl(url)

        self.write(DataProtocol.getSuccessJson())

class GetGanjiUrlHandler(BaseHandler):
    def get(self):
        service = self.getDbService();
        item = service.mongo.trunkDb.ganjiUrl.find_one({"read":{'$ne':1}})
        if item:
            item["read"] = 1
            service.mongo.trunkDb.ganjiUrl.update({"_id":item["_id"]},item)
            self.write(DataProtocol.getSuccessJson(item["url"],"string"))
        else:
            self.write(DataProtocol.getSuccessJson("nothing","string"))

class Get51YunliHandler(BaseHandler):
    def post(self):
        service = self.getDbService()
        data = self.get_argument("data",None)
        data = data.encode("utf-8")
        if data:
            dataJSON = json.loads(data)
            for item in dataJSON:
                service.mongo.trunkDb.grab51YunliCol.update({"phonenum":item["phonenum"]}, item, True)
                print item
            self.write(DataProtocol.getSuccessJson("nothing","string"))
        else:
            self.write(DataProtocol.getSuccessJson("fail","string"))

    def get(self):
        self.write(DataProtocol.getSuccessJson("fail","string"))


class Grab56135UrlHandler(BaseHandler):
    def post(self):
        data = self.get_argument("data",None)
        data = data.encode("utf-8")
        if data:
            dataJSON = json.loads(data)

        service = self.getDbService();
        for url in dataJSON:
            service.save56135Url(url)

        self.write(DataProtocol.getSuccessJson())

class Get56135UrlHandler(BaseHandler):
    def get(self):
        service = self.getDbService();
        item = service.mongo.trunkDb.a56135Url.find_one({"read":{'$ne':1}})
        if item:
            item["read"] = 1
            service.mongo.trunkDb.a56135Url.update({"_id":item["_id"]},item)
            self.write(DataProtocol.getSuccessJson(item["url"],"string"))
        else:
            self.write(DataProtocol.getSuccessJson("nothing","string"))

settings = {
    "login_url":"/login",
    "cookie_secret":"61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo="
}

static_path = os.path.join(os.path.dirname(__file__), "admin_dist")
rel_static_path = "admin_dist"

application = tornado.web.Application([
    (r"/api/admin/login", LoginHandler),
    (r"/api/admin/register", RegisterHandler),
    (r"/api/admin/logout", LogoutHandler),
    (r"/api/admin/edit", EditAdminHandler),
    (r"/api/admin/get", GetAdminHandler),
    (r"/api/verifyDriverLicense", VerifyDriverLicenseHandler),
    (r"/api/verifyIDNum", VerifyIDNumHandler),
    (r"/api/verifyTrunkLicense", VerifyTrunkLicenseHandler),

    (r'/', IndexHandler),
    (r'/login.html', LoginPageHandler),
    (r'/main.html', MainPageHandler),
    (r"/verifyDriverLicense.html",LoginVerifyHander),
    (r"/verifyIDNum.html",LoginVerifyHander),
    (r"/verifyTrunkLicense.html",LoginVerifyHander),
    (r"/addInfo.html",AddInfoHandler),
    (r"/seeInfo.html",LoginVerifyHander),
    (r"/match.html",LoginVerifyHander),
    (r"/me.html",LoginVerifyHander),
    (r"/log.html",LoginVerifyHander),

    (r"/upload/IDNum",UploadIDNumHandler),
    (r"/upload/trunkLicense",UploadTrunkLicenseHandler),
    (r"/upload/driverLicense",UploadDriverLicenseHandler),

    (r"/message/add",AddMessageHandler),
    (r"/message/delete",DeleteMessageHandler),
    (r"/message/done",DoneMessageHandler),
    (r"/message/get",GetMessageHandler),
    (r"/message/send",SendMessageHandler),  # 发送到verifying list
    (r"/message/getVerifying",GetVerifyingMessageHandler),   #获取审核中的消息列表
    (r"/message/getRefuse",GetRefuseMessageHandler),
    (r"/message/confirm",ConfirmMessageHandler),
    (r"/message/refuse",RefuseMessageHandler),
    (r"/message/modify",ModifyMessageHandler),
    (r"/message/giveup",GiveupMessageHandler),

    (r"/addedmessage/delete",DeleteAddedMessageHandler),

    (r"/stat/summary",GetSummaryStatHandler),
    (r"/stat/workload",GetWorkLoadHandler),
    (r"/stat/toadd",GetToAddStatHandler),
    (r"/stat/added",GetAddedStatHandler),

    (r"/msg/match",SendMatchMsgHandler),

    (r"/log/get",GetLogHandler),
    (r"/log/getList",GetLogListHandler),

    (r"/grabPhonenum",GrabPhonenumHandler),
    (r"/grabBaixingUrl",GrabBaixingUrlHandler),
    (r"/getBaixingUrl",GetBaixingUrlHandler),

    (r"/grabGanjiUrl",GrabGanjiUrlHandler),
    (r"/getGanjiUrl",GetGanjiUrlHandler),

    (r"/get51yunli",Get51YunliHandler),

    (r"/grab56135Url",Grab56135UrlHandler),
    (r"/get56135Url",Get56135UrlHandler),

    (r"/userFeedback",UserFeedbackHandler),
    # (r"/secret/(.*)",SecretPicHander),
    (r'/secret/(.*)', tornado.web.StaticFileHandler, {'path': static_path + "/secret"}),
    (r'/(.*)', tornado.web.StaticFileHandler, {'path': static_path})
], **settings)
    
def writePid():
    print "writePid"
    fileHandle = open(os.path.join(os.path.dirname(__file__), "admin.pid"),'w')
    print os.getpid()
    fileHandle.write(str(os.getpid()))
    fileHandle.close()    

writePid()
if __name__ == "__main__":
    mylog.getlog().info("application start ,http://115.29.8.74:9289")

    application.listen(9289)
    tornado.ioloop.IOLoop.instance().start()
