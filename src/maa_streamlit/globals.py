"""Global (immutable) data using `st.cache`."""

import time

import streamlit as st

from maa_streamlit.maa import MaaProxy

from . import adb, data

__all__ = [
    "task_dict",
    "tasksets",
    "profiles",
    "maa_proxy_dict",
    "adb_proxy_dict",
]


@st.cache_data
def task_dict() -> dict[str, data.Task]:
    tasks = data.load_all_tasks()
    return {task.name: task for task in tasks}


@st.cache_resource
def tasksets() -> list[data.TaskSet]:
    return sorted(data.load_all_tasksets())


@st.cache_data
def profiles() -> dict[str, data.Profile]:
    return data.load_all_profiles()


@st.cache_resource
def maa_proxy_dict() -> dict[str, MaaProxy]:
    res = {}
    for name, profile in profiles().items():
        res[name] = MaaProxy(profile)
        time.sleep(1)
    return res


@st.cache_resource
def adb_proxy_dict() -> dict[str, adb.AdbProxy]:
    return {
        name: adb.AdbProxy(profile)
        for name, profile in profiles().items()
    }


# @st.cache_resource
# def inventory_dict() -> dict[str, dict]:
#     return {name: {} for name, _ in profiles().items()}
