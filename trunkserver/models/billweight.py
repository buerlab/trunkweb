#encoding=utf-8

__author__ = 'zhongqiling'

from defines import *
from dbmodels import *

config = None


def evalBillMatchWeight(historyBills, bill):
    for userBill in historyBills:
        if userBill.fromAddr == bill.fromAddr and userBill.toAddr == bill.toAddr:
            return 1000000
    return 0


def evalLocationWeight(user, bill):
    if user.homeLocation == bill.fromAddr:
        return config.homeLocationWeight
    return 0

def evalHistoryWeight(user, bill):
    return 0


def evalTimeWeight(user, bill):
    return 0





