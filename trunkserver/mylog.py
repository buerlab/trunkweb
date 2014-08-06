#coding=utf-8 

import logging
import datetime
import sys,os
#用法
#mylog.info("hello,world")
#CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET

def cur_file_dir():
    #获取脚本路径
    path = sys.path[0]
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)

class Logger(object):
    
    def __init__(self):
        self.logger = self.createLogger()

    def createLogger(self):
        # 创建一个logger
        name = 'trunkserver'
        logger = logging.getLogger(name)

        logger.setLevel(logging.DEBUG)

        self.datetime = datetime.datetime.now().strftime('%y-%m-%d')

        # 创建一个handler，用于写入日志文件
        fh = logging.FileHandler(cur_file_dir()+"/log/" + name + "-" + self.datetime+".log")
        fh.setLevel(logging.DEBUG)


        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 给logger添加handler
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger
    
    def getlog(self):
        if self.logger is None:
            self.logger = self.createLogger()
        else:
            if datetime.datetime.now().strftime('%y-%m-%d') != self.datetime:
                self.logger = self.createLogger()
        return self.logger

    def getLogText(*arg):
        text = ""
        for item in arg:
            if type(item) == unicode:
                item = item.encode('utf-8')
            text = text + str(item)
            text = text + " "
        return text
    getLogText  =  staticmethod(getLogText)

    # def info(self,*arg):
    #     self.getlog().info(self._getText(arg))

    # def error(self,*arg):
    #     self.getlog().error(self._getText(arg))

    # def debug(self,*arg):
    #     self.getlog().debug(self._getText(arg))

    # def critical(self,*arg):
    #     self.getlog().critical(self._getText(arg)) 

    # def warning(self,*arg):
    #     self.getlog().warning(self._getText(arg))  

mylog = Logger()
getLogText = Logger.getLogText

# a ={"a":1}
# mylog.info("a",a)
# mylog.error("a",a)
# mylog.debug("a",a)
# mylog.critical("a",a)

# mylog.info(getLogText("a",a))

# print getLogText("examname",u"司法考试")
# print type(u"司法考试")
