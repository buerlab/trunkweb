# encoding=utf-8
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
from tornado.options import  define, options
import signal

from handler.billhandler import *
from dataprotocol import *
from dbservice import *
from mylog import mylog, getLogText
from urllib import unquote
import StringIO
import os
from jobs import *
from models import connect
import time
from  jpush.RegCodeService import RegCode

try:
    from PIL import Image
except:
    raise EnvironmentError('Must have the PIL (Python Imaging Library).')

define("dburi", default="mongodb://root:430074@localhost:16888/admin", type=str)
define("dbaddr", default="localhost:16888", type=str)
define("dbuser", default="zql", type=str)
define("dbpsw", default="fine", type=str)
define("dbname", default="trunkDb", type=str)
# define("dburi", default="mongodb://localhost:27017", type=str)
define("port", default=9288, type=int)
define("billDueMins", default=1, type=int)
define("historyReturnPieces", default=5, type=int)

commentDict = {
    "userType": "driver/owner",
    "starNum":0, #0,1,2,3
    "text":"吴师傅活不错",
    "commentTime":"138545564554",
    "fromUserName":"李小姐",
    "fromUserId":"ObjectId()",
    "toUserId":"ObjectId()",
    "billId":"ObjectId()"
}

class IndexHandler(BaseHandler):
    def get(self):
        self.render("./dist/index.html")

    @auth
    def post(self):
        service = self.getDbService()
        mylog.getlog().info(getLogText(service))
        self.write("you make it")

class LoginHandler(BaseHandler):
    @addAllowOriginHeader
    def post(self):
        username = self.get_argument("username", None)
        phoneNum = self.get_argument("phoneNum", None)
        psw = self.get_argument("password", None)
        userinput = username or phoneNum

        service = DbService()
        service.connect()
        #valid cookie or username and password can login

        if userinput and psw:
            print "get input:", userinput, "psw:", psw
            userid = service.confirmUser(userinput, encryptPassword(psw))
            print "login userid", userid
            print 'self.get_cookie("username")', self.get_cookie("username")

            if userid:
                userData = service.getUserBaseData(userid)

                if userData.has_key("nickName") and userData["nickName"] !=None and userData["nickName"] !="":
                    self.set_cookie("nickName", userData["nickName"])
                elif userData.has_key("username") and userData["username"] !=None and userData["username"] !="":
                    self.set_cookie("nickName", userData["username"])
                elif userData.has_key("phoneNum") and userData["phoneNum"] !=None and userData["phoneNum"] !="":
                    self.set_cookie("nickName", userData["phoneNum"])

                self.set_secure_cookie("userid", str(userid))
                self.set_secure_cookie("mark", getMark(userid))


                print str(userid)
                print getMark(userid)
                self.write(DataProtocol.getSuccessJson(userData,"json"))
            else:
                self.write(DataProtocol.getJson(DataProtocol.LOGIN_FAIL,"手机号码或者密码错误，登录失败"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))



class QuickLoginHanlder(BaseHandler):
    @auth
    def post(self):
        userId = self.getCurrentUser()
        service = self.getDbService()
        userData = service.getUserBaseData(userId)
        if userData:
            self.write(DataProtocol.getSuccessJson(userData, "json"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.AUTH_ERROR))


class LogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("mark")
        self.clear_cookie("userid")
        self.clear_cookie("nickName")
        self.write(DataProtocol.getSuccessJson())

class RegisterHandler(BaseHandler):
    requiredParams = {
        "password":unicode,
    }

    optionalParams = {
        "username": unicode,
        "phoneNum": unicode
    }


    @addAllowOriginHeader
    def post(self):
        username = self.get_argument("username", None)
        psw = self.get_argument("password", None)
        phoneNum = self.get_argument("phoneNum", None)
        userinput = username or phoneNum

        if userinput and psw:
            service = DbService()
            service.connect()
            # self.set_secure_cookie("mark", getmark(user))

            if not service.hasUser(userinput):
                print "register new user:", userinput
                userid = service.addUser(username, phoneNum, encryptPassword(psw))
                print userid
                userData = service.getUserBaseData(userid)

                #注册完马上给个登录态
                self.set_secure_cookie("userid", str(userid))
                self.set_secure_cookie("mark", getMark(userid))
                self.write(DataProtocol.getSuccessJson(userData,"json"))
            else:
                self.write(DataProtocol.getJson(DataProtocol.USER_EXISTED_ERROR,"用户已经存在"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"missing username or password"))


class UserHanlder(BaseHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")
    @auth
    def put(self):
        userid = self.getCurrentUser()
        toSave = dict([(key, self.get_argument(key, None)) for key in userDict.iterkeys() if self.get_argument(key, None)])
        mylog.getlog().info(getLogText( "save user data:", toSave))
        service = self.getDbService()
        if service:
            if toSave:
                print "success"
                service.updateUser(userid, **toSave)
                self.write(DataProtocol.getSuccessJson())
            else:
                self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
        else:
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))

    @auth
    def get(self):
        userid = self.getCurrentUser()
        service = self.getDbService()
        if userid and service:
            userdata = service.getUserBaseData(userid)

            self.write(DataProtocol.getSuccessJson(userdata,"json"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class UserTrunkHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")

    @auth
    def post(self):
        userid = self.getCurrentUser()
        print "userid=", userid

        trunk = dict([(key, self.get_argument(key, None)) for key in trunkDict.iterkeys() if self.get_argument(key, None)])

        print "trunk=",trunk

        service = self.getDbService()
        if trunk:

            if not trunk.has_key("licensePlate"):
                self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
                return

            licensePlate = trunk["licensePlate"]
            if service.getUserTrunk(userid,licensePlate) is None:
                trunks = service.getUserTrunks(userid)

                print "trunks=",trunks

                if not trunks or len(trunks) == 0:
                    trunk["isUsed"] = True

                print "trunk=",trunk

                print "service.getUserBaseData(userid)"
                print service.getUserBaseData(userid)

                print "service.addUserATrunk(userid, **trunk)"
                print service.addUserATrunk(userid, **trunk)

            else:
                self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "相同车牌的货车不能重复添加"))
            self.write(DataProtocol.getSuccessJson())
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))

    @auth
    def put(self):
        userid = self.getCurrentUser()
        trunk = dict([(key, self.get_argument(key, None)) for key in trunkDict.iterkeys() if self.get_argument(key, None)])
        print "trunk=",trunk

        service = self.getDbService()
        if trunk:

            if not trunk.has_key("licensePlate"):
                self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
                return

            licensePlate = trunk["licensePlate"]
            trunkFromDB = service.getUserTrunk(userid,licensePlate)

            if trunkFromDB:
                service.updateUserATrunk(userid,**trunk)
                self.write(DataProtocol.getSuccessJson())
            else:
                self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR, "要修改的货车不存在"))

        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class DeleteUserTrunkHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")
    @auth
    def post(self):
        userid = self.getCurrentUser()
        licensePlate = self.get_argument("licensePlate")
        service = self.getDbService()

        if userid and licensePlate:
            trunks = service.getUserTrunks(userid)
            if trunks and len(trunks) <=1:
                self.write(DataProtocol.getJson(DataProtocol.AT_LEAST_ONE_TRUNK_ERROR,"至少保留一辆货车"))
                return

            if service.getUserTrunk(userid, licensePlate) is None:
                self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))

            ret = service.deleteUserATrunk(userid,licensePlate)
            if ret:
                self.write(DataProtocol.getSuccessJson(service.getUserTrunks(userid),"json"))
            else:
                self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))

class UseTrunkHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")
    @auth
    def post(self):
        userid = self.getCurrentUser()
        licensePlate = self.get_argument("licensePlate")
        service = self.getDbService()

        if userid and licensePlate:

            if service.getUserTrunk(userid, licensePlate) is None:
                self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))

            ret = service.setUsedTrunk(userid,licensePlate)
            if ret:
                self.write(DataProtocol.getSuccessJson(service.getUserTrunks(userid),"json"))
            else:
                self.write(DataProtocol.getJson(DataProtocol.DB_ERROR))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))

class UploadTrunkPicHandler(BaseHandler):
    def post(self):
        files = self.request.files["file"]
        # print files
        hasCleared = False
        if files and len(files)>0:
            service = self.getDbService()
            for item in files:
                img = item["body"]
                filename =item["filename"]
                print "filename", filename

                image = Image.open(StringIO.StringIO(buf=img))
                size = image.size
                type = image.format
                print "size", size
                print "type", type


                names = filename.split("_")
                licensePlate = unquote(names[0].encode("utf-8"))
                userid = names[1]

                #要保存图片之前先清除一遍。因为在修改货车的情况下编辑会重复保存
                if not hasCleared:
                    service.removeTrunkPics(userid,licensePlate)
                    hasCleared = True

                filename = licensePlate + "_" + userid + names[2]
                filepath = "/upload/trunkPic/"+filename+"."+type.lower()
                image.save(static_path + filepath)
                print names

                service.saveTrunkPic(userid,licensePlate,filepath)
            print "ok"

        self.write(DataProtocol.getSuccessJson("ok","json"))


####################### Comment Hanlder begin #######################
class CommentHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")

    @auth
    def get(self):
        userid = self.getCurrentUser()
        num = self.get_argument("num", 0)
        count = self.get_argument("count", -1)
        userType = self.get_argument("userType",None)
        mylog.getlog().info(getLogText( "get comment:userid", userid, " num", num," count",count,"userType",userType))
        service = self.getDbService()
        if userid:
            commentIds = service.getUserComments(userid,userType, int(num), int(count))
            commentDatas = [service.getCommentById(commentIds[i]) for i in xrange(len(commentIds))] if commentIds else []

            print commentIds
            print commentDatas
            for item in commentDatas:
                if "fromUserId" in item:
                    item["nickBarData"] = service.getNickBarData(item["fromUserId"])
            self.write(DataProtocol.getSuccessJson(commentDatas,"json"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"userid is invalid"))

    @auth
    def delete(self):
        commentId = self.get_argument("commentId",None)
        service = self.getDbService()
        if commentId:
            ret = service.removeComment(commentId)
            if ret:
                self.write(DataProtocol.getSuccessJson())
            else:
                self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"fail to delete a comment"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"userid is invalid"))

    @auth
    def put(self):
        commentId = self.get_argument("commentId",None)
        starNum = self.get_argument("starNum",None)
        text = self.get_argument("text",None)
        service = self.getDbService()
        if not commentId or not starNum or not text:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"arg is invalid"))
            return

        starNum = int(starNum)
        text = str(text)
        if not commentDict:
            trunkserverLog("has not the commentDict")
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"has not the commentDict"))
            return

        ret = service.updateComment(commentId,starNum,text)
        if ret:
            self.write(DataProtocol.getSuccessJson())
        else:
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"fail to update a comment"))

    @auth
    def post(self):
        if commentDict:
            params = {}
            for k in commentDict.iterkeys():
                params[k] = self.get_argument(k, None)
            service = self.getDbService()
            trunkserverLog("comment：", params)
            params["commentTime"] = str(time.time())

            if "userType" in params :
                if params["userType"] == "driver":
                    params["userType"] = "owner"
                elif params["userType"] == "owner":
                    params["userType"] = "driver"

                ret = service.addComment(**params)
                if ret:
                    self.write(DataProtocol.getSuccessJson())
                else:
                    self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"fail to add a comment"))
            else:
                self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"参数错误"))
        else:
            trunkserverLog("has not the commentDict")
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"has not the commentDict"))

    def options(self):
        self.add_header("Access-Control-Allow-Methods","POST, GET, OPTIONS,DELETE,HEAD,PATCH,PUT")
        self.add_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept,X-Requested-With")

#获取评论的一些文案
class CommentTextHandler(BaseHandler):
    def get(self):
        userType = self.get_argument("userType", None)
        if userType == "owner" or userType=="driver":
            service = self.getDbService()
            try:
                commentText = service.getConf("commentText")
                # print commentText
                self.write(DataProtocol.getSuccessJson(commentText[userType],"json"))
            except Exception, e:
                self.write(DataProtocol.getJson(DataProtocol.FILE_ERROR,"config read error"))
                trunkserverLog(DataProtocol.FILE_ERROR,"config read error",e)
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"userType must be 'owner' or 'driver'"))

#######################Comment Hanlder end #######################

class LocationHandler(BaseHandler):
    def post(self):
        latitude = self.get_argument("latitude", None)
        longitude = self.get_argument("longitude", None)
        userId = self.get_argument("userId", None)
        prov = self.get_argument("prov", None)
        city = self.get_argument("city", None)
        district = self.get_argument("district", None)
        trunkserverLog( "latitude=",latitude,"longitude=",longitude,"userId=",userId)
        if latitude and longitude and userId:
            service = self.getDbService()
            service.addLocation(userId,latitude,longitude,prov,city,district,str(time.time()))
            self.write(DataProtocol.getSuccessJson())
        else:
           self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"param error"))
           trunkserverLog("LocationHandler param error")

    # def get(self):
    #     latitude = self.get_argument("latitude", None)
    #     longitude = self.get_argument("longitude", None)
    #     userId = self.get_argument("userId", None)
    #     trunkserverLog( "latitude=",latitude,"longitude=",longitude,"userId=",userId)
    #     if latitude and longitude and userId:
    #         service = self.getDbService()
    #         service.addLocation(userId,latitude,longitude)
    #         self.write(DataProtocol.getSuccessJson())
    #     else:
    #        self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"param error"))
    #        trunkserverLog("LocationHandler param error")


#######################Page Hanlder#######################
class LoginPageHandler(BaseHandler):
    def get(self):
        userid = self.getCurrentUser()
        mark = self.getMark()
        customType = self.getCustomType()

        if userid and mark and checkMark(userid, mark,customType):
            self.redirect("/main.html")
        else:
           self.render("./dist/login.html")
        # self.render("./dist/login.html")

class MainPageHandler(BaseHandler):
    @authPage
    def get(self):
        self.render("./dist/main.html")

#######################Page Hanlder END #######################

class TestHandler(BaseHandler):
    requiredParams = {\
        "fielda":unicode\
    }

    @coroutine
    def onCall(self, *args, **kwargs):
        self.finish("you make it, server get:"+self.get_argument("fielda"))


####################### 验证码相关 BEGIN #######################

class RegCodeHandler(BaseHandler):
    def get(self):
        phonenum = self.get_argument("phonenum",None)
        #TODO 验证手机格式
        if not phonenum is None:
            #发送短信
            regcodeObject = RegCode()
            #TODO 这里可能会出错，但短信不够或者服务出错的情况，需要补充逻辑
            regcodeStr = regcodeObject.sendRegCode(phonenum)
            print regcodeStr

            service = self.getDbService()
            service.addRegCode(phonenum,regcodeStr)
            self.write(DataProtocol.getSuccessJson())
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"param error"))
            trunkserverLog("RegCodeHandler param error")

class CheckCodeHandler(BaseHandler):
    def get(self):
        phonenum = self.get_argument("phonenum",None)
        regcode = self.get_argument("regcode",None)

        service = self.getDbService()
        if not phonenum is None and not regcode is None:

            if service.hasUser(phonenum):
                self.write(DataProtocol.getJson(DataProtocol.USER_EXISTED_ERROR,"用户已经存在"))
            else:
                ret = service.checkCode(phonenum,regcode)
                self.write(DataProtocol.getSuccessJson({"ret":ret},"json"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"param error"))
            trunkserverLog("CheckCodeHandler param error")

####################### 验证码相关 END #######################

class UserCompleteDataHanlder(BaseHandler):
    @auth
    def get(self):
        userid =self.getCurrentUser()
        getType = self.get_argument("getType",None)

        service = self.getDbService()
        if userid and getType:
            data = service.getUserCompleteData(userid,getType)
            if data is None:
                 self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"数据验证失败"))
            else:
                self.write(DataProtocol.getSuccessJson(data,"json"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"userid is none or getType is none"))
            trunkserverLog("UserCompleteDataHanlder param error")

settings = {
    "debug":True,
    "login_url":"/login",
    "cookie_secret":"61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo="
}

static_path = os.path.join(os.path.dirname(__file__), "dist")

application = tornado.web.Application([
    (r"/api/admin/qlogin", QuickLoginHanlder),
    (r'/', IndexHandler),
    (r"/api/admin/login", LoginHandler),
    (r"/api/admin/register", RegisterHandler),
    (r"/api/admin/logout", LogoutHandler),
    (r"/api/bill", BillHandler),
    (r"/api/bill/get", GetUserBillsHandler),
    (r"/api/bill/send", SendBillHandler),
    (r"/api/bill/delete", DeleteBillHandler),
    (r"/api/bill/remove", RemoveBillHanlder),
    (r"/api/bill/update", UpdateBillHandler),
    (r"/api/bill/invite", InviteBillHandler),
    (r"/api/bill/conn", ConnBillHandler),
    (r"/api/bill/recomend", GetRecommendBillsHandler),
    (r"/api/bill/call", BillCallHandler),
    (r"/api/bill/visited", GetVisitedBillHandler),
    (r"/api/bill/history", GetHistoryBillHandler),
    (r"/api/bill/pick", PickBillHandler),
    (r"/api/bill/confirm", ConfirmBillReqHandler),
    (r"/api/comment", CommentHandler),
    (r"/api/comment/text", CommentTextHandler),
    (r"/api/user", UserHanlder),
    (r"/api/user/getCompleteData", UserCompleteDataHanlder),
    (r"/api/user/trunk", UserTrunkHandler),
    (r"/api/user/trunk/delete", DeleteUserTrunkHandler),
    (r"/api/user/trunk/use", UseTrunkHandler),
    (r"/api/user/trunk/uploadPic", UploadTrunkPicHandler),
    (r"/api/location", LocationHandler),
    (r"/api/regcode",RegCodeHandler),
    (r"/api/regcode/check",CheckCodeHandler),
    (r'/login.html', LoginPageHandler),
    (r'/main.html', MainPageHandler),
    (r'/test', TestHandler),
    (r'/(.*)', tornado.web.StaticFileHandler, {'path': static_path})
], **settings)

def _quit_if_ioloop_is_empty():
    ioloop = tornado.ioloop.IOLoop.instance()
    reset()

    if len(ioloop._handlers) <= len(ioloop._timeouts):
        mylog.getlog().info("No more request in progress(%d timeouts). really quiting", len(ioloop._timeouts))
        tornado.ioloop.IOLoop.instance().stop()
    else:
        mylog.getlog().info("%d more handlers pending", len(ioloop._handlers))


def gracefullyShutDown(signum, frame):

    server.stop()
    tornado.ioloop.PeriodicCallback(_quit_if_ioloop_is_empty, 500, io_loop=tornado.ioloop.IOLoop.instance()).start()


def writePid():
    print "writePid"
    fileHandle = open(os.path.join(os.path.dirname(__file__), "this.pid"),'w')
    print os.getpid()
    fileHandle.write(str(os.getpid()))
    fileHandle.close()

writePid()

if __name__ == "__main__":
    mylog.getlog().info("application start ,http://115.29.8.74:9288")
    connection = connect("mongodb://"+options.dbuser+":"+options.dbpsw+"@"+options.dbaddr+"/"+options.dbname)

    server = HTTPServer(application, xheaders=True)
    server.listen(options.port)

    minJobs = tornado.ioloop.PeriodicCallback(jobsEveryMin, 10*1000)
    minJobs.start()

    # job = tornado.ioloop.PeriodicCallback(jobsEvery5Mins, 5*60*1000)
    # job.start()

    # signal.signal(signal.SIGINT, gracefullyShutDown)
    # signal.signal(signal.SIGTERM, gracefullyShutDown)
    # signal.signal(signal.SIGQUIT, gracefullyShutDown)

    tornado.ioloop.IOLoop.instance().start()

