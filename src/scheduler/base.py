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
        self.job_name_set = set()
        self.redis_conn:aioredis.StrictRedis = redis_conn

        self.semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent tasks

        self._job_identifier = uuid.uuid1().__str__()

        self._job_key = 'job:{}:{}'

        self._job_status_pending = 0
        self._job_status_running = 1

        self._job_expire = 1 * 1000 * 300

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

        self._task_expire = 1 * 1000 * 300

        #self._factory = {}

        self.shutdown_flag = False
        
    @property
    def logging(self) -> logging.Logger:
        return self.logger
    
    async def run_by_worker(self):
        await self.init_loop_by_async()
        self.load_tasks()
        self.load_jobs()
        await self.start_jobs_by_async()
    
    def run_by_thread(self):
        thread = threading.Thread(target=self.init_by_thread)
        thread.start()

    def init_by_thread(self):
        self.init_loop_by_thread()
        self.load_tasks()
        self.load_jobs()
        self.start_jobs_by_thread()
    
    def init_loop_by_thread(self):
        self.asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.asyncio_loop)

    async def run_by_async(self):
        await self.init_loop_by_async()
        self.load_tasks()
        self.load_jobs()
        await self.start_jobs_by_async()

    async def init_loop_by_async(self):
        self.asyncio_loop = asyncio.get_event_loop()
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
                self.logger.info(f"[Task] - [{task_name}] - [{task_id}] - completed in {elapsed_time} seconds")

        self.asyncio_loop.create_task(task_wrapper())


    #def add_instance_to_factory(self, task_id, key, instance):
    #    if task_id not in self._factory:
    #        self._factory[task_id] = {}
    #    self._factory[task_id][key] = instance

    #def get_instance_from_factory(self, task_id, key):
    #    if task_id not in self._factory:
    #        return None
    #    return self._factory[task_id].get(key, None)
    
    #def del_instance_from_factory(self, task_id):
    #    if task_id in self._factory:
    #        del self._factory[task_id]
    #        return True
    #    return False

    def add_task(self, task):
        if task in self.tasks:
            raise Exception(f"Task {task} already exists")
        
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
        await self.set_task(task_id, key=self._status_key, value=self._task_status_pending)
        return task_id

    async def start_task_handler(self):
        locker = self.redis_conn.locker(self._task_queue_key)
        while not self.shutdown_flag:
            async with locker.lock():
                _, task = await self.redis_conn.brpop(self._task_queue_key, 0)
                task = ujson.loads(task)

                task_id = task["task_id"]
                task_name = task["task_name"]
                task_args = task["task_args"]
                task_key = self._task_key.format(task_id)
                
                await self.set_task(task_key, key=self._status_key, value=self._task_status_working)
                await self.set_task(task_key, key=self._result_key, value="None")

                try:
                    result = await self.safe_execute(self.tasks[task_name], task_name, task_id, **task_args)
                except Exception as e:
                    await self.set_task(task_name, key=self._status_key, value=self._task_status_error)
                    await self.set_task(task_name, key=self._result_key, value=e.__str__())
                else:
                    await self.set_task(task_name, key=self._status_key, value=self._task_status_done)
                    await self.set_task(task_name, key=self._result_key, value=result or "None")

    def add_job(self, job_name, default_interval):
        if job_name in self.job_name_set:
            raise Exception(f"Job [{job_name}] already exists")
        self.job_name_set.add(job_name)
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                while not self.shutdown_flag:
                    task_id = str(uuid.uuid1())
                    job_config_key = self._job_key.format(job_name, self._job_identifier)
                    job_config = await self.redis_conn.hgetall(job_config_key)
                    if job_config:
                        await self.redis_conn.expire(job_config_key, self._job_expire)
                        interval = int(job_config.get(self._interval, default_interval))
                        status = int(job_config.get(self._status, self._job_status_pending))
                    else:
                        self.logger.info(f"Job [{job_name}] is created - status: {self._job_status_running}")
                        
                        await self.set_job(job_name, self._interval,  default_interval)
                        await self.set_job(job_name, self._status,    self._job_status_running)
                        continue

                    if status == self._job_status_pending:
                        self.logger.warning(f"Job [{job_name}] is not running - status: {status}")
                        await asyncio.sleep(interval)
                        continue

                    await self.safe_execute(func, job_name, task_id, *args, **kwargs)
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
        
    def start_jobs_by_thread(self):
        self.jobs.append(self.asyncio_loop.create_task(self.start_task_handler()))
        self.asyncio_loop.run_until_complete(asyncio.gather(*self.jobs))

    async def start_jobs_by_async(self):
        self.jobs.append(self.asyncio_loop.create_task(self.start_task_handler()))
        await asyncio.gather(*self.jobs)

    async def get_jobs(self):
        all_jobs = {}
        for job_name in self.job_name_set:
            job_config_key = self._job_key.format(job_name, self._job_identifier)
            job_config = await self.redis_conn.hgetall(job_config_key)
            all_jobs[job_name] = {key: value for key, value in job_config.items()}
        return all_jobs

    async def set_job(self, job_name, key=None, value=None, **kwargs):
        job_config_key = self._job_key.format(job_name, self._job_identifier)
        try:
            if not key and not value:
                for key, value in kwargs.items():
                    await self.redis_conn.hset(job_config_key, key, value)
            else:
                await self.redis_conn.hset(job_config_key, key, value)
            await self.redis_conn.expire(job_config_key, self._job_expire)
            return True
        except Exception as e:
            self.logger.error(f"[Job] - Setting job config error: {e}")
            return False

    async def get_tasks(self):
        hset_tasks = {}
        tasks = await self.redis_conn.lrange(self._task_queue_key, 0, -1)
        tasks = [ujson.loads(task) for task in tasks]            # 获取哈希集中的任务
        
        for task in tasks:
            task_key = self._task_key.format(task['task_id'])
            task_data = await self.redis_conn.hgetall(task_key)
            hset_tasks['task_key'] = {key: value for key, value in task_data.items()}

        return hset_tasks

    async def set_task(self, task_id, **kargs):
        task_key = self._task_key.format(task_id)
        try:
            await self.redis_conn.hset(task_key, **kargs)
            await self.redis_conn.expire(task_key, self._task_expire)
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