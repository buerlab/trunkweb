__author__ = 'zhongqiling'


class BillType(object):
    GOODS = "goods"
    TRUNK = "trunk"


class BillState(object):
    WAIT = "wait"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    DONE = "done"


class UserType(object):
    DRIVER = "driver"
    OWNER = "owner"


class PendingReqState(object):
    WAITING = "wait"
    PUSHED = "pushed"
    FINISHED = "finished"

class HistoryBillType(object):
    GOODS = "goods"
    TRUNK = "trunk"
    USER = "user"

def getBillTypeOfUser(usertype):
    if usertype == UserType.DRIVER:
        return BillType.TRUNK
    elif usertype == UserType.OWNER:
        return BillType.GOODS
    return ""
