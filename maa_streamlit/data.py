import datetime as dt
import pathlib

import tomllib
from attrs import define, field
from cattrs import register_structure_hook, structure
from deepmerge import Merger

CONFIG_DIR = pathlib.Path("config")

# only dicts got merged (in our case, it should be params)
my_merger = Merger(
    [(dict, ["merge"])],
    ["override"],
    ["override"],
)


@define
class Task:
    """Task. Usually built from dict like
    ```
    { "name": "hooray", "type": "fight", "params": {}, use: "fight_ap_5" }
    ```
    where `_use` instructs the loader to use `config_dir/tasks/xxx`
    """

    name: str
    type: str
    params: dict = {}
    enabled: bool = True
    _use: str | None = field(repr=False, default=None)

    @classmethod
    def from_name(cls, name):
        return structure({"_use": name}, cls)

    @classmethod
    def from_dict(cls, dict):
        return structure(dict, cls)


@define(frozen=True, eq=True)
class Device:
    name: str
    address: str
    config: str  # https://github.com/MaaAssistantArknights/MaaAssistantArknights/edit/dev/resource/config.json


@define(order=True)
class TaskSet:
    name: str
    device: Device
    tasks: list[Task] = field(order=False)
    enabled: bool = field(default=False, order=False)
    schedule: dt.time | None = None

    last_run: dt.datetime | None = field(order=False, default=None)


# cattrs
def structure_task(d: dict, cl):
    """Handle `_use`."""
    if use := d.get("_use"):
        path = pathlib.Path(CONFIG_DIR / f"tasks/{use}.toml")
        toml = tomllib.loads(path.read_text())
        d = my_merger.merge(toml, d)
        if "name" not in d:
            d["name"] = use
        del d["_use"]
    return cl(**d)


register_structure_hook(Task, structure_task)
register_structure_hook(
    dt.time, lambda time, _: dt.datetime.strptime(time, "%H:%M:%S").time()
)


# loaders
def load_all_tasks() -> list[Task]:
    tasks = []
    for path in (CONFIG_DIR / "tasks").glob("*.toml"):
        name = path.with_suffix("").name
        tasks.append(Task.from_name(name))
    return tasks


def load_all_tasksets() -> list[TaskSet]:
    tasksets = []
    for path in (CONFIG_DIR / "tasksets").glob("*.toml"):
        toml = tomllib.loads(path.read_text())
        if "name" not in toml:
            toml["name"] = path.with_suffix("").name
        tasksets.append(structure(toml, TaskSet))
    return tasksets
