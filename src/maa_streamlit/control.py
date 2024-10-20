import datetime as dt
import random
import time
from copy import deepcopy

from . import globals, logger, utils
from .data import Task


def run_tasks(
    profile_name: str,
    tasks: list[Task],
    force_stop: bool = False,
) -> bool:
    """Run tasks, prepend `StartUp`. The main control function exposed to UI.
    `force_stop` takes priority under all circumstances. So use with care.

    | Maa         | Game        | Action                             | What is happening    |
    |-------------|-------------|------------------------------------|----------------------|
    | Not Running | Not Running | Run Tasks (follow `force_stop`)    | Idle                 |
    | Not Running | Running     | Run Tasks (follow `force_stop`)    | User playing? Idle?  |
    | Running     | Not Running | Return or Stop then Run Tasks      | Game starting up?    |
    | Running     | Running     | Return or Stop then Run Tasks      | Running tasks        |
    """
    maa_proxy = globals.maa_proxy_dict()[profile_name]
    adb_proxy = globals.adb_proxy_dict()[profile_name]
    tasks = deepcopy(tasks)

    # maa_proxy must **not** be running before start
    while maa_proxy.running():
        if force_stop:
            if maa_proxy.stop():
                logger.info(f"[Runner] Maa core for {profile_name} is force-stopped.")
                # fix: sometimes maa core hangs there for a few seconds and blocks following executions
                time.sleep(1)
            else:
                logger.error(f"[Runner] Maa core for {profile_name} failed to stop.")
                return False
        else:
            logger.error(
                f"[Runner] Maa core for {profile_name} is running while receiving new tasks "
                "and you did not specify `force_stop`"
            )
            return False
    # app could be running before start
    if adb_proxy.app_running() and force_stop:
        adb_proxy.force_close()
        logger.info(f"[Runner] App on {profile_name} is force-stopped.")

    if tasks[0].type != "StartUp":
        tasks.insert(0, globals.task_dict()["start"])
    # replace "AutoFight" with "fight" and stage name
    autofight_dict = {
        1: (["AP-5"], [1]),
        2: (["1-7", "PR-B-1", "PR-B-2"], [1, 1, 3]),  # 术士狙击
        3: (
            ["PR-D-1", "PR-D-2", "PR-C-1", "PR-C-2"],
            [1, 3, 0.25, 0.75],
        ),  # 近卫特种/先锋辅助
        4: (["AP-5"], [1]),
        5: (["CA-5", "PR-A-1", "PR-A-2"], [1, 1, 3]),  # 医疗盾卫
        6: (["AP-5"], [1]),
        7: (["AP-5"], [1]),
    }
    for task in tasks:
        if task.type == "AutoFight":
            task.type = "Fight"
            weekday = utils.get_arknights_weekday(dt.datetime.now())
            task.params.update({"stage": random.choices(*autofight_dict[weekday])[0]})
    for task in tasks:
        if task.enabled:
            maa_proxy.append_task(task.type, task.params)
    logger.info(f"Run tasks: {profile_name} {tasks}")
    return maa_proxy.start()
