# encoding=utf-8
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
from tornado.options import  define, options
import signal

from handler.billhandler import *
from handler.userhandler import *
from dataprotocol import *
from dbservice import *
from mylog import mylog, getLogText
from urllib import unquote
import StringIO
import os
from jobs import *
from models import connect
import time
from  jpush.RegCodeService import RegCode
from appconf import AppConf, printConf

try:
    from PIL import Image
except:
    raise EnvironmentError('Must have the PIL (Python Imaging Library).')

define("dburi", default="mongodb://root:430074@localhost:16888/admin", type=str)
define("dbaddr", default="localhost:16888", type=str)
define("dbuser", default="zql", type=str)
define("dbpsw", default="fine", type=str)
define("dbname", default="trunkDb", type=str)
# define("dburi", default="mongodb://localhost:27017", type=str)
define("port", default=80, type=int)
define("billDueMins", default=1, type=int)
define("historyReturnPieces", default=5, type=int)

define("locationValidDay", default=10, type=int)
define("locationArchDays", default=10, type=int)
define("locationArchIntervalHours", default=2, type=int)
define("locationCacheHours", default=10, type=int)
define("locationInterval", default=4, type=int)

#推荐单子每次请求返回的最大数量
define("recomendBillReturnOnce", default=20, type=int)

# define("inviteOnceBonus", default=10, type=int)


#每次数据库查找返回的文档最大数量
define("findMaxReturn", default=1000, type=int)



class IndexHandler(BaseHandler):
    def get(self):
        self.render("./dist/index.html")


#######################Page Hanlder#######################
class LoginPageHandler(BaseHandler):
    def get(self):
        userid = self.getCurrUserId()
        mark = self.getMark()
        customType = self.getCustomType()

        if userid and mark and checkMark(userid, mark,customType):
            self.redirect("/main.html")
        else:
           self.render("./dist/login.html")
        # self.render("./dist/login.html")

class MainPageHandler(BaseHandler):
    @authPage
    def get(self):
        self.render("./dist/main.html")

class RestHandler(BaseHandler):
    def get(self,param):

        if os.path.exists(static_path + self.request.path):
            self.render(static_path + self.request.path)
        else:
            self.write_error(404)

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render('./dist/404.html')
        else:
            self.write('error:' + str(status_code))


class AppDownloadHandler(BaseHandler):
    def get(self,param):
        self.set_header("Content-Type","application/octet-stream")
        with open("dist/app/"+param, "r") as f:
            self.write(f.read())

settings = {
    "login_url":"/login",
    "cookie_secret":"61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo="
}

rel_static_path = "dist"

static_path = os.path.join(os.path.dirname(__file__), "dist")

application = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/login.html', LoginPageHandler),
    (r'/main.html', MainPageHandler),
    (r'/app/(.*)', AppDownloadHandler),
    (r'/images/(.*)', tornado.web.StaticFileHandler, {'path': static_path +"/images"}),
    (r'/scripts/(.*)', tornado.web.StaticFileHandler, {'path': static_path +"/scripts"}),
    (r'/styles/(.*)', tornado.web.StaticFileHandler, {'path': static_path + "/styles"}),
    (r'/(.*)', RestHandler)
], **settings)

def _quit_if_ioloop_is_empty():
    ioloop = tornado.ioloop.IOLoop.instance()
    reset()

    if len(ioloop._handlers) <= len(ioloop._timeouts):
        mylog.getlog().info("No more request in progress(%d timeouts). really quiting", len(ioloop._timeouts))
        tornado.ioloop.IOLoop.instance().stop()
    else:
        mylog.getlog().info("%d more handlers pending", len(ioloop._handlers))


def gracefullyShutDown(signum, frame):

    server.stop()
    tornado.ioloop.PeriodicCallback(_quit_if_ioloop_is_empty, 500, io_loop=tornado.ioloop.IOLoop.instance()).start()


def writePid():
    print "writePid"
    fileHandle = open(os.path.join(os.path.dirname(__file__), "this.pid"),'w')
    print os.getpid()
    fileHandle.write(str(os.getpid()))
    fileHandle.close()

@coroutineDebug
@coroutine
def initAppConf():
    conf = yield Config.objects().one()
    if not conf:
        conf = Config()
        conf.currUse = True
        yield conf.save()

    AppConf.conf = conf

writePid()

if __name__ == "__main__":
    mylog.getlog().info("application start ,http://115.29.8.74")
    connection = connect("mongodb://"+options.dbuser+":"+options.dbpsw+"@"+options.dbaddr+"/"+options.dbname)

    server = HTTPServer(application, xheaders=True)
    server.listen(options.port)


    tornado.ioloop.IOLoop.instance().start()

