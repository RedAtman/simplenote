import json
import logging
import re
import sys
import time

# import mimetypes
from typing import Any, Dict


try:
    from typing import TypeVar
except ImportError:
    from typing_extensions import TypeVar


__all__ = [
    "Dict2Obj",
    "Json2Obj",
    # "is_media",
    "loading_bar",
    "progressbar",
]

logger = logging.getLogger()


# class Dict2Obj:
#     '''Convert dict to object recursively.'''
#     def __init__(self, data):
#         for name, value in data.items():
#             setattr(self, name, self.__wrap(value))

#     def __wrap(self, value):
#         if isinstance(value, (tuple, list, set, frozenset)):
#             return type(value)([self.__wrap(v) for v in value])
#         return Dict2Obj(value) if isinstance(value, dict) else value

#     def _dict(self):
#         return {k: v._dict() if isinstance(v, Dict2Obj) else v
#                 for k, v in self.__dict__.items()}

_VT = TypeVar("_VT")


class Dict2Obj(dict):

    def __init__(self: Dict[str, _VT], **kwargs: _VT) -> None:
        super().__init__(**kwargs)
        self.__dict__ = self

    # def __init__(self, data: Union[dict, "Dict2Obj"]) -> None:
    #     if isinstance(data, Dict2Obj):
    #         data = data.__dict__
    #     for key, value in data.items():
    #         setattr(self, key, value)

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)

    def get(self, key: str, default: Any = None) -> Any:
        return super().get(key, default)


class Json2Obj(Dict2Obj):
    """Load and resolve json file to a Dict2Obj object."""

    def __init__(self: Dict[str, _VT], file: str) -> None:

        def __load(file: str) -> Dict[str, Any]:
            dict_obj: Dict[str, Any] = {}
            with open(file, "r") as fd:
                content = fd.read()
                assert content, "File(%s) is empty!" % file
                # remove comments and empty lines, then load json
                dict_obj: Dict[str, Any] = json.loads(re.sub("\\s//.*", "", content, flags=re.MULTILINE))
                assert isinstance(dict_obj, dict), "File(%s) is not a dict!" % file
            return dict_obj

        dict_obj = __load(file)
        super().__init__(**dict_obj)


# mimetypes.init()


# def is_media(file: str, include_type: List[str] = ["image", "audio", "video"]):
#     """Check if the file is a media file."""
#     mime_start = mimetypes.guess_type(file)[0]
#     if mime_start is not None:
#         mime_start = mime_start.split("/")[0]
#         if mime_start in include_type:
#             return True
#     return False


def loading_bar(count, total, size):
    """Use `sys.stdout.write` to print the loading bar.

    Arguments:
        count {[int]} -- [Current count]
        total {[int]} -- [Total count]
        size {[int]} -- [Size of the loading bar]

    Usage:
        for i in range(0, 100):
            loading_bar(i, 100, 2)
            time.sleep(.1)
    Example:
        001/100 [==========] 100%
    """
    percent = float(count) / float(total) * 100
    sys.stdout.write(
        "\r"
        + str(int(count)).rjust(3, "0")
        + "/"
        + str(int(total)).rjust(3, "0")
        + " ["
        + "=" * int(percent / 10) * size
        + " " * (10 - int(percent / 10)) * size
        + "]"
    )


def progressbar(count: int):
    """Use `sys.stdout.write` to print the progress bar.

    Arguments:
        count {int} -- [Current count]

    Usage:
        for i in progressbar(100):
            time.sleep(0.1)
    Example:
        [##########] - 10/10
    """
    for current in range(count):
        print(
            f"[{current * '#'}{(count - 1 - current)*' '}] - {current + current}/{count}",
            end="\r",
        )
        yield current
    print("\n")


if __name__ == "__main__":
    kwargs = {"a": 1, "b": 2, "c": 3}
    d = Dict2Obj(**kwargs)
    print(d)
    print(d.a)
    print(d["a"])
    print(d.get("a"))
    assert d.a == 1
    assert False
    import time

    for i in progressbar(10):
        time.sleep(0.1)

    loading_bar(5, 10, 2)
    for i in range(0, 10):
        loading_bar(i, 10, 2)
        time.sleep(0.1)
