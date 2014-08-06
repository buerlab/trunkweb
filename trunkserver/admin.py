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
import os
from urllib import unquote
try:
    from PIL import Image
except:
    raise EnvironmentError('Must have the PIL (Python Imaging Library).')

#打log 并加上DbServiceLog前缀
def adminLog(*arg):
    prefix = tuple(["admin:"])
    arg = prefix + arg
    mylog.getlog().info(getLogText(arg))

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

    delta = timedelta(days=1)
    print "userid",userid
    print "mark",mark
    print "markArray",markArray

    markTime = datetime.utcfromtimestamp(float(markArray[1]))
    today = datetime.utcfromtimestamp(time.time())

    if markTime + delta < today:
        # 已经超过期限
        return False

    print "getMark(userid)", getMark(userid)
    if getMark(userid).split("time:")[0] == markArray[0]:
        return True 
    else:
        return False


def auth(func):
    def check(self, *args, **kwargs):
        username = self.getCurrentUser()
        
        mark = self.getMark()
        mylog.getlog().info(getLogText("get connect username:", username, "mark:", mark))

        if username and mark and checkMark(username, mark):
            return func(self, *args, **kwargs)

        self.clear_cookie("mark")
        self.clear_cookie("username")
        self.write(DataProtocol.getJson(DataProtocol.AUTH_ERROR,"AUTH_ERROR"))
        self.finish()
        return None
        
    return check

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


class BaseHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")
    def getCurrentUser(self):
        return self.get_secure_cookie("username")

    def getMark(self):
        return self.get_secure_cookie("mark")

    def getDbService(self):
        service = DbService().connect()
        
        if not service:
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"db connect error"))
            adminLog(DataProtocol.DB_ERROR,"db connect error")
        return service

    def options(self):
        self.add_header("Access-Control-Allow-Methods","POST, GET, OPTIONS,DELETE,HEAD,PATCH,PUT")
        self.add_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept,X-Requested-With")

class LoginHandler(BaseHandler):
    def post(self):
        userinput = self.get_argument("username", None)
        psw = self.get_argument("password", None)
        service = self.getDbService()
        #valid cookie or username and password can login
        if userinput and psw:
            username = service.confirmAdmin(userinput, encryptPassword(psw))
            print 'self.get_cookie("username")', self.get_cookie("username")

            if username:

                self.set_secure_cookie("username", str(username))
                self.set_secure_cookie("mark", getMark(username))
                print str(username)
                print getMark(username)
                self.write(DataProtocol.getSuccessJson())
            else:
                self.write(DataProtocol.getJson(DataProtocol.AUTH_ERROR))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class LogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("mark")
        self.clear_cookie("username")
        self.write(DataProtocol.getSuccessJson())

class RegisterHandler(BaseHandler):
    def post(self):
        username = self.get_argument("username", None)
        psw = self.get_argument("password", None)

        if username and psw:
            service = self.getDbService()

            # self.set_secure_cookie("mark", getmark(user))

            if not service.hasAdmin(username):
                print "register new admin:", username
                service.addAdmin(username, encryptPassword(psw))
                self.write(DataProtocol.getSuccessJson("ok","json"))
            else:
                self.write(DataProtocol.getJson(DataProtocol.USER_EXISTED_ERROR,"管理员已经存在"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR,"missing username or password"))

#######################Page Hanlder#######################
class LoginPageHandler(BaseHandler):
    def get(self):
        username = self.getCurrentUser()
        mark = self.getMark()
        if username and mark and checkMark(username, mark):
            self.redirect("/")
        else:
           self.render(rel_static_path+"/login.html")


class LoginVerifyHander(BaseHandler):
    @authPage
    def get(self):
        self.render(rel_static_path+self.request.path)

class LoginVerifyWithRegexHander(BaseHandler):
    @authPage
    def get(self,param):
        self.render(rel_static_path+self.request.path)

class IndexHandler(BaseHandler):
    def get(self):
        self.render(rel_static_path+"/index.html")

class MainPageHandler(BaseHandler):
    @authPage
    def get(self):
        self.render(rel_static_path+"/main.html")

class UploadIDNumHandler(BaseHandler):
    def post(self):
        img = self.request.files["file"][0]["body"]
        filename = self.request.files['file'][0]["filename"]
        print "filename",filename

        image = Image.open(StringIO.StringIO(buf=img))
        size = image.size
        type = image.format
        print "size",size
        print "type",type
        filepath = "/secret/IDNumPic/"+filename+"_" + str(int(time.time()) ) + "."+type.lower()
        image.save(static_path +filepath)
        userid = filename.split("_")[1]
        print userid
        service = self.getDbService()
        service.updateUser(userid,**dict({"IDNumPicFilePath":filepath}))
        print "ok"
        self.write(DataProtocol.getSuccessJson("ok","json"))

class UploadDriverLicenseHandler(BaseHandler):
    def post(self):
        img = self.request.files["file"][0]["body"]
        filename = self.request.files['file'][0]["filename"]
        print "filename",filename

        image = Image.open(StringIO.StringIO(buf=img))
        size = image.size
        type = image.format
        print "size",size
        print "type",type

        filepath = "/secret/driverLicensePic/"+filename+"_" + str(int(time.time()) ) +"."+type.lower()
        image.save(static_path +filepath)
        userid = filename.split("_")[1]
        print userid
        service = self.getDbService()
        service.updateUser(userid,**dict({"driverLicensePicFilePath":filepath}))
        print "ok"
        self.write(DataProtocol.getSuccessJson("ok","json"))

class UploadTrunkLicenseHandler(BaseHandler):
    def post(self):
        img = self.request.files["file"][0]["body"]
        filename = self.request.files['file'][0]["filename"]
        print "filename", filename

        image = Image.open(StringIO.StringIO(buf=img))
        size = image.size
        type = image.format


        filepath = "/secret/trunkLicensePic/"+filename+"_" + str(int(time.time()) ) +"."+type.lower()
        image.save(static_path + filepath)
        names = filename.split("_")
        userid = names[1]
        licensePlate = unquote(names[0].encode("utf-8"))
        print names
        service = self.getDbService()
        service.saveTrunkLicensePic(userid,licensePlate,filepath)
        print "ok"
        self.write(DataProtocol.getSuccessJson("ok","json"))


class VerifyIDNumHandler(BaseHandler):
    @auth
    def get(self):
        service = self.getDbService()
        usrs = service.getIDNumVerifyingUsers()
        print usrs
        self.write(DataProtocol.getSuccessJson(usrs,"json"))

    @auth
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
    @auth
    def get(self):
        service = self.getDbService()
        usrs = service.getDriverLicenseVerifyingUsers()
        self.write(DataProtocol.getSuccessJson(usrs,"json"))

    @auth
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
    @auth
    def get(self):
        service = self.getDbService()
        usrs = service.getTrunkLicenseVerifyingUsers()
        self.write(DataProtocol.getSuccessJson(usrs,"json"))

    @auth
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
    @auth
    def get(self):
        service = self.getDbService()
        data = service.getFeedback()
        self.write(DataProtocol.getSuccessJson(data,"json"))


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
    (r"/api/verifyDriverLicense", VerifyDriverLicenseHandler),
    (r"/api/verifyIDNum", VerifyIDNumHandler),
    (r"/api/verifyTrunkLicense", VerifyTrunkLicenseHandler),
    (r'/', IndexHandler),
    (r'/login.html', LoginPageHandler),
    (r'/main.html', MainPageHandler),
    (r"/verifyDriverLicense.html",LoginVerifyHander),
    (r"/verifyIDNum.html",LoginVerifyHander),
    (r"/verifyTrunkLicense.html",LoginVerifyHander),
    
    (r"/upload/IDNum",UploadIDNumHandler),
    (r"/upload/trunkLicense",UploadTrunkLicenseHandler),
    (r"/upload/driverLicense",UploadDriverLicenseHandler),

    (r"/userFeedback",UserFeedbackHandler),
    (r"/secret/(.*)",LoginVerifyWithRegexHander),
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

