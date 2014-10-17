#encoding=utf-8

from appmodels import *
import urllib, urllib2
import base64, json
import sys

notificationDict = {
    "alert":"",
    "title":"",
    "builder_id":0,
    "extras":{}
}

messageDict = {
    "msg_content":"",
    "title":"",
    "Content-type":"",
    "extras":{}
}

canJPush = True
JPushCurrAuth = ""
JPushOwnerAuth = "cee61b3f886124cfba3dca69:269fa6630d8ce960aa8085b8"
JPushDriverAuth = "925cbe63935b3fdde4541b89:d97c3582a59e913464b7e4a5"

def createAlias(userid, usertype):
    return userid+str(usertype)


class JPushProtocal(object):
    PHONE_CALL = 1
    BILL_VISITED = 2
    BILL_CONFIRM = 3
    HISTORY_BILL_CONFIRM = 4
    HISTORY_BILL_REQ = 5
    RECOMMEND_BILL = 6
    GET_MATCH_BILL = 7

def createNotification(alert, title="天天回程车"):
    return {"notification":{"alert":alert,"title":title}}

#userid是指要发送对象的userid， 客户端要校验才会接受
def createprotocol(userId, protType, msg=""):
    return {"code":protType, "userId":userId, "msg":msg}

def createBillReqMsg(userId, senderName, reqId):
    data = {"senderName":senderName, "reqId":reqId}
    return createprotocol(userId, JPushProtocal.PHONE_CALL, data)

def createHistoryBillReqMsg(userId, senderName, reqId, billId):
    data = {"senderName":senderName, "reqId":reqId, "billId":billId}
    return createprotocol(userId, JPushProtocal.HISTORY_BILL_REQ, data)

def createBillConfirmMsg(userId, senderName, billId):
    data = {"senderName":senderName, "billId":billId}
    return createprotocol(userId, JPushProtocal.BILL_CONFIRM, data)

def createHistoryBillConfirmMsg(userId, senderName, billId):
    data = {"senderName":senderName, "historyBillId":billId}
    return createprotocol(userId, JPushProtocal.HISTORY_BILL_CONFIRM, data)

def createRecomendBillMsg(userId, bill):
    data = {"bill": bill}
    return createprotocol(userId, JPushProtocal.RECOMMEND_BILL, data)

def createGetMatchBillMsg(userId):
    return createprotocol(userId, JPushProtocal.GET_MATCH_BILL)


def JPushNotifyAll(alert, msg={}, toUserType = ""):
    parms = {
        "platform":"all",
        "audience":"all",
        "notification":{
            "alert":alert,
            "extras":msg
        }
    }
    JPush(parms, toUserType)

def JPushNotifyToId(id, alert, toUserType = ""):
    parms = {
        "platform":"all",
        "audience":{
            "registration_id":[id]
        },
        "notification":{
            "alert":alert,
            "title":"天天回程车"
        }
    }
    JPush(parms, toUserType)


def JPushNotifyToAlias(alias, alert, msg={}, toUserType = ""):
    parms = {
        "platform":"all",
        "audience":{
            "alias":[alias]
        },
        "notification":{
            "alert":alert,
            "title":"天天回程车"
        },
        "message":{
            "msg_content":msg
        }
    }
    JPush(parms, toUserType)


def JPushMsgAll(msg, toUserType = ""):
    parms = {
        "platform":"all",
        "audience":"all",
        "message":{
            "msg_content":msg
        }
    }
    JPush(parms, toUserType)


def JPushMsgTo(alias, msg, toUserType = ""):
    parms = {
        "platform":"all",
        "audience":{
            "alias":[alias]
        },
        "message":{
            "msg_content":msg
        }
    }
    JPush(parms, toUserType)


def JPushMsgToId(id, msg, toUserType = ""):
    parms = {
        "platform":"all",
        "audience":{
            "registration_id":[id]
        },
        "message":{
            "msg_content":msg
        }
    }
    JPush(parms, toUserType)


def JPushToId(id, notification=None, msg=None, toUserType=""):
    parms = {
        "platform":"all",
        "audience":{
            "registration_id":[id]
        }
    }
    if notification:
        parms.update(notification)
    if msg:
        parms.update({"message":{"msg_content":msg}})
    JPush(parms, toUserType)

def initPush(toUsertype):
    global JPushCurrAuth
    JPushCurrAuth = JPushDriverAuth if toUsertype == UserType.DRIVER else JPushOwnerAuth

#务必指明userType，决定推送的authkey
def JPush(parms, toUserType = ""):
    data = json.dumps(parms)
    authId = ""
    if toUserType == UserType.DRIVER:
        authId = JPushDriverAuth
    elif toUserType == UserType.OWNER:
        authId = JPushOwnerAuth
    elif JPushCurrAuth:
        authId = JPushCurrAuth

    if authId:
        b64AuthStr = base64.b64encode(authId)
        try:
            req = urllib2.Request("https://api.jpush.cn/v3/push", data)
            req.add_header("Content-type", "application/json")
            req.add_header("Authorization", "Basic "+b64AuthStr)
            resp = urllib2.urlopen(req)
            print "JPUSH RESPONSE:",resp.read()
        except Exception, e:
            print "****jpush error caught****", e.message
            exc_type, exc_value, traceback = sys.exc_info()
            sys.excepthook(exc_type, exc_value, traceback)
            print "***********"
    else:
        raise Exception("JPUSH HASN'T INIT")


