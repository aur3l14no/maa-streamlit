from typing import List

from loguru import logger

from . import adb, config, consts, globals, schedule, utils  # noqa: F401

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

    maa.update_core()
    maa.update_ota()

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
    device: str, tasks: List["config.Task"], force_stop: bool = False
) -> bool:
    """Run tasks, prepend `StartUp`.
    `force_stop` takes priority under all circumstances. So use with care.

    | Maa         | Game        | Action                             | What is happening    |
    |-------------|-------------|------------------------------------|----------------------|
    | Not Running | Not Running | Run Tasks (follow `force_stop`)    | Idle                 |
    | Not Running | Running     | Run Tasks (follow `force_stop`)    | User playing? Idle?  |
    | Running     | Not Running | Run Tasks (follow `force_stop`)    | Game starting up?    |
    | Running     | Running     | Run Tasks (follow `force_stop`)    | Running tasks        |
    """
    maa_proxy = globals.maa_proxy_dict()[device]
    adb_proxy = globals.adb_proxy_dict()[device]

    if maa_proxy.running() and force_stop:
        if maa_proxy.stop():
            logger.info(f"Maa core for {device} stopped.")
        else:
            logger.error(f"Maa core for {device} failed to stop.")
    if adb_proxy.app_running() and force_stop:
        adb_proxy.force_close()

    if tasks[0].type != "StartUp":
        tasks.insert(0, globals.task_dict()["start"])
    for task in tasks:
        maa_proxy.append_task(task.type, task.params)
    logger.info(f"Run tasks: {device} {tasks}")
    return maa_proxy.start()
