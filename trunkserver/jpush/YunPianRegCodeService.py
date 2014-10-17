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
    params = urllib.urlencode({'apikey': apikey, 'tpl_id':tpl_id, 'tpl_value': tpl_value.encode("utf-8"), 'mobile':mobile})
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

class YunPianFindPasswordCode():
    regcodeStr = ""

    def sendRegCode(self,phonenum):
        mobile = phonenum
        apikey = "e0254da93c76329fd30aef158b242e41"
        for i in range(0, 6):
            regcode = random.randint(0,9)
            self.regcodeStr = self.regcodeStr + str(regcode)

        #调用模板接口发短信
        tpl_id = 7
        tpl_value = '#code#='+self.regcodeStr+'&#company#=天天回程车'
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
    def send(self,sendTo,phonenum,usertype,nickname,_from,_to,comment):
        apikey = "808afa76542a86e83859f2e88305851f"
        mobile = sendTo
        #调用模板接口发短信
        tpl_id = 447579

        if usertype == "owner":
            url = u'http://t.cn/RhlRVXa QQ群:215785844'  #http://www.tthcc.cn/msg_app.html?type=owner  货主版app
            _type = u"货车。"+"("+ comment+")"
        else:
            url = u'http://t.cn/RhlRIzD QQ群:215785844' #http://www.tthcc.cn/msg_app.html?type=driver  司机版app
            _type = u"货物。"+"("+comment+")"

        tpl_value = '#phonenum#='+ phonenum +'&#url#='+url + "&#nickname#=" + nickname + "&#from#=" + _from + "&#to#=" + _to + "&#type#=" + _type
        
        print "tpl_value",tpl_value
        print(tpl_send_sms(apikey, tpl_id, tpl_value, mobile))

class YunPianMsgMatch2():
    def send(self,sendTo,usertype,nickname,_from,_to,comment):
        apikey = "808afa76542a86e83859f2e88305851f"
        mobile = sendTo
        #调用模板接口发短信
        tpl_id = 495099

        if usertype == "owner":
            _type = u"货车。"+"("+ comment+")"
        else:
            _type = u"货物。"+"("+comment+")"

        method = u"请添加微信号：tthcc2014 或加入官方QQ群：215785844"
        tpl_value =  '#method#='+method + "&#nickname#=" + nickname + "&#from#=" + _from + "&#to#=" + _to + "&#type#=" + _type
        
        print "tpl_value",tpl_value
        print(tpl_send_sms(apikey, tpl_id, tpl_value, mobile))


class YunPianQunfa():
    def send(self,sendTo):
        apikey = "e0254da93c76329fd30aef158b242e41"
        mobile = sendTo
        #调用模板接口发短信
        tpl_id = 495227

        name = u"http://t.cn/RhkSOXW"
        tpl_value =  '#name#='+ name
        
        print "tpl_value",tpl_value
        print(tpl_send_sms(apikey, tpl_id, tpl_value, mobile))

class YunPianQunfaDriver():
    def send(self,sendTo):
        apikey = "e0254da93c76329fd30aef158b242e41"
        mobile = sendTo
        #调用模板接口发短信
        tpl_id = 499417

        name = u"http://t.cn/R77NQQb "
        tpl_value =  '#name#='+ name
        
        print "tpl_value",tpl_value
        print(tpl_send_sms(apikey, tpl_id, tpl_value, mobile))

class YunPianQunfaDriver2():
    def send(self,sendTo):
        apikey = "e0254da93c76329fd30aef158b242e41"
        mobile = sendTo
        #调用模板接口发短信
        tpl_id = 498135

        name = u"http://t.cn/R7P4xgh"
        tpl_value =  '#name#='+ name
        
        print "tpl_value",tpl_value
        print(tpl_send_sms(apikey, tpl_id, tpl_value, mobile))


#发送短信
# regcodeObject = YunPianMsgMatch2()
# # #TODO 这里可能会出错，当短信不够或者服务出错的情况，需要补充逻辑
# regcodeStr = regcodeObject.send(u"15507507400","owner",u"泰迪",u"广州",u"深圳",u"广深有货啊~~")
# # print "regcodeStr",regcodeStr                            

# regcodeObject = YunPianQunfa()
# regcodeStr = regcodeObject.send(u"15507507400")
# print "regcodeStr",regcodeStr  

# regcodeObject = YunPianQunfaDriver()
# regcodeStr = regcodeObject.send(u"15507507400")
# print "regcodeStr",regcodeStr