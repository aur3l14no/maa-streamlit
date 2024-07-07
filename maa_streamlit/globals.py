"""Global (immutable) data using `st.cache`."""

import time

import streamlit as st

import maa
import maa_streamlit

__all__ = [
    "task_dict",
    "tasksets",
    "profiles",
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
def profiles() -> dict[str, maa_streamlit.data.Profile]:
    return maa_streamlit.data.load_all_profiles()


@st.cache_resource
def maa_proxy_dict() -> dict[str, "maa.MaaProxy"]:
    res = {}
    for name, profile in profiles().items():
        res[name] = maa.MaaProxy(profile)
        time.sleep(1)
    return res


@st.cache_resource
def adb_proxy_dict() -> dict[str, maa_streamlit.adb.AdbProxy]:
    return {
        name: maa_streamlit.adb.AdbProxy(profile)
        for name, profile in profiles().items()
    }


# @st.cache_resource
# def inventory_dict() -> dict[str, dict]:
#     return {name: {} for name, _ in profiles().items()}
