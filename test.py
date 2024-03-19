from attrs import define, field
from cattrs import Converter, register_structure_hook, structure
from cattrs.gen import make_dict_structure_fn
from deepmerge import Merger

# only dicts got merged (in our case, it should be params)
my_merger = Merger(
    [(dict, ["merge"])],
    ["override"],
    ["override"],
)

converter = Converter()


def fallback_field(converter_arg: Converter, old_to_new_field: dict[str, str]):
    def decorator(cls):
        struct = make_dict_structure_fn(cls, converter_arg)

        def structure(d, cl):
            for k, v in old_to_new_field.items():
                if k in d:
                    d[v] = d[k]

            return struct(d, cl)

        converter_arg.register_structure_hook(cls, structure)

        return cls

    return decorator


@fallback_field(converter, {"old_field": "new_field"})
@define
class MyInternalAttr:
    new_field: str


@define(frozen=True)
class Task:
    name: str | None = None
    type: str | None = None
    params: dict = {}
    _use: str | None = field(repr=False, default=None)


def func(d, cl):
    if "_use" in d.keys():
        b = {"name": "used"}
        d = my_merger.merge(b, d)
        del d["_use"]
    return cl(**d)


register_structure_hook(Task, func)

print(structure({"_use": "haha"}, Task))
print(structure({"name": "name"}, Task))
