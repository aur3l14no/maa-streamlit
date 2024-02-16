import maa_streamlit.config


def test_load_task_with_name():
    task = maa_streamlit.config.Task.load("roguelike_phantom")
    assert task.type == "Roguelike"
    assert task.name == "roguelike_phantom"
    assert task.params != {}


def test_load_task_in_taskset():
    d = {"use": "roguelike_phantom"}
    task = maa_streamlit.config.Task.model_validate(d)
    assert task.type == "Roguelike"
    assert task.name == "roguelike_phantom"
    assert task.params != {}

    d = {"use": "roguelike_phantom", "name": "newname!", "params": {"theme": "Sami"}}
    task = maa_streamlit.config.Task.model_validate(d)
    assert task.type == "Roguelike"
    assert task.name == "newname!"
    assert task.params["theme"] == "Sami"
    assert len(task.params.keys()) > 1


def test_override():
    d = {"use": "mall", "params": {"blacklist": []}}
    task = maa_streamlit.config.Task.model_validate(d)
    assert task.params["blacklist"] == []
    assert (
        task.params["buy_first"]
        == maa_streamlit.config.Task.load("mall").params["buy_first"]
    )


def test_load_tasks():
    tasks = maa_streamlit.config.load_all_tasks()
    assert tasks


def test_load_tasksets():
    tasksets = maa_streamlit.config.load_all_tasksets()
    assert tasksets
