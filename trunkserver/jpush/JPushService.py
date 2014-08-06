#encoding=utf-8
import urllib, urllib2
import base64, json

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

def createAlias(userid, usertype):
    return userid+str(usertype)


class JPushProtocal(object):
    PHONE_CALL = 1
    BILL_VISITED = 2


def createprotocol(protType, msg=""):
    return {"code":protType, "msg":msg}

def createBillReqMsg(senderName, reqId):
    data = {"senderName":senderName, "reqId":reqId}
    return createprotocol(JPushProtocal.PHONE_CALL, data)

def JPushNotifyAll(alert, msg={}):
    parms = {
        "platform":"all",
        "audience":"all",
        "notification":{
            "alert":alert,
            "extras":msg
        }
    }
    JPush(parms)

def JPushNotifyToId(id, alert):
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
    JPush(parms)


def JPushNotifyToAlias(alias, alert, msg={}):
    parms = {
        "platform":"all",
        "audience":{
            "alias":[alias]
        },
        "notification":{
            "alert":alert,
            "title":"天天回程车",
            "extras":msg
        },
        "message":{
            "msg_content":msg
        }
    }
    JPush(parms)


def JPushMsgAll(msg):
    parms = {
        "platform":"all",
        "audience":"all",
        "message":{
            "msg_content":msg
        }
    }
    JPush(parms)


def JPushMsgTo(alias, msg):
    parms = {
        "platform":"all",
        "audience":{
            "alias":[alias]
        },
        "message":{
            "msg_content":msg
        }
    }
    JPush(parms)


def JPushMsgToId(id, msg):
    parms = {
        "platform":"all",
        "audience":{
            "registration_id":[id]
        },
        "message":{
            "msg_content":msg
        }
    }
    JPush(parms)
    print "push:  ", json.dumps(parms)


def JPush(parms):
    data = json.dumps(parms)

    authStr = "c6561ed88743cb91d34b8572:24728d0cf947c98489876097"
    b64AuthStr = base64.b64encode(authStr)

    req = urllib2.Request("https://api.jpush.cn/v3/push", data)
    req.add_header("Content-type", "application/json")
    req.add_header("Authorization", "Basic "+b64AuthStr)
    resp = urllib2.urlopen(req)
    print "JPUSH RESPONSE:",resp.read()


