def init():
    from . import globals, logger, schedule
    from .maa import MaaUpdater

    updater = MaaUpdater()
    updater.update_core()
    # updater.update_ota()

    # init globals
    for obj in [getattr(globals, name) for name in globals.__all__]:
        obj()
    logger.info(f"initialized globals: {globals.__all__}")
    schedule.spawn_scheduler_thread()
