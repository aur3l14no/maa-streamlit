import datetime as dt
import pathlib
from typing import Any, List, Optional

import tomllib
from deepmerge import Merger
from pydantic import BaseModel, model_validator

CONFIG_DIR = pathlib.Path("config")

# only dicts got merged (in our case, it should be params)
my_merger = Merger(
    [(dict, ["merge"])],
    ["override"],
    ["override"],
)


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
            data = my_merger.merge(toml, data)
            if "name" not in data:
                data["name"] = data["use"]
        return data

    @classmethod
    def load(cls, name):
        return cls.model_validate({"use": name})


class Device(BaseModel):
    name: str
    address: str
    config: str  # https://github.com/MaaAssistantArknights/MaaAssistantArknights/edit/dev/resource/config.json

    def __key(self):
        return (self.name, self.address, self.config)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Device):
            return self.__key() == other.__key()
        return NotImplemented


class TaskSet(BaseModel):
    name: str
    tasks: List[Task]
    device: Device
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
