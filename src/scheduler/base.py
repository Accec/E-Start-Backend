import asyncio
import traceback
from utils import logger
from functools import wraps

class Scheduler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.logger = logger.Logger()
        self.logger.info("Scheduler is working now...")
        self.jobs = []
        self.tasks = {}
    
    @property
    def logging(self) -> logger.Logger:
        return self.logger

    async def init_loop(self):
        self.logger.info("init asyncio loop is successfully")
        self.asyncio_loop = asyncio.get_event_loop()

    def add_task(self, task):
        def decorator(func):
            self.tasks[task] = func
            return func
        return decorator

    async def run_task(self, task, **extra):
        await asyncio.gather(self.asyncio_loop.create_task(self.tasks[task](**extra)))

    def handle_task_error(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                e_traceback = traceback.format_exc()
                self.logger.info(e_traceback)
                return
        return wrapper
    
    def add_job(self, func):
        self.jobs.append(self.asyncio_loop.create_task(func(self.asyncio_loop)))

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
        
    async def start_jobs(self):
        await asyncio.gather(*self.jobs)

    async def cancel_jobs(self):
        for job in self.jobs:
            job.cancel()
        await asyncio.gather(*self.jobs, return_exceptions=True)