import datetime as dt
import time
from copy import deepcopy

from loguru import logger

from . import adb, consts, data, globals, schedule, utils  # noqa: F401

logger = logger.bind(module="maa_streamlit")
logger.add(
    consts.MAA_STREAMLIT_STATE_DIR / "maa_streamlit.log",
    level="INFO",
    format=consts.LOGGER_FORMAT,
    filter=lambda record: record["extra"].get("module") == "maa_streamlit",
    enqueue=True,
)


def init():
    import maa

    updater = maa.MaaUpdater()
    updater.update_core()
    # updater.update_ota()

    # init globals
    for obj in [getattr(globals, name) for name in globals.__all__]:
        obj()
    logger.info(f"initialized globals: {globals.__all__}")
    schedule.spawn_scheduler_thread()


# def shutdown():
#     """Shutdown streamlit.

#     1. Delete maa_proxy instances.
#     2. Invalidate caches.
#     """
#     for maa_proxy in globals.maa_proxy_dict().values():
#         maa_proxy.shutdown()
#     logger.info("All MaaProxy shutdown!")

#     for obj in [getattr(globals, name) for name in globals.__all__]:
#         obj.clear()
#     logger.info("Globals refreshed!")


# def restart():
#     shutdown()
#     init()


def run_tasks(
    profile_name: str,
    tasks: list["data.Task"],
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
        1: "AP-5",
        2: "CE-6",
        3: "CA-5",
        4: "AP-5",
        5: "CA-5",
        6: "AP-5",
        7: "AP-5",
    }
    for task in tasks:
        if task.type == "AutoFight":
            task.type = "Fight"
            weekday = utils.get_arknights_weekday(dt.datetime.now())
            task.params.update({"stage": autofight_dict[weekday]})
    for task in tasks:
        if task.enabled:
            maa_proxy.append_task(task.type, task.params)
    logger.info(f"Run tasks: {profile_name} {tasks}")
    return maa_proxy.start()
