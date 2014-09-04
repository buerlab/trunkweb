#encoding=utf-8

from dbservice import DbService
from dataprotocol import DataProtocol
from mylog import mylog,getLogText
from bson.objectid import ObjectId
import os
import  random
from  jpush.RegCodeService import RegCode
import md5
import calendar
from datetime import datetime

service = DbService().connect()

def getAllUser(): 
	for item in service.mongo.trunkDb.userCol.find({}):
		print item

def getUser(username): 
    for item in service.mongo.trunkDb.userCol.find({"username":username}):
        print item

def getUserById(id):
    for item in service.mongo.trunkDb.userCol.find({"_id":ObjectId(id)}):
        print item

def getUserByPhoneNum(phoneNum): 
    for item in service.mongo.trunkDb.userCol.find({"phoneNum":phoneNum}):
        print item

def getAllComments(): 
    for item in service.mongo.trunkDb.commentCol.find({}):
        print item


def deleteAllComments():
    service.mongo.trunkDb.commentCol.remove()



def removeUserComments(userid):
    user = service.mongo.trunkDb.userCol.find_one({"_id":ObjectId(userid)})
    if user:
        user["driverComments"] = []
        user["driverStars"] = 0
        user["ownerComments"] = []
        user["ownerStars"] = 0
        # update stars
        service.mongo.trunkDb.userCol.update({"_id":ObjectId(userid)}, user)  

def setIDNumVerify():
    service.mongo.trunkDb.userCol.update({"phoneNum":"111111"},{"$set":{"IDNumVerified":"0"}})

def deleteUser(phoneNum):
    service.mongo.trunkDb.userCol.remove({"phoneNum":phoneNum})

def deleteUserById(userid):
    service.mongo.trunkDb.userCol.remove({"_id":ObjectId(userid)})


def getAllLocation():
    for item in service.mongo.trunkDb.LocationCol.find():
        print item


# getAllLocation()
# service.getLastLocation("53c4b2407938ee1089520738")
# deleteUser("15507507400")
# print service.getLocation("53c4b2407938ee1089520738")

# deleteUserById("53ae236b7938ee4ce851148b")
# setIDNumVerify()
# print service.getIDNumVerifyingUsers()     
######################




# commentDict = {
#     "starNum":0, #0,1,2,3
#     "text":"吴师傅活不错",
#     "commentTime":"138545564554",
#     "fromUserName":"李小姐",
#     "fromUserId":"ObjectId()",
#     "billId":"ObjectId()",
#     "isDeleted":False
# }

# trunk = {
#     "isUsed":False,
#     "licensePlate":"粤B1",
#     "type":"高栏车",
#     "length":1,
#     "load":12,
#     "trunkLicense":"1230021992",
#     "trunkLicenseVerified":"0", #0 未审核 1 审核中 2 审核通过 3 审核失败
#     "trunkLicensePicFilePath":"123123.jpg",
#     "trunkPicFilePaths":["123123.jpg","123123.jpg","123123.jpg"]
# }
# print service.addUserATrunk("53ae236b7938ee4ce851148b", **trunk)
# trunk = {
#     "isUsed":False,
#     "licensePlate":"粤B2",
#     "type":"高栏车",
#     "length":1,
#     "load":12,
#     "trunkLicense":"1230021992",
#     "trunkLicenseVerified":"0", #0 未审核 1 审核中 2 审核通过 3 审核失败
#     "trunkLicensePicFilePath":"123123.jpg",
#     "trunkPicFilePaths":["123123.jpg","123123.jpg","123123.jpg"]
# }
# print service.addUserATrunk("53ae236b7938ee4ce851148b", **trunk)
# trunk = {
#     "isUsed":False,
#     "licensePlate":"粤B3",
#     "type":"高栏车",
#     "length":1,
#     "load":12,
#     "trunkLicense":"1230021992",
#     "trunkLicenseVerified":"1", #0 未审核 1 审核中 2 审核通过 3 审核失败
#     "trunkLicensePicFilePath":"123123.jpg",
#     "trunkPicFilePaths":["123123.jpg","123123.jpg","123123.jpg"]
# }
# print service.addUserATrunk("53ae236b7938ee4ce851148b", **trunk)
# trunk = {
#     "isUsed":False,
#     "licensePlate":"粤B4",
#     "type":"高栏车",
#     "length":1,
#     "load":12,
#     "trunkLicense":"1230021992",
#     "trunkLicenseVerified":"1", #0 未审核 1 审核中 2 审核通过 3 审核失败
#     "trunkLicensePicFilePath":"123123.jpg",
#     "trunkPicFilePaths":["123123.jpg","123123.jpg","123123.jpg"]
# }
# print service.addUserATrunk("53bf6fea7938ee7b8c169380", **trunk)


# service.deleteUserATrunk("53ae236b7938ee4ce851148b","粤B2")
# service.setUsedTrunk("53ae236b7938ee4ce851148b", "粤B2")
# print service.getUserTrunks("53ae236b7938ee4ce851148b")
# getAllUser()
# service.deleteUserATrunk("53ae236b7938ee4ce851148b","粤B444444")
# getUserByPhoneNum("111111")


# service.saveTrunkPic("53b3edc17938ee2fc2882b3a","6666","123.jpg")
# getUserById("53b3edc17938ee2fc2882b3a")
# print service.getTrunkLicenseVerifyingUsers()
# service.failTrunkLicenseVerifying("53ae236b7938ee4ce851148b", "粤B3")
# print service.getTrunkLicenseVerifyingUsers()
# service.addComment(**{
#     "starNum":1, #0,1,2,3
#     "text":"吴师傅活不错2",
#     "commentTime":"138542564554",
#     "fromUserName":"aaaa",
#     "fromUserId":"539fe7b97938ee399731c692",
#     "toUserId":"53ae236b7938ee4ce851148b",
#     "billId":"5399818a7938ee399731c688"
#     })

# service.addComment(**{
#     "starNum":3, #0,1,2,3
#     "text":"吴师傅态度很好",
#     "commentTime":"138545584554",
#     "fromUserName":"aaaa",
#     "fromUserId":"539fe7b97938ee399731c692",
#     "toUserId":"53ae236b7938ee4ce851148b",
#     "billId":"5399818a7938ee399731c688"
#     })

# service.addComment(**{
#     "starNum":3, #0,1,2,3
#     "text":"吴师傅态度很好",
#     "commentTime":"138545584554",
#     "fromUserName":"aaaa",
#     "fromUserId":"539fe7b97938ee399731c692",
#     "toUserId":"53ae236b7938ee4ce851148b",
#     "billId":"5399818a7938ee399731c688"
#     })

# service.addComment(**{
#     "starNum":3, #0,1,2,3
#     "text":"吴师傅态度很好",
#     "commentTime":"138545584554",
#     "fromUserName":"aaaa",
#     "fromUserId":"539fe7b97938ee399731c692",
#     "toUserId":"53b663f27938ee6c041f14e3",
#     "billId":"5399818a7938ee399731c688"
#     })
#
# service.addComment(**{
#     "starNum":3, #0,1,2,3
#     "userType":"driver",
#     "text":"感谢tod的帮忙！太给力了@@",
#     "commentTime":"138545584554",
#     "fromUserName":"teddy",
#     "fromUserId":"53c38b347938ee65f08ef387",
#     "toUserId":"53c4e3937938ee38e9fb00e4",
#     "billId":"5399818a7938ee399731c688"
#     })
# getAllUser()
# service.removeComment("53b4de6e15a5e41d7f37fffb") #TODO
# removeUserComments("53b663f27938ee6c041f14e3")
# getUserByPhoneNum("88") #53b4c4347938ee141a02dc7b
# service.updateComment("539feb3115a5e46403c16448",1,"better")

# getUserById("53b663f27938ee6c041f14e3")
# getUser("aaaa")  # id 539fe7b97938ee399731c692 bill 5399818a7938ee399731c688
# getUser("bbbb")  # id 539fe7de7938ee399731c693 bill 5399826c7938ee399731c68a
# deleteAllComments()
# removeUserComments("539aae917938ee399731c68f")
# getAllComments()

# print service.getCommentById("539ab03c15a5e4461c9cf23b")

# print service.getUserComments("53ae236b7938ee4ce851148b",0,-1)

# for item in service.mongo.trunkDb.LocationCol.find({}):
#     print item

# regcodeStr = ""
# for i in range(0, 6):
#     regcode = random.randint(0,9)
#     regcodeStr = regcodeStr + str(regcode)
#
# print regcodeStr

# service.addRegCode("15507507400","123456")
# for item in service.mongo.trunkDb.regcodeCol.find({}):
#     print item
# # getAllUser()
#
# print service.checkCode("15507507400","075419")

# a = RegCode()
# print service.addUser("123", "123", "123")
# print a.sendRegCode("18503003832")
# deleteUser("123")
# deleteUser("15507507401")
# deleteUser("15507507402")
# deleteUser("15507507403")
# deleteUser("15507507408")
#
# getAllUser()
# getUserByPhoneNum("13417473149")

# getUserByPhoneNum("15811804083")
# deleteAllComments()
# print service.getUserComments("53bd6d1d7938ee71fc2bb408","driver",0,-1)
#
# commentIds = service.getUserComments("53bd6d1d7938ee71fc2bb408","driver",0,-1)
#
# commentDatas = [service.getCommentById(commentIds[i]) for i in xrange(len(commentIds))] if commentIds else []
# print commentDatas

# removeUserComments("53bd6d1d7938ee71fc2bb408")

# print service.getUserCompleteData("53bd75427938ee7ae66ed34f","driver")

# print getUserById("53c38b347938ee65f08ef387")
#
# t = {
#     "isUsed":True,
#     "licensePlate":"如题",
#     "type":"高栏车",
#     "length":1,
#     "load":12,
#     "trunkLicense":"1230021992",
#     "trunkLicenseVerified":"1", #0 未审核 1 审核中 2 审核通过 3 审核失败
#     "trunkLicensePicFilePath":"123123.jpg",
#     "trunkPicFilePaths":["123123.jpg","123123.jpg","123123.jpg"]
# }
#
# print  service.updateUserATrunk("53c38b347938ee65f08ef387",**t)

# service.addFeedback("53c38b347938ee65f08ef387","hello")
# print service.getFeedback()

# print service.getUserTrunk("53c38b347938ee65f08ef387","搞糊涂")

# print service.setUsedTrunk("53c38b347938ee65f08ef387","搞糊涂")

# service.setPushSettings("53bd74417938ee7ae66ed34e","owner",False)
# print getUserById("53bd74417938ee7ae66ed34e")
# getUserByPhoneNum("12345678900") #53bd74417938ee7ae66ed34e

# getUserByPhoneNum("15507507411")
# print service.getUserTrunks("53bd6bd07938ee71fc2bb407")

# print service.getUserBaseData("53bd6bd07938ee71fc2bb407")

# service.updateUser("53bd6bd07938ee71fc2bb407",**{"IDNumVerified":"0"})

# def encryptPassword(psw):
#     return md5.new("hello"+ psw + "world").hexdigest()

# service.addUser("admin", "12345678900", encryptPassword("hust430074"))  #id = 53e9cd5915a5e45c43813d1c

# service.doneToAddMessage("53ec7a307938ee66168e266f")
# print service.mongo.trunkDb.toAddMessage.find_one({"_id":ObjectId("53ec7a307938ee66168e266f")})


# print service.getSummaryStat("day",None,None,"teddywu",None)

# print service.getRegionSummaryStat("day",None,None,None,"prov",None)

# for item in service.mongo.trunkDb.toAddMessageCol.find():
#     id = item["_id"]
#     time = item["time"]
#     time_d = int(time)
#     item["time"] = time_d
#     service.mongo.trunkDb.toAddMessageCol.update({"_id":ObjectId(id)},item)
# print len(service.getToAddStat("wait",0,None,None,None,None))

# print service.getToAddMessage(None,"teddywu")

# print service.getIDNumVerifyingUsers()

# print service.getAdmin("teddywu8")

# content = "车讯：深圳回广州7米6箱式车 电联18502088009"
# condition = {}
# a = datetime.now()
# a = a.replace(a.year,a.month,a.day,0,0,0)
# ts = calendar.timegm(a.utctimetuple())
# condition["time"] = {}
# condition["time"]["$gt"] = ts * 1000
# condition["state"] = {
#     "$in" : ["wait", "editing"]
# } 
# condition["content"] = content
# condition["_id"] = ObjectId("5401d1e57938ee2dcad60cad")
# service.mongo.trunkDb.toAddMessageCol.update(condition,{"$set": {"state":"ignore"} })
# for i in service.mongo.trunkDb.toAddMessageCol.find(condition):
#     service.mongo.trunkDb.toAddMessageCol.update(condition,{"$set": {"state":"wait"} })

for item in service.mongo.trunkDb.addedMessageCol.find({"editor":"teddywu","state":"refuse"}):
    print item