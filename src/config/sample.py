from config.base import *

#环境设置
APP = "e-starter"
DeBug = True
UploadsPath = "uploads"
LogsPath = "backend/src/logs"
JwtSecretKey = ""
#Sanic设置
SanicHost = "localhost"
SanicPort = 8000
#Nginx配置
ForwardedSecret = ""
#Mysql设置
MysqlHost = "localhost"
MysqlPort = 3306
MysqlUsername = 'root'
MysqlPassword = ''
MysqlDatabaseName = 'E-Starter'
#Redis设置
RedisUrl = "redis://127.0.0.1/0"
#CORS 设置
CorsDomains = ['localhost.com']