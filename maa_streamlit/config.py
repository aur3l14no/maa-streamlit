import datetime as dt
import pathlib
from typing import Any, List, Optional

import tomllib
from deepmerge import always_merger
from pydantic import BaseModel, model_validator

CONFIG_DIR = pathlib.Path("config")


class Task(BaseModel):
    name: str
    type: str
    params: dict = {}

    @model_validator(mode="before")
    @classmethod
    def handle_use(cls, data: Any) -> Any:
        """When `data` has a `use` field, load that used task."""
        if isinstance(data, dict) and "use" in data:
            path = pathlib.Path(CONFIG_DIR / f"tasks/{data['use']}.toml")
            toml = tomllib.loads(path.read_text())
            # priority: data > toml
            data = always_merger.merge(toml, data)
            if "name" not in data:
                data["name"] = data["use"]
        return data

    @classmethod
    def load(cls, name):
        return cls.model_validate({"use": name})


class TaskSet(BaseModel):
    class AsstConfig(BaseModel):
        address: str

    name: str
    tasks: List[Task]
    asst: AsstConfig
    schedule: Optional[dt.time] = None
    enable: bool = False


def load_all_tasks() -> List[Task]:
    tasks = []
    for path in (CONFIG_DIR / "tasks").glob("*.toml"):
        name = path.with_suffix("").name
        tasks.append(Task.load(name))
    return tasks


def load_all_tasksets() -> List[TaskSet]:
    tasksets = []
    for path in (CONFIG_DIR / "tasksets").glob("*.toml"):
        toml = tomllib.loads(path.read_text())
        if "name" not in toml:
            toml["name"] = path.with_suffix("").name
        tasksets.append(TaskSet.model_validate(toml))
    return tasksets
