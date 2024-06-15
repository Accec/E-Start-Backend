from logging.handlers import TimedRotatingFileHandler
import logging
import os
from pathlib import Path
import time
import re
import sys

class ReTimedRotatinFileHandler(TimedRotatingFileHandler):
    """
    时间为切割点日志
    """
    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.
        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        # prefix = baseName + "."
        # plen = len(prefix)
        for fileName in fileNames:
            # if fileName[:plen] == prefix:
            # suffix = fileName[:-4]
            if self.extMatch.match(fileName):
                 result.append(os.path.join(dirName, fileName))
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        return result
 
 
def splitFileName(filename):
    filePath = filename.split('default.log.')
    return ''.join(filePath)
 
def setupLogger(logName, logsPath, when, level):
    
    # 创建logger对象,log_name: 日志名字
    loggerObj = logging.getLogger(logName)

    # loge文件路径
    logFilePath = f"{logsPath}/default.log"
 
    # when="MIDNIGHT", interval=1,表示每天0点为更新点，每天生成一个文件
    loggerHandler = ReTimedRotatinFileHandler(filename=logFilePath, when=when, interval=1, backupCount=7, encoding='utf-8')
    # 处理日志文件名称
    loggerHandler.namer = splitFileName
 
    # 修改后缀suffix,生成.log文件
    # extMatch是编译好正则表达式，用于匹配日志文件名后缀
    # 需要注意的是suffix和extMatch一定要匹配的上，如果不匹配，过期日志不会被删除
    loggerHandler.suffix = f"{loggerHandler.suffix}.log"
    # when=S: r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(.log)$"
    # when=M: r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(.log)$"
    # when=H: r"^\d{4}-\d{2}-\d{2}_\d{2}(.log)$"
    # when=D or MIDNIGHT : r"^\d{4}-\d{2}-\d{2}(.log)$"
    # when=W: r"^\d{4}-\d{2}-\d{2}(.log)$"

    suffix = {"S": r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(.log)$",
                "M": r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(.log)$",
                "H": r"^\d{4}-\d{2}-\d{2}_\d{2}(.log)$",
                "D": r"^\d{4}-\d{2}-\d{2}(.log)$",
                "MIDNIGHT": r"^\d{4}-\d{2}-\d{2}(.log)$",
                "W": r"^\d{4}-\d{2}-\d{2}(.log)$"}

    loggerHandler.extMatch = re.compile(suffix[when], re.ASCII)
 
    # 创建日志输出格式
    logger_formatter = logging.Formatter(
        "[%(asctime)s] [%(process)d] [%(levelname)s] - %(name)s.%(module)s.%(funcName)s (%(filename)s:%(lineno)d) - %(message)s")

    streamHandler = logging.StreamHandler(sys.stdout)
 
    # 配置日志输出格式
    loggerHandler.setFormatter(logger_formatter)
    streamHandler.setFormatter(logger_formatter)
 
    # 增加日志处理器
    loggerObj.addHandler(loggerHandler)
    loggerObj.addHandler(streamHandler)
 
    # 设置日志的记录等级,常见等级有: DEBUG<INFO<WARING<ERROR
    loggerObj.setLevel(level)
 
    return loggerObj
 
 
if __name__ == "__main__":
    setupLogger("test", "backend/src/logs", "M", 2)
    n = 1
    a = logging.getLogger("test")
    while True:
        a.debug(f"this is debug message")
        a.info(f"this is info message")
        a.warning(f"this is warning message")
        a.error(f"this is error message")
        time.sleep(1)
        n += 1