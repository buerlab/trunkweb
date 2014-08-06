#encoding=utf-8
__author__ = 'zhongqiling'

from tornado.options import define, options
from basehandler import *
from dbservice import DbService
from dataprotocol import DataProtocol
from mylog import mylog, getLogText
from appmodels import *
from dbmodels import *
from jpush.JPushService import *
from motor import Op
from utils import *


class UserRegisterHandler(BaseHandler):

    requiredParams = {
        "password":unicode,
    }

    optionalParams = {
        "username": unicode,
        "phoneNum": unicode
    }

    @auth
    @coroutineDebug
    @coroutine
    def onCall(self, **kwargs):
        pass
