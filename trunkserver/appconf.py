# encoding=utf-8

__author__ = 'zhongqiling'

from tornado.gen import coroutine, Return

from models.defines import coroutineDebug
from dbmodels import Config

# AppConf = None

class AppConf(object):
    conf = None


# @coroutineDebug
# @coroutine
# def initAppConf():
#     conf = yield Config.objects().one()
#     if not conf:
#         conf = Config()
#         conf.currUse = True
#         yield conf.save()
#     global AppConf
#     AppConf = yield getConf()
#
# @coroutineDebug
# @coroutine
# def getConf():
#     conf = yield Config.objects().one()
#     if not conf:
#         conf = Config()
#         conf.currUse = True
#         yield conf.save()
#
#     raise Return(conf)

def initAppConf():
    global AppConf
    AppConf = Config()

def printConf():
    print AppConf.conf.to_client()