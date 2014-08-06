#coding=utf-8 

import tornado.ioloop
import tornado.web
from data_protocol import DataProtocol
import os

sett = {
    "id":5
}
dotoList = [
    {
        "completed": False,
        "title":"123",
        "id":1
    },{
        "completed": True,
        "title":"abc",
        "id":2
    },{
        "completed": True,
        "title":"hello",
        "id":3
    }
]

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("./dist/index.html")  

class TodosHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")
    def initialize(self,):
        pass

    def get(self):
        print "get"
        self.add_header("Access-Control-Allow-Origin","*")
        print dotoList
        self.write(DataProtocol.getSuccessJson(dotoList,"json"))

    def post(self):
        print "post"
        self.add_header("Access-Control-Allow-Origin","*")
        title = self.get_argument("title",None)
        completed = self.get_body_argument("completed",None)

        dotoList.append({
            "title":title,
            "completed":completed,
            "id":sett["id"]
            })
        sett["id"] = sett["id"]+1
        self.write(DataProtocol.getSuccessJson(dotoList,"json"))

    def put(self):
        print "put"
        self.add_header("Access-Control-Allow-Origin","*")
        self.write(DataProtocol.getSuccessJson(dotoList,"json"))

    def delete(self):
        print "delete"
        self.add_header("Access-Control-Allow-Origin","*")
        self.write(DataProtocol.getSuccessJson(dotoList,"json"))

    def options(self):
        self.add_header("Access-Control-Allow-Origin","*")
        self.add_header("Access-Control-Allow-Methods","POST, GET, OPTIONS,DELETE,HEAD,PATCH,PUT")
        self.add_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept,X-Requested-With")

class TodoHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ("GET", "HEAD", "POST", r"DELETE", "PATCH", "PUT", "OPTIONS")
    def get(self,id):
        print "get",id
        self.add_header("Access-Control-Allow-Origin","*")
        ret = None
        for item in dotoList:
            if str(item["id"]) == id:
                ret = item

        self.write(DataProtocol.getSuccessJson(ret,"json"))

    def post(self,id):
        print "post",id
        self.add_header("Access-Control-Allow-Origin","*")

        dotoList.append({
            "title":title,
            "completed":bool(completed)
            })
        self.write(DataProtocol.getSuccessJson())

    def put(self,id):
        print "put",id,self.get_argument("title",None),self.get_argument("completed",None)
        self.add_header("Access-Control-Allow-Origin","*")

        completed = self.get_argument("completed",None)
        if completed == "true":
            completed = True
        else:
            completed = False
        
        for item in dotoList:
            if str(item["id"]) == id:
                item["title"] = self.get_argument("title",None)
                item["completed"] = completed

        print dotoList
        self.write(DataProtocol.getSuccessJson())

    def delete(self,id):
        print "delete",id
        self.add_header("Access-Control-Allow-Origin","*")
        for item in dotoList:
            if str(item["id"]) == id:
                dotoList.remove(item)
        self.write(DataProtocol.getSuccessJson())

    def options(self,id):
        self.add_header("Access-Control-Allow-Origin","*")
        self.add_header("Access-Control-Allow-Methods","POST, GET, OPTIONS,DELETE,HEAD,PATCH,PUT")
        self.add_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept,X-Requested-With")

settings = {
    "cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    "xsrf_cookies":False
}

static_path = os.path.join(os.path.dirname(__file__), "dist")
application = tornado.web.Application([
    (r"/", MainHandler),
    (r'/(.*)', tornado.web.StaticFileHandler, {'path': static_path})
    ],**settings)

def writePid():
    print "writePid"
    fileHandle = open(os.path.join(os.path.dirname(__file__), "this.pid"),'w')
    print os.getpid()
    fileHandle.write(str(os.getpid()))
    fileHandle.close()    

writePid()

if __name__ == "__main__":
    application.listen(8888)
    print "listen to localhost:8888"
    tornado.ioloop.IOLoop.instance().start()
    writePid()