__author__ = 'zhongqiling'

class Value(object):
    True = "1"
    False = "0"

    @classmethod
    def fromBoolean(cls, value):
        return cls.True if value else cls.False

class BillType(object):
    GOODS = "goods"
    TRUNK = "trunk"


class BillState(object):
    WAIT = "wait"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    DONE = "done"

class UserLevel(object):
    NORMAL = "normal"
    WECHAT = "wechat"
    MANAGER = "manager"

class UserType(object):
    DRIVER = "driver"
    OWNER = "owner"

class PendingReqState(object):
    WAITING = "wait"
    PUSHED = "pushed"
    FINISHED = "finished"

class RequestType(object):
    Bill = "bill"
    HistoryBill = "historybill"

class HistoryBillType(object):
    GOODS = "goods"
    TRUNK = "trunk"
    USER = "user"


class SettingType(object):
    JPush = "jpush"
    Locate = "locate"


class RecomendBillType(object):
    GOODS = "goods"
    TRUNK = "trunk"
    LOCAL = "local_trunk"


def createRecommendBill(userdata, bill, recBillType):
    return {"user":userdata, "bill":bill, "type":recBillType}


def matchBillType(usertype):
    if usertype == UserType.DRIVER:
        return BillType.TRUNK
    elif usertype == UserType.OWNER:
        return BillType.GOODS
    return ""

def matchUserType(billtype):
    if billtype == BillType.GOODS:
        return UserType.OWNER
    elif billtype == BillType.TRUNK:
        return UserType.DRIVER
    return ""

def oppsiteUserType(usertype):
    return UserType.OWNER if usertype == UserType.DRIVER else UserType.DRIVER

def oppsiteBillType(billtype):
    billtypes = [BillType.GOODS, BillType.TRUNK]
    try:
        return billtypes[1-billtypes.index(billtype)]
    except Exception, e:
        return ""