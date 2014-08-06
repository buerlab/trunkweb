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
    DATAPROTOCOL_ERROR = -5  # -5 ：数据封装问题
    IS_NOT_AJAX_REQUEST = -6 #非 ajax请求却请求了ajax/xxx的文件
    FILE_ERROR = -6 #文件读取失败
    AUTH_ERROR = -7
    USER_EXISTED_ERROR = -8 #用户已经存在，注册失败
    LOGIN_FAIL = -9
    AT_LEAST_ONE_TRUNK_ERROR = -20001 #只要要保存一辆货车
    # code: 0 代表成功 ，负数代表失败，-1 ~ -100 通用失败， -1000 ~ -9999 自定义错误代码
   
    # datatype include "html","json","string","nothing"
    #"nothing " is default

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
    def getJson(code, msg="have no message.", data=None, datatype="nothing"):
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
