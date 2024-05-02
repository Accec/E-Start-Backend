import os
from pathlib import PurePosixPath
import importlib


from scheduler import tasks

import models

from tortoise.contrib.sanic import register_tortoise


import config


Config = config.Config()

def create_app(server):
    TortoiseConfig = {
            'connections': {
                'default': {
                    'engine': 'tortoise.backends.mysql',
                    'credentials': {
                            'host': Config.MysqlHost,
                            'port': Config.MysqlPort,
                            'user': Config.MysqlUsername,
                            'password': Config.MysqlPassword,
                            'database': Config.MysqlDatabaseName,
                        "maxsize":"15",
                        "minsize":"5"
                    }
                },
            },
            'apps': {
                'e-starter': {
                    'models': ["models"],
                    'default_connection': 'default',
                }
            },
            'use_tz': True,
        }

    cwd = os.getcwd().replace('\\','/')

    if Config.RelativePath == True:
        Config.UploadsPath = f"{cwd}/{Config.UploadsPath}"
        Config.LogsPath = f"{cwd}/{Config.LogsPath}"

    
    os.environ['LOG_PATH'] = Config.LogsPath
    server.config.SERVER_NAME = f"{Config.SanicHost}:{Config.SanicPort}"
    server.config.CORS_ORIGINS = ";".join(Config.CorsDomains)
    server.config.LOGGING = True
    

    register_tortoise(
            server, config = TortoiseConfig,
            generate_schemas=True
        )

    return server

def load_task():
    #获取tasks路径
    tasks_dir = os.path.dirname(os.path.abspath(tasks.__file__))
    #遍历tasks文件夹下面的所有task文件夹
    for task_dir in os.listdir(tasks_dir):
        #获取tasks路径下的task路径
        task_dir = os.path.join(tasks_dir, task_dir)
        task_dir = PurePosixPath(task_dir)
        #确认该task路径不以__开头并且是文件夹
        if os.path.isdir(task_dir.as_posix()) and task_dir.stem.startswith("__") == False:
            #遍历task文件夹下面的所有文件夹
            for task in os.listdir(task_dir):
                print (f"[Task] - [{task_dir.stem}] is loaded")
                #importlib.import_module(f"scheduler.tasks.{task_dir.stem}.task.py")

def _get_models():
    #定义一个空列表用来储存model的包名
    model_list = []
    #获取models路径
    models_dir = os.path.dirname(os.path.abspath(models.__file__))
    #遍历models文件夹下面的所有model文件夹
    for model in os.listdir(models_dir):
        #获取models路径下的model路径
        model = os.path.join(models_dir, model)
        model = PurePosixPath(model)
        #为了兼容性所以采用这种方式进行获取model的命名
        model_name = os.path.basename(model.as_posix())
        model_name = model_name.replace(".py", "")
        #确认model文件不以__开头
        if os.path.isfile(model.as_posix()) and model_name.startswith("__") == False:
            print (f"[Model] - [{model_name}] is loaded")
            model_list.append(f"models.{model_name}")

    return model_list