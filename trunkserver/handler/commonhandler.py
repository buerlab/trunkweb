#encoding=utf-8

__author__ = 'zhongqiling'

from basehandler import BaseHandler, addAllowOriginHeader
from tornado.gen import coroutine, Return
from models.defines import coroutineDebug
from basehandler import auth
from dbmodels import Regular
from dataprotocol import DataProtocol
import json

def createRoute(fromAddr, toAddr, prob):
    return {"fromAddr":fromAddr, "toAddr":toAddr, "probability":prob}

def validateRoute(route):
    try:
        return route["fromAddr"] and route["toAddr"] and route["probability"]

    except Exception, e:
        print "validate route error", e.message
        return False


class RegularHandler(BaseHandler):

    requiredParams = {
        "nickName": unicode,
        "phoneNum": unicode,
        "userType": unicode,
        "editor":unicode,
        "time":unicode,
        "role":unicode
    }

    optionalParams = {
        "routes": unicode,
        "comment": unicode,
        "qqgroupid": unicode,
        "qqgroup": unicode,

        "trunkType": unicode,
        "trunkLoad":unicode
    }

    # @auth
    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):

        print "kwargs",kwargs
        regular = Regular()

        regular.nickName = kwargs["nickName"]
        regular.phoneNum = kwargs["phoneNum"]
        regular.userType = kwargs["userType"]
        regular.editor = kwargs["editor"]
        regular.role = kwargs["role"]

        if "comment" in kwargs:
            regular.comment = kwargs["comment"]

        if "qqgroupid" in kwargs:
            regular.qqgroupid = kwargs["qqgroupid"]

        if "qqgroup" in kwargs:
            regular.qqgroup = kwargs["qqgroup"]
        
        if "trunkType" in kwargs:
            regular.trunkType = kwargs["trunkType"]

        if "trunkLoad" in kwargs:    
            regular.trunkLoad = kwargs["trunkLoad"]

        try:
            regular.time = int(kwargs["time"])
        except Exception, e:
            print "RegularHandler",e
            pass

        if (yield Regular.objects({"nickName":regular.nickName, "phoneNum":regular.phoneNum}).count()) > 0:
            self.finish(DataProtocol.getJson(DataProtocol.ALREADY_EXIST))
            raise Return()

        try:
            routes = json.loads(kwargs["routes"])
            regular.routes = [route for route in routes if validateRoute(route)]
        except Exception, e:
            pass

        yield regular.save()
        self.finish(DataProtocol.getSuccessJson())

class AddRouteHandler(BaseHandler):

    requiredParams = {
        "id":unicode,
        "route":unicode
    }

    # @auth
    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        regular = yield Regular.get(kwargs["id"])
        print kwargs["route"]
        try:
            route = json.loads(kwargs["route"])
        except Exception, e:
            print "JSON ERROR", e.message
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))
            return
        if regular and validateRoute(route):
            regular.routes.append(route)
            yield regular.save()
            self.finish(DataProtocol.getSuccessJson())
            return
        self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))


class GetRegularHandler(BaseHandler):

    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        result = yield Regular.objects().to_list(1000)
        self.finish(DataProtocol.getSuccessJson([item.to_client() for item in result]))


class RemoveRegularHandler(BaseHandler):
    requiredParams = {
        "id":unicode
    }

    # @auth
    @coroutineDebug
    @coroutine
    @addAllowOriginHeader
    def onCall(self, **kwargs):
        result = yield Regular.objects({"id":kwargs["id"]}).remove()
        if result:
            self.finish(DataProtocol.getSuccessJson())
        else:
            self.finish(DataProtocol.getJson(DataProtocol.ARGUMENT_ERROR))

