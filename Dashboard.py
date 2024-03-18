if __name__ == "__main__":
    import datetime as dt
    import threading

    import streamlit as st
    import tomllib
    from streamlit_authenticator import Authenticate
    from streamlit_autorefresh import st_autorefresh

    import maa_streamlit

    @st.cache_resource
    def init_maa_streamlit_lock():
        return threading.Lock()

    @st.cache_resource
    def init_maa_streamlit():
        with init_maa_streamlit_lock():
            maa_streamlit.init()

    st.set_page_config(
        page_title="MaaS",
        page_icon="⛵︎",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    auth_config = tomllib.loads(
        (maa_streamlit.config.CONFIG_DIR / "auth.toml").read_text()
    )
    authenticator = Authenticate(
        auth_config["credentials"],
        auth_config["cookie"]["name"],
        auth_config["cookie"]["key"],
        auth_config["cookie"]["expiry_days"],
    )

    name, authentication_status, username = authenticator.login()

    if not st.session_state["authentication_status"]:
        st.stop()

    init_maa_streamlit()

    _ = st_autorefresh(10_000, key="dashboard_refresher")

    st.title("Live Dashboard")

    for device in maa_streamlit.globals.managed_devices():
        st.markdown(f"## {device.name}")
        maa_proxy = maa_streamlit.globals.maa_proxy_dict()[device]
        adb_proxy = maa_streamlit.globals.adb_proxy_dict()[device]
        # except Exception as e:
        #     # debug
        #     maa_streamlit.logger.error(
        #         f"maa_proxy_dict: {maa_streamlit.globals.maa_proxy_dict()}"
        #     )
        #     maa_streamlit.logger.error(
        #         f"adb_proxy_dict: {maa_streamlit.globals.adb_proxy_dict()}"
        #     )
        #     raise e

        col_img, col_ctrl, col_log = st.columns(3)

        with col_img:
            st.markdown("#### Screenshot")
            st.image(adb_proxy.screenshot())

        with col_ctrl:
            st.markdown("#### Status")
            # APP CTRL
            col_label, col_status, col_stop = st.columns(3)
            with col_label:
                st.markdown("🕹️ **app**")
            with col_status:
                st.markdown("🟩" if adb_proxy.app_running() else "🟥")
            with col_stop:
                st.button(
                    "stop",
                    key=f"{device}/app/stop",
                    on_click=lambda maa_proxy, adb_proxy: (
                        maa_proxy.stop(),
                        adb_proxy.force_close(),
                    ),
                    args=(maa_proxy, adb_proxy),
                )

            # MAA CTRL
            col_label, col_status, col_stop = st.columns(3)
            with col_label:
                st.markdown("🤖 **maa**")
            with col_status:
                st.markdown("🟩" if maa_proxy.running() else "🟥")
            with col_stop:
                st.button(
                    "stop",
                    key=f"{device}/maa/stop",
                    on_click=lambda maa_proxy: maa_proxy.stop(),
                    args=(maa_proxy,),
                )

            # Run Tasks
            st.markdown("#### Run Tasks")
            with st.form(f"{device}/tasks_form"):
                options = st.multiselect(
                    label="Tasks",
                    label_visibility="hidden",
                    placeholder="Choose tasks to run (in order)",
                    options=list(maa_streamlit.globals.task_dict().keys()),
                    key=f"{device}/tasks_form/selected_tasks",
                )
                st.form_submit_button(
                    "Start",
                    on_click=lambda device: (
                        maa_streamlit.run_tasks(
                            device,
                            [
                                maa_streamlit.globals.task_dict()[k]
                                for k in st.session_state[
                                    f"{device}/tasks_form/selected_tasks"
                                ]
                            ],
                        ),
                    ),
                    args=(device,),
                )

            # Scheduled Tasksets
            st.markdown("#### Scheduled Tasksets")
            tasksets = [
                taskset
                for taskset in maa_streamlit.globals.tasksets()
                if taskset.device == device
            ]
            # TODO allow dynamic config?
            for taskset in tasksets:
                col_name, col_schedule, col_start = st.columns(3)
                with col_name:
                    st.markdown(f"**{taskset.name}**")
                with col_schedule:

                    def handle_toggle_schedule(taskset: maa_streamlit.config.TaskSet):
                        taskset.enable = not taskset.enable

                    if taskset.schedule:
                        st.toggle(
                            str(taskset.schedule),
                            on_change=handle_toggle_schedule,
                            args=(taskset,),
                            key=f"{taskset.device}/{taskset.name}/schedule",
                            value=taskset.enable,
                        )
                with col_start:

                    def handle_start_taskset(
                        taskset: maa_streamlit.config.TaskSet,
                    ):
                        maa_streamlit.run_tasks(taskset.device, taskset.tasks)
                        maa_streamlit.schedule.scheduled_tasks_stats_dict()[
                            taskset.name
                        ] = dt.datetime.now()

                    st.button(
                        "start",
                        on_click=handle_start_taskset,
                        args=(taskset,),
                        key=f"{taskset.device}/{taskset.name}/start",
                    )
                tasks_str = " | ".join(
                    [
                        task.name
                        if (preset := maa_streamlit.globals.task_dict().get(task.name))
                        and task.params == preset.params
                        else task.name + "*"
                        for task in taskset.tasks
                    ]
                )
                st.markdown(
                    # f"{'🟩' if taskset.enable else '🟥'} **[{taskset.name}] @ {taskset.schedule}**\n\n"
                    f"last: {maa_streamlit.schedule.scheduled_tasks_stats_dict()[taskset.name]}\n\n"
                    f"{' | '.join([task.name if task.params == maa_streamlit.globals.task_dict()[task.name].params else task.name + '*' for task in taskset.tasks])}"
                )

        with col_log:
            st.markdown("#### Log")
            path = maa_streamlit.consts.MAA_STREAMLIT_STATE_DIR / f"{device.name}.log"
            if path.exists():
                st.code(
                    maa_streamlit.utils.last_n_lines(path.read_text(), 30),
                    language="log",
                )
            else:
                st.code("")
