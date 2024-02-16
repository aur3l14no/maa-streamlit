"""Background tasks."""
import datetime as dt
import logging
import threading
import time

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

import maa_streamlit

logger = logging.getLogger("maa_streamlit.background")


def cron_delta(cron_time: dt.time, datetime: dt.datetime):
    min_delta = dt.timedelta(days=1)
    for delta_days in range(-1, 2):
        offset_date = datetime.date() + dt.timedelta(days=delta_days)
        delta = abs(dt.datetime.combine(offset_date, cron_time) - datetime)
        if delta < min_delta:
            min_delta = delta
    return min_delta


@st.cache_resource
def scheduled_tasks_stats_dict():
    tasksets = maa_streamlit.globals.tasksets()
    return {taskset.name: None for taskset in tasksets}


@st.cache_resource
def spawn_scheduler_thread() -> threading.Thread:
    MIN_INTERVAL_BETWEEN_RUNS_PER_TASKSET = dt.timedelta(minutes=10)

    # FIXME avoid repetitive runs
    def f():
        tasksets = maa_streamlit.globals.tasksets()
        while True:
            now = dt.datetime.now()
            for taskset in tasksets:
                if (
                    taskset.schedule
                    and taskset.enable
                    and cron_delta(taskset.schedule, dt.datetime.now())
                    < dt.timedelta(minutes=1)
                    and (last_run := scheduled_tasks_stats_dict()[taskset.name])
                    and now - last_run > MIN_INTERVAL_BETWEEN_RUNS_PER_TASKSET
                ):
                    logger.info(f"Scheduled taskset: {taskset.name}")
                    maa_streamlit.run_tasks(taskset.asst.address, taskset.tasks)
                    scheduled_tasks_stats_dict()[taskset.name] = dt.datetime.now()
            time.sleep(60)

    t = threading.Thread(name="scheduler", target=f, daemon=True)
    add_script_run_ctx(t)
    t.start()
    return t
