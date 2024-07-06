"""Global (immutable) data using `st.cache`."""

import time
from collections import OrderedDict

import streamlit as st

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
def task_dict() -> dict[str, maa_streamlit.data.Task]:
    tasks = maa_streamlit.data.load_all_tasks()
    return {task.name: task for task in tasks}

@st.cache_resource
def tasksets() -> list[maa_streamlit.data.TaskSet]:
    return sorted(maa_streamlit.data.load_all_tasksets())


@st.cache_data
def managed_devices() -> list[maa_streamlit.data.Device]:
    devices = [taskset.device for taskset in tasksets()]
    try:
        return [d for d in OrderedDict.fromkeys(devices)]
    except Exception as e:
        print(devices)
        raise e

@st.cache_data
def static_option() -> maa_streamlit.data.StaticOption:
    return maa_streamlit.data.load_static_option()

@st.cache_resource
def maa_proxy_dict() -> dict[maa_streamlit.data.Device, "maa.MaaProxy"]:
    res = {}
    for device in managed_devices():
        res[device] = maa.MaaProxy(device)
        time.sleep(1)
    return res

@st.cache_resource
def adb_proxy_dict() -> dict[maa_streamlit.data.Device, maa_streamlit.adb.AdbProxy]:
    return {device: maa_streamlit.adb.AdbProxy(device) for device in managed_devices()}

@st.cache_resource
def inventory_dict() -> dict[maa_streamlit.data.Device, dict]:
    return {device: {} for device in managed_devices()}
