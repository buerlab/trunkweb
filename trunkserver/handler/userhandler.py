#encoding=utf-8
__author__ = 'zhongqiling'

from tornado.options import define, options
import time

from basehandler import *
from dbservice import DbService
from dataprotocol import DataProtocol
from utils import *


@coroutine
def getClientControl():
    config = yield Config.objects({"currUse":True}).one()
    result = {"serverTimeMills":int(time.time())*1000, "locationReportFreq":config.locationReportFreq}
    raise Return(result)


class UserRegisterHandler(BaseHandler):

    requiredParams = {
        "password":unicode,
    }

    optionalParams = {
        "username": unicode,
        "phoneNum": unicode,
        "inviteNum":unicode
    }

    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):

        username, phoneNum = self.get_argument("username", None), self.get_argument("phoneNum", None)
        inviteNum = self.get_argument("inviteNum", None)
        psw = kwargs["password"]
        if username or phoneNum:
            # sameUser = yield User.get_collection().find_one(qOr(username=username, phoneNum=phoneNum))
            sameUser = yield User.objects({"$or":[{"username":username}, {"phoneNum":phoneNum}]}).one()
            if sameUser:
                self.finish(DataProtocol.getJson(DataProtocol.USER_EXISTED_ERROR,"用户已经存在"))
            else:
                user = User(username, phoneNum, encryptPassword(psw))
                user.regtime = time.time()
                yield user.save()

                #注册完马上给个登录态
                self.set_secure_cookie("userid", str(user.id))
                self.set_secure_cookie("mark", getMark(user.id))
                self.finish(DataProtocol.getSuccessJson(user.to_client(), "json"))
        else:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class UserLoginHandler(BaseHandler):

    requiredParams = {
        "password":unicode
    }

    optionalParams = {
        "username": unicode,
        "phoneNum": unicode
    }


    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        username = self.get_argument("username", None)
        phoneNum = self.get_argument("phoneNum", None)
        psw = self.get_argument("password", None)
        userinput = username or phoneNum

        if userinput:
            encryptPsw = encryptPassword(psw)
            query = {"$or":[{"username": userinput, "psw": encryptPsw}, {"phoneNum": userinput, "psw": encryptPsw}]}
            user = yield User.objects(query).one()
            if user:
                if user.nickName:
                    self.set_cookie("nickName", user.nickName)
                elif user.username:
                    self.set_cookie("nickName", user.username)
                elif user.phoneNum:
                    self.set_cookie("nickName", user.phoneNum)

                self.set_secure_cookie("userid", str(user.id))
                self.set_secure_cookie("mark", getMark(user.id))

                userData = user.to_client()
                userData["userId"] = userData.pop("id")
                control = yield getClientControl()
                dataToClient = {"user":userData, "control":control}
                self.finish(DataProtocol.getSuccessJson(dataToClient,"json"))
            else:
                self.finish(DataProtocol.getJson(DataProtocol.LOGIN_FAIL,"手机号码或者密码错误，登录失败"))
        else:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class UserQuickLoginHandler(BaseHandler):

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        userId = self.getCurrUserId()
        user = yield User.get(self.getCurrUserId(), self.getUserType())
        userData = user.to_client()
        userData["userId"] = userData.pop("id")
        control = yield getClientControl()
        dataToClient = {"user":userData, "control":control}
        self.finish(DataProtocol.getSuccessJson(dataToClient, "json"))


class UserLogoutHandler(BaseHandler):

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        user = yield self.getUser()
        user.setAttr("JPushId", "")
        yield user.save()
        print "========USER %s LOGOUT"%self.getCurrUserId()
        self.clear_cookie("mark")
        self.clear_cookie("userid")
        self.clear_cookie("nickName")
        self.finish(DataProtocol.getSuccessJson())


class UserSettingHandler(BaseHandler):

    optionalParams = {
        "push":unicode,
        "locate":unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        user = yield User.get(self.getCurrUserId(), self.getUserType())
        if "push" in kwargs:
            value = True if kwargs["push"] == Value.True else False
            user.getAttr("Settings")["push"] = value
        if "locate" in kwargs:
            value = True if kwargs["locate"] == Value.True else False
            user.getAttr("Settings")["locate"] = value
        yield user.save()
        self.finish(DataProtocol.getSuccessJson())

class UserLocationHandler(BaseHandler):

    requiredParams = {
        "userId": unicode,
        "latitude": unicode,
        "longitude": unicode,
        "prov": unicode,
        "city": unicode,
        "district": unicode
    }

    normalLocationRecordDays = 15
    freqLocationRecordHours = 24

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        location = Location()
        location.userId = kwargs["userId"]
        location.latitude = kwargs["latitude"]
        location.longitude = kwargs["longitude"]
        location.prov = kwargs["prov"]
        location.city = kwargs["city"]
        location.district = kwargs["district"]
        location.timestamp = time.time()

        config = yield Config.shared()
        archiveCount = yield Location.objects({"userId":location.userId, "isArchived":True}).count()
        if archiveCount > 0:
            latest = yield Location.objects({"userId":location.userId, "isArchived":True}).skip(archiveCount-1).to_list(1)
            latestLocation = latest[0]
            nextArchiveTime = latestLocation.timestamp + config.locationArchIntervalHours*60*60
            lastCacheTime = location.timestamp - config.locationCacheHours*60*60
            query = {"userId":location.userId, "isArchived":False, "timestamp":{"$lt":lastCacheTime, "$gt":nextArchiveTime}}
            nextArchive = yield Location.objects(query).limit(1).to_list(1)
            if nextArchive:
                archiveLocation = nextArchive[0]
                archiveLocation.isArchived = True
                yield archiveLocation.save()

            yield Location.objects({"userId":location.userId, "isArchived":False, "timestamp":{"$lt":lastCacheTime}}).remove()

        else:
            location.isArchived = True

        yield location.save()
        self.finish(DataProtocol.getSuccessJson())


class GetUserLocationHandler(BaseHandler):

    requiredParams = {
        "getUserId":unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        getUserId = kwargs["getUserId"]
        location = yield Location.get_collection().find({"userId":getUserId}).sort([("timestamp", -1)]).limit(1).to_list(1)
        if location:
            self.write(DataProtocol.getSuccessJson(location[0], "json"))
        else:
            self.write(DataProtocol.getJson(DataProtocol.DB_ERROR,"找不到该用户的地理位置"))


class UpdateUserHandler(BaseHandler):

    optionalParams = docToParms(User)

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        print "-------------UpdateUserHandler", kwargs
        update = dict([(k, v) for k,v in kwargs.items() if k in self.optionalParams])
        print update
        yield User.objects({"id":self.getCurrUserId()}).update(**User.query_dict_to_db(update))
        self.finish(DataProtocol.getSuccessJson())



