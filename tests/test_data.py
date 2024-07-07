import maa_streamlit.data


def test_load_task_with_name():
    task = maa_streamlit.data.Task.from_name("roguelike_sami_invest")
    assert task.type == "Roguelike"
    assert task.name == "roguelike_sami_invest"
    assert task.params != {}


def test_load_task_in_taskset():
    task = maa_streamlit.data.Task.from_dict({"_use": "roguelike_sami_invest"})
    assert task.type == "Roguelike"
    assert task.name == "roguelike_sami_invest"
    assert task.params != {}


def test_override():
    task = maa_streamlit.data.Task.from_dict(
        {"_use": "mall", "params": {"blacklist": []}}
    )
    assert task.params["blacklist"] == []
    assert (
        task.params["buy_first"]
        == maa_streamlit.data.Task.from_name("mall").params["buy_first"]
    )


def test_load_tasks():
    tasks = maa_streamlit.data.load_all_tasks()
    assert tasks


def test_load_tasksets():
    tasksets = maa_streamlit.data.load_all_tasksets()
    assert tasksets
    assert len(tasksets[0].tasks) > 0


def test_tasks_schedule():
    tasksets = maa_streamlit.data.load_all_tasksets()
    # at least one taskset has schedule
    at_least_one = False
    for taskset in tasksets:
        if taskset.schedule:
            at_least_one = True
    assert at_least_one


def test_taskset_tasks_independence():
    tasksets = maa_streamlit.data.load_all_tasksets()
    assert tasksets[0].tasks[0].name == tasksets[1].tasks[0].name
    tasksets[0].tasks[0].enabled = False
    assert tasksets[1].tasks[0].enabled


def test_load_profiles():
    profiles = maa_streamlit.data.load_all_profiles()
    print(profiles)
