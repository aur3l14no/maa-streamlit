from typing import List

from loguru import logger

from . import adb, background, config, consts, globals, utils  # noqa: F401

logger = logger.bind(module="maa_streamlit")
logger.add(
    consts.MAA_STREAMLIT_STATE_DIR / "maa_streamlit.log",
    level="INFO",
    format=consts.LOGGER_FORMAT,
    filter=lambda record: record["extra"].get("module") == "maa_streamlit",
)


def init():
    import maa

    # init maa_core
    maa.init_core()
    # init globals
    for obj in [getattr(globals, name) for name in globals.__all__]:
        obj()
    logger.info(f"initialized globals: {globals.__all__}")
    background.spawn_scheduler_thread()


def shutdown():
    """Shutdown streamlit.

    1. Delete assts instances.
    2. Invalidate caches.
    """
    for asst in globals.asst_dict().values():
        asst.stop()
    logger.info("All assts stopped!")

    for obj in [getattr(globals, name) for name in globals.__all__]:
        obj.clear()
    logger.info("Globals refreshed!")


def restart():
    shutdown()
    init()


def run_tasks(
    device: str, tasks: List["config.Task"], force_stop: bool = False
) -> bool:
    """Run tasks, prepend `StartUp`.
    `force_stop` takes priority under all circumstances. So use with care.

    | Asst        | Game        | Action                             | What is happening    |
    |-------------|-------------|------------------------------------|----------------------|
    | Not Running | Not Running | Run Tasks (follow `force_stop`)    | Idle                 |
    | Not Running | Running     | Run Tasks (follow `force_stop`)    | User playing? Idle?  |
    | Running     | Not Running | Run Tasks (follow `force_stop`)    | Game starting up?    |
    | Running     | Running     | Run Tasks (follow `force_stop`)    | Running tasks        |
    """
    asst = globals.asst_dict()[device]
    adb_proxy = globals.adb_proxy_dict()[device]

    if asst.running() and force_stop:
        if asst.stop():
            asst.log("INFO", "Asst stopped.")
        else:
            asst.log("ERROR", "Asst failed to stop.")
    if adb_proxy.app_running() and force_stop:
        adb_proxy.force_close()

    if tasks[0].type != "StartUp":
        tasks.insert(0, globals.task_dict()["start"])
    for task in tasks:
        asst.append_task(task.type, task.params)
    logger.info(f"Run tasks: {device} {tasks}")
    return asst.start()
