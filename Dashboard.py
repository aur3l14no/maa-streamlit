if __name__ == "__main__":
    import datetime as dt
    import threading

    import streamlit as st

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

    init_maa_streamlit()

    profiles = list(maa_streamlit.globals.profiles().keys())  # NOTE `keys()`

    tabs = st.tabs(profiles)
    for profile, tab in zip(profiles, tabs):
        with tab:
            maa_proxy = maa_streamlit.globals.maa_proxy_dict()[profile]
            adb_proxy = maa_streamlit.globals.adb_proxy_dict()[profile]

            col_img, col_ctrl, col_log = st.columns(3)

            with col_img:
                st.markdown("#### Screenshot")
                st.image(maa_proxy.get_image() or adb_proxy.screenshot())
                st.button("⟳", key=f"{profile}/refresh")

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
                        key=f"{profile}/app/stop",
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
                        key=f"{profile}/maa/stop",
                        on_click=lambda maa_proxy: maa_proxy.stop(),
                        args=(maa_proxy,),
                    )

                # Run Tasks
                st.markdown("#### Run Tasks")
                with st.form(f"{profile}/tasks_form"):
                    options = st.multiselect(
                        label="Tasks",
                        label_visibility="hidden",
                        placeholder="Choose tasks to run (in order)",
                        options=list(maa_streamlit.globals.task_dict().keys()),
                        key=f"{profile}/tasks_form/selected_tasks",
                    )
                    st.form_submit_button(
                        "Start",
                        on_click=lambda profile: (
                            maa_streamlit.run_tasks(
                                profile,
                                [
                                    maa_streamlit.globals.task_dict()[k]
                                    for k in st.session_state[
                                        f"{profile}/tasks_form/selected_tasks"
                                    ]
                                ],
                            ),
                        ),
                        args=(profile,),
                    )

                # Scheduled Tasksets
                st.markdown("#### Scheduled Tasksets")
                tasksets = [
                    taskset
                    for taskset in maa_streamlit.globals.tasksets()
                    if taskset.profile == profile
                ]
                for taskset in tasksets:
                    col_name, col_schedule, col_start = st.columns(3)
                    with col_name:
                        st.markdown(f"**{taskset.name}**")
                    with col_schedule:

                        def handle_toggle_schedule(
                            taskset: maa_streamlit.data.TaskSet, key: str
                        ):
                            taskset.enabled = st.session_state[key]

                        if taskset.schedule:
                            key = f"{taskset.profile}/{taskset.name}/schedule"
                            st.toggle(
                                str(taskset.schedule),
                                on_change=handle_toggle_schedule,
                                args=(taskset, key),
                                key=key,
                                value=taskset.enabled,
                            )
                    with col_start:

                        def handle_start_taskset(
                            taskset: maa_streamlit.data.TaskSet,
                        ):
                            maa_streamlit.run_tasks(taskset.profile, taskset.tasks)
                            taskset.last_run = dt.datetime.now()

                        st.button(
                            "start",
                            on_click=handle_start_taskset,
                            args=(taskset,),
                            key=f"{taskset.profile}/{taskset.name}/start",
                        )
                    # add `*` to tasks with overriding params
                    tasks_display_names = [
                        str(task.name)
                        if (preset := maa_streamlit.globals.task_dict().get(task.name))
                        and task.params == preset.params
                        else task.name + "*"
                        for task in taskset.tasks
                    ]
                    with st.expander("..."):
                        for i, task in enumerate(taskset.tasks):
                            display_name = tasks_display_names[i]

                            def handle_toggle_task(
                                task: maa_streamlit.data.Task,
                                key: str,
                            ):
                                task.enabled = st.session_state[key]

                            key = f"{taskset.profile}/{taskset.name}/tasks/{task.name}"
                            st.toggle(
                                display_name,
                                value=task.enabled,
                                key=key,
                                on_change=handle_toggle_task,
                                args=(task, key),
                            )

            with col_log:
                st.markdown("#### Log")
                path = maa_streamlit.consts.MAA_STREAMLIT_STATE_DIR / f"{profile}.log"
                if path.exists():
                    st.code(
                        maa_streamlit.utils.last_n_lines(
                            path.read_text(encoding="utf-8"), 50
                        ),
                        language="log",
                    )

    def global_set_task_state(name, enabled):
        tasksets = maa_streamlit.globals.tasksets()
        for taskset in tasksets:
            for task in taskset.tasks:
                if task.name == name:
                    task.enabled = enabled

    st.divider()

    st.markdown("#### Global Controls")

    st.button(
        "Use fight_event",
        key="use_fight_event",
        on_click=lambda: (
            global_set_task_state("fight_event", True),
            global_set_task_state("fight_auto", False),
            global_set_task_state("fight_last", False),
        ),
    )

    st.button(
        "Use fight_auto",
        key="use_fight_auto",
        on_click=lambda: (
            global_set_task_state("fight_event", False),
            global_set_task_state("fight_auto", True),
            global_set_task_state("fight_last", False),
        ),
    )

    st.button(
        "Use fight_last",
        key="use_fight_last",
        on_click=lambda: (
            global_set_task_state("fight_event", False),
            global_set_task_state("fight_auto", False),
            global_set_task_state("fight_last", True),
        ),
    )
