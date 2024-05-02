"""from utils.utils import *

from utils.ContractsHandle import contractsHandle

from utils.Models.webiste import Tasks

@TaskScheduler.add_job
async def del_contract_task(asyncio_loop):

    while True:

        async for initial_task in _get_tasks("Audit"):
            task_info = initial_task.task_info

            if await _is_contract_exist(task_info):
                task = _execute(asyncio_loop, _del_contract_task, task_info)
                task.start()

        await asyncio.sleep(10)

async def _get_tasks(task_type, **extra):

    successfully_tasks = await Tasks.filter(status = 2).all()
    error_tasks = await Tasks.filter(status = -1).all()

    task_list = successfully_tasks + error_tasks

    for task in task_list:
        task_info = task.task_info

        if task_info['task'] == task_type:

            yield task

class _execute(threading.Thread):
    def __init__(self, asyncio_loop, task, task_info):
        threading.Thread.__init__(self)
        self.asyncio_loop = asyncio_loop
        self.task = task
        self.task_info = task_info

    def run(self):
        asyncio.run_coroutine_threadsafe(self.task(self.task_info), self.asyncio_loop)


async def _del_contract_task(task_info):
    #读取任务信息
    task_id = task_info['task_id']

    Logger.info(f"Task[{task_id}] - is done, ready for deleting.")
    
    contractsHandle.delete_dirs(Config.UploadsPath, task_id)

async def _is_contract_exist(task_info):
    #读取任务信息
    task_id = task_info['task_id']

    directory = os.path.join(Config.UploadsPath, task_id)
    if os.path.exists(directory):
        return True
    else:
        return False
"""