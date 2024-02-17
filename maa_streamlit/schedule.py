"""Background tasks."""
import datetime as dt
import threading
import time
from typing import Optional

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

import maa_streamlit


def cron_delta(cron_time: dt.time, datetime: dt.datetime):
    min_delta = dt.timedelta(days=1)
    for delta_days in range(-1, 2):
        offset_date = datetime.date() + dt.timedelta(days=delta_days)
        delta = abs(dt.datetime.combine(offset_date, cron_time) - datetime)
        if delta < min_delta:
            min_delta = delta
    return min_delta


@st.cache_resource
def scheduled_tasks_stats_dict() -> dict[str, Optional[dt.datetime]]:
    tasksets = maa_streamlit.globals.tasksets()
    return {taskset.name: None for taskset in tasksets}


@st.cache_resource
def spawn_scheduler_thread() -> threading.Thread:
    MIN_INTERVAL_BETWEEN_RUNS_PER_TASKSET = dt.timedelta(minutes=10)
    TOLERANCE = dt.timedelta(minutes=1)
    FORCE_STOP = True

    def f():
        tasksets = maa_streamlit.globals.tasksets()
        while True:
            now = dt.datetime.now()
            for taskset in tasksets:
                maa_streamlit.logger.trace(
                    f"Tick! {taskset.name} @ {taskset.schedule} has delta: {cron_delta(taskset.schedule, now)}"
                )
                if (
                    taskset.schedule
                    and taskset.enable
                    and cron_delta(taskset.schedule, now) < TOLERANCE
                    and (
                        (last_run := scheduled_tasks_stats_dict()[taskset.name]) is None
                        or (now - last_run > MIN_INTERVAL_BETWEEN_RUNS_PER_TASKSET)
                    )
                ):
                    maa_streamlit.logger.info(f"Scheduled taskset: {taskset.name}")
                    maa_streamlit.run_tasks(
                        taskset.asst.device, taskset.tasks, force_stop=FORCE_STOP
                    )
                    scheduled_tasks_stats_dict()[taskset.name] = dt.datetime.now()
            time.sleep(60)

    t = threading.Thread(name="scheduler", target=f, daemon=True)
    add_script_run_ctx(t)
    t.start()
    return t
