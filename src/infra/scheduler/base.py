import json
import asyncio
import importlib
import logging
import time
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from core.constants import JOB_LOGGER, SCHEDULER_LOGGER, TASK_LOGGER
from infra.redis import RedisClient, RedisLock

from . import jobs, tasks


TaskFunction = Callable[..., Awaitable[Any]]
Decorator = Callable[[TaskFunction], TaskFunction]


def get_croniter():
    from croniter import croniter

    return croniter


@dataclass(frozen=True)
class IntervalJobDefinition:
    name: str
    func: TaskFunction
    default_interval: int
    max_instance: Optional[int] = None


@dataclass(frozen=True)
class CronJobDefinition:
    name: str
    func: TaskFunction
    default_cron: Optional[str] = None
    max_instance: Optional[int] = None


class SchedulerRegistry:
    def __init__(self):
        self.tasks: dict[str, TaskFunction] = {}
        self.interval_jobs: dict[str, IntervalJobDefinition] = {}
        self.cron_jobs: dict[str, CronJobDefinition] = {}
        self._modules_loaded = False

    def load_modules(self, logger: logging.Logger) -> None:
        if self._modules_loaded:
            return

        self._load_package_modules(tasks.__file__, "infra.scheduler.tasks", "Task", logger)
        self._load_package_modules(jobs.__file__, "infra.scheduler.jobs", "Job", logger)
        self._modules_loaded = True

    def _load_package_modules(self, package_file: str, package_name: str, label: str, logger: logging.Logger) -> None:
        package_dir = Path(package_file).resolve().parent
        for module_dir in sorted(package_dir.iterdir()):
            if not module_dir.is_dir() or module_dir.name.startswith("__"):
                continue
            logger.info("[%s] - [%s] is loaded", label, module_dir.name)
            importlib.import_module(f"{package_name}.{module_dir.name}.task")

    def add_task(self, task_name: str) -> Decorator:
        def decorator(func: TaskFunction) -> TaskFunction:
            if task_name in self.tasks:
                raise ValueError(f"Task {task_name} already exists")
            self.tasks[task_name] = func
            return func

        return decorator

    def add_interval_job(self, job_name: str, default_interval: int, max_instance: Optional[int] = None) -> Decorator:
        def decorator(func: TaskFunction) -> TaskFunction:
            if job_name in self.interval_jobs or job_name in self.cron_jobs:
                raise ValueError(f"Job {job_name} already exists")
            self.interval_jobs[job_name] = IntervalJobDefinition(
                name=job_name,
                func=func,
                default_interval=default_interval,
                max_instance=max_instance,
            )
            return func

        return decorator

    def add_cron_job(self, job_name: str, default_cron_expr: Optional[str] = None, max_instance: Optional[int] = None) -> Decorator:
        def decorator(func: TaskFunction) -> TaskFunction:
            if job_name in self.interval_jobs or job_name in self.cron_jobs:
                raise ValueError(f"Job {job_name} already exists")
            self.cron_jobs[job_name] = CronJobDefinition(
                name=job_name,
                func=func,
                default_cron=default_cron_expr,
                max_instance=max_instance,
            )
            return func

        return decorator

    def add_job(self, job_name: str, default_interval: int, max_instance: Optional[int] = None) -> Decorator:
        return self.add_interval_job(job_name, default_interval, max_instance=max_instance)


scheduler_registry = SchedulerRegistry()


def add_task(task_name: str) -> Decorator:
    return scheduler_registry.add_task(task_name)


def add_interval_job(job_name: str, default_interval: int, max_instance: Optional[int] = None) -> Decorator:
    return scheduler_registry.add_interval_job(job_name, default_interval, max_instance=max_instance)


def add_cron_job(job_name: str, default_cron_expr: Optional[str] = None, max_instance: Optional[int] = None) -> Decorator:
    return scheduler_registry.add_cron_job(job_name, default_cron_expr, max_instance=max_instance)


def add_job(job_name: str, default_interval: int, max_instance: Optional[int] = None) -> Decorator:
    return scheduler_registry.add_job(job_name, default_interval, max_instance=max_instance)


class Scheduler:
    def __init__(self, redis_conn: RedisClient, *, registry: SchedulerRegistry | None = None):
        self.redis_conn = redis_conn
        self.registry = registry or scheduler_registry
        self.logger = logging.getLogger(SCHEDULER_LOGGER)

        self.semaphore = asyncio.Semaphore(10)
        self.shutdown_flag = False
        self._runtime_started = False
        self._worker_tasks: set[asyncio.Task] = set()
        self._execution_tasks: set[asyncio.Task] = set()

        self._interval_job_key = "scheduler:job:interval:{}"
        self._cron_job_key = "scheduler:job:cron:{}"
        self._task_queue_key = "scheduler:task:queue"
        self._task_key = "scheduler:task:{}"
        self._running_counter_key = "scheduler:job:running:{}"

        self._interval = "interval"
        self._cron = "cron"
        self._status = "status"
        self._job_type = "job_type"

        self._job_status_paused = 0
        self._job_status_running = 1
        self._task_status_error = -1
        self._task_status_pending = 0
        self._task_status_working = 1
        self._task_status_done = 2

        self._job_expire = 300_000
        self._task_expire = 300_000

    def _load_modules(self) -> None:
        self.registry.load_modules(self.logger)

    async def start(self) -> None:
        await self.run_by_async()

    async def run_by_async(self) -> None:
        if self._runtime_started:
            return

        self._load_modules()
        self.shutdown_flag = False
        self._runtime_started = True

        self._create_worker(self.start_task_handler())
        for definition in self.registry.interval_jobs.values():
            self._create_worker(self._run_interval_job(definition))
        for definition in self.registry.cron_jobs.values():
            self._create_worker(self._run_cron_job(definition))

        self.logger.info("Scheduler has started.")

    def _create_worker(self, coroutine: Awaitable[Any]) -> asyncio.Task:
        task = asyncio.create_task(coroutine)
        self._worker_tasks.add(task)
        task.add_done_callback(self._worker_tasks.discard)
        return task

    def _create_execution(self, coroutine: Awaitable[Any]) -> asyncio.Task:
        task = asyncio.create_task(coroutine)
        self._execution_tasks.add(task)
        task.add_done_callback(self._execution_tasks.discard)
        return task

    async def _increment_running(self, job_name: str) -> int:
        key = self._running_counter_key.format(job_name)
        return await self.redis_conn.incr(key)

    async def _decrement_running(self, job_name: str) -> int:
        key = self._running_counter_key.format(job_name)
        count = await self.redis_conn.decr(key)
        if count <= 0:
            await self.redis_conn.delete(key)
        return count

    def _get_execution_logger(self, namespace: str) -> logging.Logger:
        if namespace == "task":
            return logging.getLogger(TASK_LOGGER)
        if namespace == "job":
            return logging.getLogger(JOB_LOGGER)
        return self.logger

    async def _execute(
        self,
        func: TaskFunction,
        execution_name: str,
        execution_id: str,
        *,
        namespace: str,
        max_instance: Optional[int] = None,
        **kwargs: Any,
    ) -> bool:
        logger = self._get_execution_logger(namespace)
        start_time = time.time()
        running_count_incremented = False

        logger.info("[%s] - [%s] - [%s] is working", namespace.title(), execution_name, execution_id)
        try:
            async with self.semaphore:
                if max_instance is not None:
                    running_count = await self._increment_running(execution_name)
                    running_count_incremented = True
                    if running_count > max_instance:
                        logger.warning(
                            "[%s] - [%s] skipped because max_instance=%s",
                            namespace.title(),
                            execution_name,
                            max_instance,
                        )
                        return False

                lock = RedisLock(self.redis_conn, f"{namespace}:{execution_name}")
                async with lock.lock():
                    await func(**kwargs)
            return True
        except Exception as exc:
            logger.error("[%s] - [%s] - [%s] failed: %s", namespace.title(), execution_name, execution_id, exc)
            logger.debug(traceback.format_exc())
            return False
        finally:
            if running_count_incremented:
                await self._decrement_running(execution_name)
            elapsed_time = time.time() - start_time
            logger.info(
                "[%s] - [%s] - [%s] completed in %.2f seconds",
                namespace.title(),
                execution_name,
                execution_id,
                elapsed_time,
            )

    async def run_task(self, task_name: str, **extra: Any) -> bool:
        self._load_modules()
        task = self.registry.tasks.get(task_name)
        if task is None:
            self.logger.error("Task '%s' is not registered.", task_name)
            return False

        return await self._execute(task, task_name, str(uuid.uuid4()), namespace="task", **extra)

    async def run_task_by_queue(self, task_name: str, **extra: Any) -> str:
        self._load_modules()
        if task_name not in self.registry.tasks:
            self.logger.error("Task '%s' is not registered.", task_name)
            return ""

        task_id = str(uuid.uuid4())
        task_data = json.dumps({"task_id": task_id, "task_name": task_name, "task_args": extra})
        await self.redis_conn.lpush(self._task_queue_key, task_data)
        await self._set_task(task_id, status=self._task_status_pending)
        return task_id

    async def start_task_handler(self) -> None:
        while not self.shutdown_flag:
            try:
                item = await self.redis_conn.brpop(self._task_queue_key, timeout=5)
                if not item:
                    continue

                _, payload = item
                task_data = json.loads(payload)
                task_id = task_data["task_id"]
                task_name = task_data["task_name"]
                task_args = task_data.get("task_args", {})
                task = self.registry.tasks.get(task_name)

                if task is None:
                    await self._set_task(task_id, status=self._task_status_error, result="Task not registered")
                    continue

                await self._set_task(task_id, status=self._task_status_working, result="None")
                success = await self._execute(task, task_name, task_id, namespace="task", **task_args)
                if success:
                    await self._set_task(task_id, status=self._task_status_done, result="Success")
                else:
                    await self._set_task(task_id, status=self._task_status_error, result="Failed")
            except Exception as exc:
                self.logger.error("[Scheduler] Unexpected error in task handler: %s", exc)
                self.logger.debug(traceback.format_exc())
                await asyncio.sleep(1)

    async def _run_interval_job(self, definition: IntervalJobDefinition) -> None:
        while not self.shutdown_flag:
            config = await self._get_interval_job_config(definition.name, definition.default_interval)
            interval = int(config[self._interval])
            status = int(config[self._status])

            if status == self._job_status_running:
                self._create_execution(
                    self._execute(
                        definition.func,
                        definition.name,
                        str(uuid.uuid4()),
                        namespace="job",
                        max_instance=definition.max_instance,
                    )
                )
            await asyncio.sleep(max(interval, 1))

    async def _run_cron_job(self, definition: CronJobDefinition) -> None:
        current_expr: Optional[str] = None
        next_run_at: Optional[datetime] = None

        while not self.shutdown_flag:
            config = await self._get_cron_job_config(definition.name, definition.default_cron)
            cron_expr = config.get(self._cron)
            status = int(config[self._status])

            if status != self._job_status_running or not cron_expr:
                current_expr = None
                next_run_at = None
                await asyncio.sleep(5)
                continue

            now = datetime.now()
            if cron_expr != current_expr or next_run_at is None:
                current_expr = cron_expr
                next_run_at = get_croniter()(cron_expr, now).get_next(datetime)

            if now >= next_run_at:
                self._create_execution(
                    self._execute(
                        definition.func,
                        definition.name,
                        str(uuid.uuid4()),
                        namespace="job",
                        max_instance=definition.max_instance,
                    )
                )
                next_run_at = get_croniter()(cron_expr, now).get_next(datetime)
                continue

            delay = min(max((next_run_at - now).total_seconds(), 0.5), 30)
            await asyncio.sleep(delay)

    async def _get_interval_job_config(self, job_name: str, default_interval: int) -> dict[str, Any]:
        job_key = self._interval_job_key.format(job_name)
        job_config = await self.redis_conn.hgetall(job_key) or {}
        interval = int(job_config.get(self._interval, default_interval))
        status = int(job_config.get(self._status, self._job_status_running))

        if not job_config:
            await self.redis_conn.hset(
                job_key,
                mapping={
                    self._job_type: "interval",
                    self._interval: str(interval),
                    self._status: str(status),
                },
            )
            await self.redis_conn.expire(job_key, self._job_expire)

        return {
            self._job_type: "interval",
            self._interval: interval,
            self._status: status,
        }

    async def _get_cron_job_config(self, job_name: str, default_cron: Optional[str]) -> dict[str, Any]:
        job_key = self._cron_job_key.format(job_name)
        job_config = await self.redis_conn.hgetall(job_key) or {}
        cron_expr = job_config.get(self._cron, default_cron)
        status = int(job_config.get(self._status, self._job_status_running))

        if not job_config:
            mapping = {
                self._job_type: "cron",
                self._status: str(status),
            }
            if cron_expr:
                mapping[self._cron] = cron_expr
            await self.redis_conn.hset(job_key, mapping=mapping)
            await self.redis_conn.expire(job_key, self._job_expire)

        return {
            self._job_type: "cron",
            self._cron: cron_expr,
            self._status: status,
        }

    async def get_jobs(self) -> dict[str, dict[str, Any]]:
        self._load_modules()
        result: dict[str, dict[str, Any]] = {}

        for definition in self.registry.interval_jobs.values():
            result[definition.name] = await self._get_interval_job_config(definition.name, definition.default_interval)

        for definition in self.registry.cron_jobs.values():
            result[definition.name] = await self._get_cron_job_config(definition.name, definition.default_cron)

        return result

    async def set_job(
        self,
        job_name: str,
        interval: Optional[int] = None,
        cron: Optional[str] = None,
        status: Optional[int] = None,
    ) -> bool:
        self._load_modules()

        if job_name in self.registry.interval_jobs:
            if cron is not None:
                return False

            current = await self._get_interval_job_config(job_name, self.registry.interval_jobs[job_name].default_interval)
            interval_value = interval if interval is not None else current[self._interval]
            status_value = status if status is not None else current[self._status]
            if interval_value < 1:
                return False

            await self.redis_conn.hset(
                self._interval_job_key.format(job_name),
                mapping={
                    self._job_type: "interval",
                    self._interval: str(interval_value),
                    self._status: str(status_value),
                },
            )
            await self.redis_conn.expire(self._interval_job_key.format(job_name), self._job_expire)
            return True

        if job_name in self.registry.cron_jobs:
            current = await self._get_cron_job_config(job_name, self.registry.cron_jobs[job_name].default_cron)
            cron_value = cron if cron is not None else current[self._cron]
            status_value = status if status is not None else current[self._status]

            if cron_value:
                try:
                    get_croniter()(cron_value, datetime.now())
                except Exception:
                    return False

            mapping = {
                self._job_type: "cron",
                self._status: str(status_value),
            }
            if cron_value:
                mapping[self._cron] = cron_value
            await self.redis_conn.hset(self._cron_job_key.format(job_name), mapping=mapping)
            await self.redis_conn.expire(self._cron_job_key.format(job_name), self._job_expire)
            return True

        return False

    async def _set_task(self, task_id: str, **kwargs: Any) -> None:
        task_key = self._task_key.format(task_id)
        mapping = {key: str(value) for key, value in kwargs.items()}
        if not mapping:
            return
        await self.redis_conn.hset(task_key, mapping=mapping)
        await self.redis_conn.expire(task_key, self._task_expire)

    async def shutdown(self) -> None:
        self.shutdown_flag = True

        worker_tasks = [task for task in self._worker_tasks if not task.done()]
        execution_tasks = [task for task in self._execution_tasks if not task.done()]
        for task in [*worker_tasks, *execution_tasks]:
            task.cancel()

        if worker_tasks or execution_tasks:
            await asyncio.gather(*worker_tasks, *execution_tasks, return_exceptions=True)

        self._worker_tasks.clear()
        self._execution_tasks.clear()
        self._runtime_started = False
