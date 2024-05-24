import asyncio
import traceback
import logging
from functools import wraps
from utils.redis_conn import RedisClient
from redis import asyncio as aioredis
import uuid
import ujson
import os
from pathlib import PurePosixPath
from scheduler import tasks, jobs
import importlib
import threading
from utils.constant import SCHEDULER_LOGGER
import time

class Scheduler:
    _instance = None

    def __new__(cls, redis_conn: RedisClient=None):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init(redis_conn)
        return cls._instance

    def _init(self, redis_conn: RedisClient=None):
        self.logger = logging.getLogger(SCHEDULER_LOGGER)
        self.logger.info("Scheduler is working now...")
        self.jobs = []
        self.tasks = {}
        self.redis_conn:aioredis.StrictRedis = redis_conn

        self.semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent tasks

        self._job_identifier = uuid.uuid1().__str__()

        self._job_key = 'job:{}:{}'

        self._job_status_pending = 0
        self._job_status_running = 1

        self._job_expire = 300

        self._task_queue_key = 'task:queue'
        self._task_key = 'task:{}'

        self._status_key = 'status'
        self._result_key = 'result'
        self._identifier = 'identifier'
        self._interval = 'interval'
        self._status = 'status'

        self._task_status_error = -1
        self._task_status_pending = 0
        self._task_status_working = 1
        self._task_status_done = 2

        self._task_expire = 300

        self._factory = {}

        self.shutdown_flag = False
        
    @property
    def logging(self) -> logging.Logger:
        return self.logger
    
    def run_by_thread(self):
        thread = threading.Thread(target=self.init)
        thread.start()

    def init(self):
        self.init_loop()
        self.load_tasks()
        self.load_jobs()
        self.start_jobs()
    
    def init_loop(self):
        self.asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.asyncio_loop)

    def load_tasks(self):
        tasks_dir = os.path.dirname(os.path.abspath(tasks.__file__))
        for task_dir in os.listdir(tasks_dir):
            task_dir = os.path.join(tasks_dir, task_dir)
            task_dir = PurePosixPath(task_dir)
            if os.path.isdir(task_dir.as_posix()) and task_dir.stem.startswith('__') == False:
                self.logger.info (f"[Task] - [{task_dir.stem}] is loaded")
                importlib.import_module(f"scheduler.tasks.{task_dir.stem}.task")

    def load_jobs(self):
        jobs_dir = os.path.dirname(os.path.abspath(jobs.__file__))
        for job_dir in os.listdir(jobs_dir):
            job_dir = os.path.join(jobs_dir, job_dir)
            job_dir = PurePosixPath(job_dir)
            if os.path.isdir(job_dir.as_posix()) and job_dir.stem.startswith('__') == False:
                self.logger.info (f"[Job] - [{job_dir.stem}] is loaded")
                importlib.import_module(f"scheduler.jobs.{job_dir.stem}.task")


    
    async def safe_execute(self, func, task_name, task_id, *args, **kwargs):
        async def task_wrapper():
            start_time = time.time()
            self.logger.info(f"[Task] - [{task_name}] - [{task_id}] - is working")
            try:
                await func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"[Task] - [{task_name}] - [{task_id}] - error: {e}")
                self.logger.debug(traceback.format_exc())
            finally:
                end_time = time.time()
                elapsed_time = end_time - start_time
                self.del_instance_from_factory(task_id)
                self.logger.info(f"[Task] - [{task_name}] - [{task_id}] - completed in {elapsed_time} seconds")

        self.asyncio_loop.create_task(task_wrapper())


    def add_instance_to_factory(self, task_id, key, instance):
        if task_id not in self._factory:
            self._factory[task_id] = {}
        self._factory[task_id][key] = instance

    def get_instance_from_factory(self, task_id, key):
        if task_id not in self._factory:
            return None
        return self._factory[task_id].get(key, None)
    
    def del_instance_from_factory(self, task_id):
        if task_id in self._factory:
            del self._factory[task_id]
            return True
        return False

    def add_task(self, task):
        def decorator(func):
            self.tasks[task] = func
            return func
        return decorator

    async def run_task(self, task, **extra):
        task_id = str(uuid.uuid1())
        async with self.semaphore:
            await self.safe_execute(self.tasks[task](**extra), task, task_id)

    async def run_task_by_queue(self, task, **extra):
        task_id = str(uuid.uuid1())
        task = ujson.dumps({"task_id": task_id, "task_name": task, "task_args": extra})
        await self.redis_conn.lpush(self._task_queue_key, task)
        await self.redis_conn.hset(self._task_key.format(task_id), self._status_key, self._task_status_pending)
        return task_id

    async def start_task_handler(self):
        locker = self.redis_conn.locker(self._task_queue_key)
        while not self.shutdown_flag:
            async with locker.lock():
                _, task = await self.redis_conn.brpop(self._task_queue_key, 0)
                task = ujson.loads(task.decode('utf-8'))

                task_id = task["task_id"]
                task_name = task["task_name"]
                task_args = task["task_args"]
                task_key = self._task_key.format(task_id)
                
                await self.redis_conn.hset(task_key, self._status_key, self._task_status_working)
                try:
                    result = await self.safe_execute(self.tasks[task_name](**task_args), task_name, task_id)
                except Exception as e:
                    await self.set_tasks(task_key, key=self._status_key, value=self._task_status_error)
                    await self.set_tasks(task_key, key=self._result_key, value=e.__str__())
                else:
                    await self.set_tasks(task_key, key=self._status_key, value=self._task_status_done)
                    await self.set_tasks(task_key, key=self._result_key, value=result)
    
    def add_job(self, job_name, default_interval):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                while not self.shutdown_flag:
                    job_config_key = self._job_key.format(job_name, self._job_identifier)
                    
                    job_config = await self.redis_conn.hgetall(job_config_key)
                    if job_config:
                        interval = int(job_config.get(self._interval.encode(), default_interval))
                        status = int(job_config.get(self._status.encode(), self._job_status_pending))
                    else:
                        self.logger.info(f"Job [{job_name}] is created - status: {self._job_status_pending}")
                        job_config = {
                                        self._interval: default_interval,
                                        self._status: self._job_status_pending
                                     }
                        await self.redis_conn.hmset(job_config_key, job_config)
                        continue

                    if status == self._job_status_pending:
                        self.logger.warning(f"Job [{job_name}] is not running - status: {status}")
                        await asyncio.sleep(interval)
                        continue

                    await self.safe_execute(func, *args, **kwargs)
                    await asyncio.sleep(interval)

            self.jobs.append(self.asyncio_loop.create_task(wrapper()))
            return func
        return decorator

    def handle_job_error(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                e_traceback = traceback.format_exc()
                self.logger.info(e_traceback)
                return
        return wrapper
        
    def start_jobs(self):
        self.jobs.append(self.asyncio_loop.create_task(self.start_task_handler()))
        self.asyncio_loop.run_until_complete(asyncio.gather(*self.jobs))

    async def get_jobs(self, job_name="*"):
        job_config_key = self._job_key.format(job_name, self._job_identifier)
        job_config = await self.redis_conn.hgetall(job_config_key)
        return {key.decode('utf-8'): value.decode('utf-8') for key, value in job_config.items()}

    async def set_jobs(self, job_name, **kargs):
        job_config_key = self._job_key.format(job_name, self._job_identifier)
        try:
            await self.redis_conn.hset(job_config_key, **kargs)
            await self.redis_conn.expire(job_config_key, 300, gt=True)
        except Exception as e:
            self.logger.error(f"[Job] - Setting job config error: {e}")
            return None

    async def get_tasks(self, task_name=None):
        if task_name is None:
            return self.tasks
        else:
            return self.tasks.get(task_name, None)

    async def set_tasks(self, task_name, **kargs):
        job_config_key = self._task_key.format(task_name, self._job_identifier)
        try:
            await self.redis_conn.hset(job_config_key, **kargs)
            await self.redis_conn.expire(job_config_key, 300, gt=True)
        except Exception as e:
            self.logger.error(f"[Task] - Setting Task config error: {e}")
            return None

            
    async def shutdown(self):
        self.shutdown_flag = True
        tasks = [t for t in asyncio.all_tasks() if t is not
                asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        self.asyncio_loop.stop()