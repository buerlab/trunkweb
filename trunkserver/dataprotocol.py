#coding=utf-8 
#此文件用于指定后台返回前台的协议

# 返回包封装类

import json
from bson import json_util

class DataProtocol(object):

    SUCCESS = 0
    ARGUMENT_ERROR = -1 #参数错误
    DB_ERROR = -2      #数据库访问错误
    DB_DUPLICATE_ERROR = -3 # 数据重复
    
    IS_NOT_AJAX_REQUEST = -4 #非 ajax请求却请求了ajax/xxx的文件
    DATAPROTOCOL_ERROR = -5  # -5 ：数据封装问题
    FILE_ERROR = -6 #文件读取失败
    AUTH_ERROR = -7
    USER_EXISTED_ERROR = -8 #用户已经存在，注册失败
    LOGIN_FAIL = -9
    SERVER_ERROR = -10

    PERMISSION_DENY = -11 #没有权限
    
    AT_LEAST_ONE_TRUNK_ERROR = -20001 #只要要保存一辆货车
    BILL_REMOVED = -30001  #bill已经被删除
    BILL_NOT_OWN = -30002   #用户不用有该bill
    BILL_NOT_WAIT = -30003   #bill不再有效期
    USER_INVALID = -30004  #请求中用户不存在或者不是有效的对象(管理员)

    ALREADY_COMMENTED = -40001 #已经评论过了
    CANNOT_SELF_COMMENT = -40002 #不能给自己评论呢
    MESSAGE_DUPLICATE_ERROR = -50001 #重复添加message
    # code: 0 代表成功 ，负数代表失败，-1 ~ -100 通用失败， -1000 ~ -9999 自定义错误代码

   
    # datatype include "html","json","string","nothing"
    #"nothing " is default

    #MSG
    COMMON_MSG = "服务器繁忙，请稍后再试"
    ARGUMENT_ERROR_MSG ="请求失败，请重试"
    DB_ERROR = "服务器繁忙，请稍后再试"
    IS_NOT_AJAX_REQUEST_MSG="非法请求，请用正常方式请求"
    AT_LEAST_ONE_TRUNK_ERROR_MSG = "至少要保存一辆货车"
    ALREADY_COMMENTED_MSG = "已经评论过了"
    CANNOT_SELF_COMMENT_MSG = "不能给自己评论"
    BILL_REMOVED_MSG = "订单已经被删除"

    #什么都不判断直接输出return，不保证数据正确，只能被getJson()调用
    @staticmethod
    def _wrapJson(code, msg, data, datatype="nothing"):
        retDict = {
            "code":code,
            "msg":msg,
            "data":data,
            "datatype":datatype
            }
        return json.dumps(retDict,default=json_util.default)
         

    @staticmethod
    def _wrapError(msg="数据封装错误"):        
        return DataProtocol._wrapJson(DataProtocol.DATAPROTOCOL_ERROR, msg,"","nothing")

    @staticmethod
    def getJson(code, msg="", data=None, datatype="nothing"):
        retJson = None
        if not isinstance(code,int):
            try:
                code = int(code)
            except:
                retJson = DataProtocol._wrapError("code is not int")

        if not isinstance(msg, str):
            try:
                msg = str(msg)
            except:
                retJson = DataProtocol._wrapError("msg is not string")

        if not isinstance(datatype, str):
            try:
                datatypeTmp = str(datatype)
            except:
                retJson = DataProtocol._wrapError("datatype is not string")
            else:
                if datatype == "string" or datatype == "json" or datatype == "html":
                    if not isinstance(data, str):
                        try:
                            dataTmpStr = str(data)
                        except:
                            retJson = DataProtocol._wrapError("datatype said is "+ datatype+ " but data is "+ str(type(data)))
                        else:
                            data = dataTmpStr
                elif datatype == "nothing":
                    pass
                else:
                    retJson = DataProtocol._wrapError("unknown datatype")

        if msg == "":
            if code == DataProtocol.ARGUMENT_ERROR:
                msg = DataProtocol.ARGUMENT_ERROR_MSG
            elif code ==DataProtocol.DB_ERROR:
                msg = DataProtocol.DB_ERROR_MSG
            elif code ==DataProtocol.IS_NOT_AJAX_REQUEST:
                msg = DataProtocol.IS_NOT_AJAX_REQUEST_MSG
            elif code ==DataProtocol.AT_LEAST_ONE_TRUNK_ERROR:
                msg = DataProtocol.AT_LEAST_ONE_TRUNK_ERROR_MSG
            elif code ==DataProtocol.ALREADY_COMMENTED:
                msg = DataProtocol.ALREADY_COMMENTED_MSG
            elif code ==DataProtocol.CANNOT_SELF_COMMENT:
                msg = DataProtocol.CANNOT_SELF_COMMENT_MSG
            else:
                msg = DataProtocol.COMMON_MSG

        # print "----------getJson",code,msg,data,datatype
        if not retJson is None:
            return retJson
        else:       
            return DataProtocol._wrapJson(code,msg,data,datatype);

    @staticmethod
    def getSuccessJson(data=None,datatype="nothing"):
        return DataProtocol.getJson(0,"success",data, datatype)

#单元测试-_-
#if __name__ == "__main__":
#     print r"DataProtocol.getSuccessJson(\"hello, world\",\"string\")", DataProtocol.getSuccessJson("hello, world","string")
#     print r"DataProtocol.getSuccessJson(\"hello, world\",\"(123,123)\")", DataProtocol.getSuccessJson("hello, world","(123,123)")
#     print r"DataProtocol.getSuccessJson(1,2)", DataProtocol.getSuccessJson(1,2)
#     print DataProtocol.getJson("0","success")
#     print DataProtocol.getJson(0,"success")
#     print DataProtocol.getJson("o","success")
#     print DataProtocol.getJson(0,"success",data={"a":1},datatype="json")
#     print DataProtocol.getJson(0,"success",data=(1,2,3),datatype="json")
#     print DataProtocol.getJson("-4",(123,123),data=(1,2,3),datatype="json")
#     print DataProtocol.getJson(5,None,None,None)
