#!/usr/local/bin/python
#-*- coding:utf-8 -*-
# Author: jacky
# Time: 14-2-22 下午11:48
# Desc: 短信http接口的python代码调用示例
import httplib
import urllib
import random

#服务地址
host = "yunpian.com"
#端口号
port = 80
#版本号
version = "v1"
#查账户信息的URI
user_get_uri = "/" + version + "/user/get.json"
#通用短信接口的URI
sms_send_uri = "/" + version + "/sms/send.json"
#模板短信接口的URI
sms_tpl_send_uri = "/" + version + "/sms/tpl_send.json"



def get_user_info(apikey):
    """
    取账户信息
    """
    conn = httplib.HTTPConnection(host, port=port)
    conn.request('GET', user_get_uri + "?apikey=" + apikey)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    return response_str

def send_sms(apikey, text, mobile):
    """
    能用接口发短信
    """
    params = urllib.urlencode({'apikey': apikey, 'text': text, 'mobile':mobile})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = httplib.HTTPConnection(host, port=port, timeout=30)
    conn.request("POST", sms_send_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    return response_str

def tpl_send_sms(apikey, tpl_id, tpl_value, mobile):
    """
    模板接口发短信
    """
    params = urllib.urlencode({'apikey': apikey, 'tpl_id':tpl_id, 'tpl_value': tpl_value, 'mobile':mobile})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = httplib.HTTPConnection(host, port=port, timeout=30)
    conn.request("POST", sms_tpl_send_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    return response_str

class YunPianRegCode():
    regcodeStr = ""

    def sendRegCode(self,phonenum):
        mobile = phonenum
        apikey = "808afa76542a86e83859f2e88305851f"
        for i in range(0, 6):
            regcode = random.randint(0,9)
            self.regcodeStr = self.regcodeStr + str(regcode)

        #查账户信息
        # print(get_user_info(apikey))

        #调用通用接口发短信
        # print(send_sms(apikey, text, mobile))

        #调用模板接口发短信
        tpl_id = 5
        tpl_value = '#code#='+self.regcodeStr+'&#company#=天天回程车&#app#=天天回程车'
        print(tpl_send_sms(apikey, tpl_id, tpl_value, mobile))
        return self.regcodeStr

class YunPianMsgAfterCalled():
    def send(self,phonenum,url,_type):
        apikey = "e0254da93c76329fd30aef158b242e41"
        mobile = phonenum
        #调用模板接口发短信
        tpl_id = 448957
        # print _type
        # print type(_type)
        tpl_value = '#url#='+url +"&#type#=" + _type
        print "tpl_value", tpl_value
        print(tpl_send_sms(apikey, tpl_id, tpl_value, mobile))

class YunPianMsgMatch():
    def send(self,phonenum,url,nickname,_from,_to,_type):
        apikey = "808afa76542a86e83859f2e88305851f"
        mobile = phonenum
        #调用模板接口发短信
        tpl_id = 447571 
        tpl_value = '#url#='+url + "&#nickname#=" + nickname + "&#from#=" + _from + "&#to#=" + _to + "&#type#=" + _type
        print(tpl_send_sms(apikey, tpl_id, tpl_value, mobile))

#发送短信
# regcodeObject = YunPianRegCode()
# #TODO 这里可能会出错，当短信不够或者服务出错的情况，需要补充逻辑
# regcodeStr = regcodeObject.sendRegCode("15810070528")
# print "regcodeStr",regcodeStr                            
