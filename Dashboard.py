import hmac

import streamlit as st
from streamlit_autorefresh import st_autorefresh

import maa_streamlit

st.set_page_config(
    page_title="MaaS",
    page_icon="⛵︎",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Auth
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.


@st.cache_resource
def init_maa_streamlit():
    maa_streamlit.init()


init_maa_streamlit()

_ = st_autorefresh(10_000, key="dashboard_refresher")

st.title("Live Dashboard")

for device in maa_streamlit.globals.managed_devices():
    st.markdown(f"## {device}")
    asst = maa_streamlit.globals.asst_dict()[device]
    adb_proxy = maa_streamlit.globals.adb_proxy_dict()[device]

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
                on_click=lambda asst, adb_proxy: (asst.stop(), adb_proxy.force_close()),
                args=(asst, adb_proxy),
            )

        # MAA CTRL
        col_label, col_status, col_stop = st.columns(3)
        with col_label:
            st.markdown("🤖 **maa**")
        with col_status:
            st.markdown("🟩" if asst.running() else "🟥")
        with col_stop:
            st.button(
                "stop",
                key=f"{device}/maa/stop",
                on_click=lambda asst: asst.stop(),
                args=(asst,),
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
            if taskset.asst.address == device
        ]
        # TODO allow dynamic config?
        for taskset in tasksets:
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
                f"{'🟩' if taskset.enable else '🟥'} **[{taskset.name}] @ {taskset.schedule}**\n\n"
                f"last: {maa_streamlit.schedule.scheduled_tasks_stats_dict()[taskset.name]}\n\n"
                f"{' | '.join([task.name if task.params == maa_streamlit.globals.task_dict()[task.name].params else task.name + '*' for task in taskset.tasks])}"
            )

    with col_log:
        st.markdown("#### Log")
        path = maa_streamlit.consts.MAA_STREAMLIT_STATE_DIR / f"{device}.log"
        if path.exists():
            st.code(
                maa_streamlit.utils.last_n_lines(path.read_text(), 30), language="log"
            )
        else:
            st.code("")
