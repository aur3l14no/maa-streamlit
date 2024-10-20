"""Background tasks."""

import datetime as dt
import threading
import time

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

from . import control, globals, logger


def cron_delta(cron_time: dt.time, datetime: dt.datetime):
    min_delta = dt.timedelta(days=1)
    for delta_days in range(-1, 2):
        offset_date = datetime.date() + dt.timedelta(days=delta_days)
        delta = abs(dt.datetime.combine(offset_date, cron_time) - datetime)
        if delta < min_delta:
            min_delta = delta
    return min_delta


@st.cache_resource
def spawn_scheduler_thread() -> threading.Thread:
    MIN_INTERVAL_BETWEEN_RUNS_PER_TASKSET = dt.timedelta(minutes=10)
    TOLERANCE = dt.timedelta(seconds=40)
    FORCE_STOP = True

    def f():
        while True:
            now = dt.datetime.now()
            for taskset in globals.tasksets():
                if (
                    taskset.schedule
                    and taskset.enabled
                    and cron_delta(taskset.schedule, now) < TOLERANCE
                    and (
                        taskset.last_run is None
                        or (
                            now - taskset.last_run
                            > MIN_INTERVAL_BETWEEN_RUNS_PER_TASKSET
                        )
                    )
                ):
                    logger.info(f"Scheduled taskset: {taskset.name}")

                    control.run_tasks(
                        taskset.profile,
                        taskset.tasks,
                        force_stop=FORCE_STOP,
                    )
                    taskset.last_run = dt.datetime.now()
            time.sleep(60)

    t = threading.Thread(name="scheduler", target=f, daemon=True)
    add_script_run_ctx(t)
    t.start()
    return t
