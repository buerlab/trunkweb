#encoding=utf-8
import urllib, urllib2
import base64, json
import random



class RegCode():
    regcodeStr = ""

    def getUrl(self,phonenum):
        url1 = "http://api.sms.cn/mt/?encode=utf8&uid=buerlab&pwd=254d923c79e9ff6550fd97f001787388&mobile="
        url2 = "&content=您的验证码是："
        url3 = "，有效期为10分钟，如非本人操作，可不用理会。【天天回程车】"

        self.regcodeStr = ""
        for i in range(0, 6):
            regcode = random.randint(0,9)
            self.regcodeStr = self.regcodeStr + str(regcode)

        ret = url1+ phonenum + url2 + self.regcodeStr +url3

        return ret


    def sendRegCode(self,phonenum):

        req = urllib2.Request(self.getUrl(phonenum))
        resp = urllib2.urlopen(req)
        #TODO 这里可能会出错，但短信不够或者服务出错的情况，需要补充逻辑

        print "RegCode RESPONSE:",resp.read()
        return self.regcodeStr



