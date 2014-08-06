#encoding=utf-8
__author__ = 'zhongqiling'

import tornado.ioloop
import tornado.web
from tornado.gen import coroutine, Future

import re
from dbservice import *
from dataprotocol import *
import md5
import time
from datetime import datetime, timedelta


#打log 并加上DbServiceLog前缀
def trunkserverLog(*arg):
    prefix = tuple(["trunkserver:"])
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
    "jpushId":"",

    "regtime":"13898394849",
    "bills":[],
    "userType":"driver/owner",
    "stars":4,

    "driverBills": [],
    "ownerBills": [],

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


def encryptPassword(psw):
    return md5.new("hello"+ psw + "world").hexdigest()


def getMark(userid):
    return md5.new("buerlab"+ str(userid)).hexdigest() +"time:"+str(time.time())


def checkMark(userid,mark, customer = None):
    if not userid or not mark:
        return False

    markArray = mark.split("time:")
    if len(markArray)<1:
        return False

    delta = timedelta(days=30)

    #客户端默认30天，web保留7天
    if customer == "web":
        delta = timedelta(days=7)

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
        userid = self.getCurrentUser()

        mark = self.getMark()
        customType = self.getCustomType()
        mylog.getlog().info(getLogText("get connect userid:", userid, "mark:", mark))

        if userid and mark and checkMark(userid, mark,customType):
            return func(self, *args, **kwargs)
        self.write(DataProtocol.getJson(DataProtocol.AUTH_ERROR,"AUTH_ERROR"))
        self.finish()
        return None

    return check


def authPage(func):
    def check(self, *args, **kwargs):
        userid = self.getCurrentUser()
        mylog.getlog().info(getLogText("get connect userid:", userid))
        mark = self.getMark()
        customType = self.getCustomType()
        print "authPage"
        print userid,mark
        if userid and mark and checkMark(userid, mark,customType):
            return func(self, *args, **kwargs)
        self.redirect("/login.html")
        return None

    return check


def addAllowOriginHeader(func):
    def retFuc(self, *args, **kwargs):
        # self.add_header("Access-Control-Allow-Origin","*")
        # mylog.getlog().info(getLogText( "add_header"))
        return func(self, *args, **kwargs)

    return retFuc


class BaseHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")

    requiredParams = {}
    optionalParams = {}

    valueValidater = re.compile(r"[\x00-\x08\x0e-\x1f]")

    def getCurrentUser(self):
        # return self.get_secure_cookie("userid")
        return self.get_argument("userId", None)

    def getUserType(self):
        return self.get_argument("userType", None)

    def getBillType(self):
        if self.getUserType() == UserType.DRIVER:
            return BillType.TRUNK
        elif self.getUserType() == UserType.OWNER:
            return BillType.GOODS
        return ""

    def getMark(self):
        return self.get_secure_cookie("mark")

    def getCustomType(self):
        return self.get_argument("customType", None)

    def getDbService(self):
        service = DbService().connect()

        if not service:
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"db connect error"))
            trunkserverLog(DataProtocol.DB_ERROR,"db connect error")
        return service

    def options(self):
        self.add_header("Access-Control-Allow-Methods","POST, GET, OPTIONS,DELETE,HEAD,PATCH,PUT")
        self.add_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept,X-Requested-With")

    def formatValue(self, v):
        v = self.decode_argument(v)
        if isinstance(v, unicode):
            # Get rid of any weird control chars (unless decoding gave
            # us bytes, in which case leave it alone)
            v = re.sub(self.valueValidater, " ", v)
            v = v.strip()
        return v

    def typeCheck(self, data, typeMaps, mandatory=True):
        for k, v in typeMaps.items():
            if not k in data:
                if mandatory:
                    return False
                else:
                    continue
            # k is present in data
            try:
                data[k] = v(data[k]) if data[k] is not None else None
            except Exception as e:
                if data[k] == "None":
                    data[k] = None
                else:
                    raise e
        return True

    def validateParams(self, params):
        try:
            return self.typeCheck(params, self.requiredParams, True) and\
                   self.typeCheck(params, self.optionalParams, False)
        except Exception:
            return False

    @coroutine
    def dispatch(self):
        try:
            kwargs = {}
            for k, v in self.request.arguments.iteritems():
                kwargs[k] = self.formatValue(v[-1])

            if self.validateParams(kwargs):
                try:
                    ret = self.onCall(**kwargs)
                    if isinstance(ret, Future):
                        yield ret
                except (TypeError, KeyError) as e:
                    self.finish(DataProtocol.getJson(DataProtocol.DATAPROTOCOL_ERROR, e.message))
                except Exception, e:
                    pass
            else:
                self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
        except Exception, e:
            self.finish("exception caught!!")

    @coroutine
    def get(self, *args, **kwargs):
        yield self.dispatch()

    @coroutine
    def post(self, *args, **kwargs):
        yield self.dispatch()

    def onCall(self, *args, **kwargs):
        self.finish("Under construction.")
