from utils.patterns.singleton.base import Singleton
from utils.tools import Json2Obj


Settings = type(
    "Settings",
    (
        Json2Obj,
        Singleton,
    ),
    {},
)
