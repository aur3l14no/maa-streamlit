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
class Connection:
    device: str
    adb_path: str = "adb"
    config: str = "General"


# @define(frozen=True, eq=True)
# class ConnectionExtra:
#     index: int
#     display: int


@define(frozen=True, eq=True)
class InstanceOptions:
    touch_mode: str


@define(frozen=True, eq=True)
class StaticOptions:
    cpu_ocr: bool
    gpu_ocr: str


@define(frozen=True, eq=True)
class Profile:
    name: str
    connection: Connection
    instance_options: InstanceOptions
    static_options: StaticOptions
    connection_extras: dict | None = None


@define(order=True)
class TaskSet:
    name: str
    profile: str  # name
    tasks: list[Task] = field(order=False)
    enabled: bool = field(default=False, order=False)
    schedule: dt.time | None = None

    last_run: dt.datetime | None = field(order=False, default=None)


# cattrs
def structure_task(d: dict, cl):
    """Handle `_use`."""
    if use := d.get("_use"):
        path = pathlib.Path(CONFIG_DIR / f"tasks/{use}.toml")
        toml = tomllib.loads(path.read_text(encoding="utf-8"))
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
def load_all_profiles() -> dict[Profile]:
    profiles = {}
    for path in (CONFIG_DIR / "profiles").glob("*.toml"):
        toml = tomllib.loads(path.read_text(encoding="utf-8"))
        if "name" not in toml:
            toml["name"] = path.with_suffix("").name
        profiles[toml["name"]] = structure(toml, Profile)
    return profiles


def load_all_tasks() -> list[Task]:
    tasks = []
    for path in (CONFIG_DIR / "tasks").glob("*.toml"):
        name = path.with_suffix("").name
        tasks.append(Task.from_name(name))
    return tasks


def load_all_tasksets() -> list[TaskSet]:
    tasksets = []
    for path in (CONFIG_DIR / "tasksets").glob("*.toml"):
        toml = tomllib.loads(path.read_text(encoding="utf-8"))
        if "name" not in toml:
            toml["name"] = path.with_suffix("").name
        tasksets.append(structure(toml, TaskSet))
    return tasksets
