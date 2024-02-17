"""Global (immutable) data using `st.cache`."""
import os
import subprocess as sp
from collections import OrderedDict
from typing import List

import streamlit as st
from loguru import logger

import maa
import maa_streamlit

__all__ = [
    "task_dict",
    "tasksets",
    "managed_devices",
    "maa_proxy_dict",
    "adb_proxy_dict",
]


@st.cache_data
def task_dict() -> dict[str, maa_streamlit.config.Task]:
    tasks = maa_streamlit.config.load_all_tasks()
    return {task.name: task for task in tasks}


@st.cache_data
def tasksets() -> List[maa_streamlit.config.TaskSet]:
    return maa_streamlit.config.load_all_tasksets()


@st.cache_data
def managed_devices() -> List[maa_streamlit.config.Device]:
    devices = [taskset.device for taskset in tasksets()]
    return [d for d in OrderedDict.fromkeys(devices)]


# @st.cache_data
# def adb_devices() -> List[str]:
#     res = sp.check_output(["adb", "devices"], encoding="utf8")
#     return [line.split()[0] for line in res.strip().splitlines()[1:]]


@st.cache_resource
def maa_proxy_dict() -> dict[maa_streamlit.config.Device, maa.MaaProxy]:
    logger.warning(managed_devices())
    return {device: maa.MaaProxy(device) for device in managed_devices()}


@st.cache_resource
def adb_proxy_dict() -> dict[maa_streamlit.config.Device, maa_streamlit.adb.AdbProxy]:
    return {device: maa_streamlit.adb.AdbProxy(device) for device in managed_devices()}
