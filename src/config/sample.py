from config.base import *

#环境设置
APP = "E-Starter"
DeBug = True
Pip = "pip"
RelativePath = True
UploadsPath = "uploads"
LogsPath = "logs"
JwtSecretKey = ""                   #JWT密钥, 请确保该密钥不会有泄露风险
#Sanic设置
SanicHost = "localhost"
SanicPort = 8000
#Nginx配置
ForwardedSecret = ""                #Nginx转发密钥配置, 请确保该密钥不会有泄露风险
#Mysql设置
MysqlHost = "localhost"
MysqlPort = 3306
MysqlUsername = 'root'
MysqlPassword = ''
MysqlDatabaseName = 'E-starter'
#Redis设置
RedisUrl = "redis://127.0.0.1/0"
#CORS 设置
CorsDomains = ['localhost.com']
