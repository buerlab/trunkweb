scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/dataprotocol.py root@115.29.8.74:/root/trunkserver/dataprotocol.py
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/dbservice.py root@115.29.8.74:/root/trunkserver/dbservice.py
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin.py root@115.29.8.74:/root/trunkserver/admin.py
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/server.py root@115.29.8.74:/root/trunkserver/server.py
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/web_server.py root@115.29.8.74:/root/trunkserver/web_server.py
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/billmatchcontroller.py root@115.29.8.74:/root/trunkserver/billmatchcontroller.py

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/dbdata.py root@115.29.8.74:/root/trunkserver/dbdata.py
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/mylog.py root@115.29.8.74:/root/trunkserver/mylog.py
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/handler root@115.29.8.74:/root/trunkserver/

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/dbmodels.py root@115.29.8.74:/root/trunkserver/
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/jobs.py root@115.29.8.74:/root/trunkserver/
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/unittest.py root@115.29.8.74:/root/trunkserver/

#scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/restart.sh root@115.29.8.74:/root/trunkserver/restart.sh
# scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/restart_admin.sh root@115.29.8.74:/root/trunkserver/restart_admin.sh

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/handler root@115.29.8.74:/root/trunkserver/
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/jpush root@115.29.8.74:/root/trunkserver/
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/models root@115.29.8.74:/root/trunkserver/

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/config.json root@115.29.8.74:/root/trunkserver/config.json


#admin 相关
scp -r ~/Documents/codes/retrunk/trunkadmin/trunkserver/admin_dist  ~/Documents/codes/retrunk/trunkserver/

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/scripts/addInfo.js root@115.29.8.74:/root/trunkserver/admin_dist/scripts/addInfo.js
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/addInfo.html root@115.29.8.74:/root/trunkserver/admin_dist/addInfo.html

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/scripts/confirmInfo.js root@115.29.8.74:/root/trunkserver/admin_dist/scripts/confirmInfo.js
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/confirmInfo.html root@115.29.8.74:/root/trunkserver/admin_dist/confirmInfo.html
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/styles/confirmInfo.css root@115.29.8.74:/root/trunkserver/admin_dist/styles/confirmInfo.css

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/scripts/seeInfo.js root@115.29.8.74:/root/trunkserver/admin_dist/scripts/seeInfo.js
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/seeInfo.html root@115.29.8.74:/root/trunkserver/admin_dist/seeInfo.html

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/scripts/match.js root@115.29.8.74:/root/trunkserver/admin_dist/scripts/match.js
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/match.html root@115.29.8.74:/root/trunkserver/admin_dist/match.html
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/styles/match.css root@115.29.8.74:/root/trunkserver/admin_dist/styles/match.css

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/scripts/me.js root@115.29.8.74:/root/trunkserver/admin_dist/scripts/me.js
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/me.html root@115.29.8.74:/root/trunkserver/admin_dist/me.html
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/styles/me.css root@115.29.8.74:/root/trunkserver/admin_dist/styles/me.css

scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/scripts/regular.js root@115.29.8.74:/root/trunkserver/admin_dist/scripts/regular.js
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/regular.html root@115.29.8.74:/root/trunkserver/admin_dist/regular.html
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/styles/regular.css root@115.29.8.74:/root/trunkserver/admin_dist/styles/regular.css


scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist root@115.29.8.74:/root/trunkserver

#反向admin
scp -r ~/Documents/codes/retrunk/trunkserver ~/Documents/codes/retrunk/trunkadmin/

# web 相关
scp -r ~/Documents/codes/retrunk/trunkweb/backend/dist  ~/Documents/codes/retrunk/trunkserver/
scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/dist root@115.29.8.74:/root/trunkserver

#发布 app
scp -P 11000 /Users/teddywu/Documents/codes/retrunk/trunkapp/out/production/trunkdriver/trunkdriver.apk root@115.29.8.74:/root/trunkserver/dist/app
scp -P 11000 /Users/teddywu/Documents/codes/retrunk/trunkapp/out/production/trunkowner/trunkowner.apk root@115.29.8.74:/root/trunkserver/dist/app





#scp -P 11000 -r /Users/teddywu/Documents/codes/retrunk/trunkserver/dist/ root@115.29.8.74:/root/trunkserver/

# scp -P 11000 -r root@115.29.8.74:/root/trunkserver/admin_dist/secret


scp -P 11000 -r ~/Documents/codes/retrunk/trunkserver/admin_dist/scripts/seeInfo.js root@115.29.8.74:/root/trunkserver/admin_dist/scripts/seeInfo.js