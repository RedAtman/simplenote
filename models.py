from dataclasses import dataclass, field
import logging
import time
from typing import Any, Dict, List, Optional, TypedDict


# from typing_extensions import Unpack


logger = logging.getLogger()


@dataclass
class _Note:
    """Data class for a note object"""

    tags: List[str] = field(default_factory=list)
    deleted: bool = False
    shareURL: str = ""
    publishURL: str = ""
    content: str = ""
    systemTags: List[str] = field(default_factory=list)
    modificationDate: float = field(default_factory=time.time)
    creationDate: float = field(default_factory=time.time)

    key: Optional[str] = ""
    version: int = 0
    modifydate: float = 0
    createdate: float = 0
    systemtags: List[str] = field(default_factory=list)

    def __post_init__(self):
        self._add_simplenote_api_fields()

    def _add_simplenote_api_fields(self):
        self.modifydate = self.modificationDate
        self.createdate = self.creationDate
        self.systemtags = self.systemTags

    # def __setattr__(self, name: str, value: Any) -> None:
    #     if name in ["content", "tags", "systemTags"]:
    #         self.modificationDate = time.time()
    #         API.modify(self.__dict__)
    #     super().__setattr__(name, value)

    # @property
    # def key(self):
    #     if self._key:
    #         return self._key
    #     return self.id

    # @key.setter
    # def key(self, value):
    #     # self._key = uuid.uuid4().hex
    #     assert isinstance(value, str), "value is not a string: %s" % value
    #     assert len(value) == 32, "value length is not 32: %s" % value
    #     self._key = value

    # @property
    # def version(self):
    #     if self._version:
    #         return self._version
    #     return self.v

    # @version.setter
    # def version(self, value: int):
    #     self._version = value


class NoteType(TypedDict):
    tags: List[str]
    deleted: bool
    shareURL: str
    systemTags: List[str]
    content: str
    publishURL: str
    modificationDate: float
    creationDate: float


@dataclass
class Note:
    v: int = 0
    d: _Note = field(default_factory=_Note)
    id: Optional[str] = None

    def _add_simplenote_api_fields(self):
        self.d.key = self.id
        self.d.version = self.v

    def __post_init__(self):
        # print((type(self.d), self.d))
        if isinstance(self.d, dict):
            d = _Note(**self.d)
            # status, note = API.modify(self.d.__dict__)
            # logger.info((status, note))
            # assert status == 0, "Error Create note"
            # assert isinstance(note, dict)
            self.d = d
        self._add_simplenote_api_fields()

    def _nest_dict(self) -> Dict:
        result = self.__dict__
        result["d"] = self.d.__dict__
        return result

    def __eq__(self, value: "Note") -> bool:
        return self.id == value.id and self.v == value.v

    # def __setattr__(self, name: str, value: Any) -> None:
    #     print(f"__setattr__({name}, {value})")
    #     super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        value = None
        try:
            value = super().__getattribute__(name)
        except AttributeError:
            value = getattr(self.d, name)
        # print(f"__getattribute__({name})", value)
        return value

    # def update(self, **kwargs: Unpack[NoteType]):
    # def update(self, **kwargs):
    #     note = _Note(**kwargs)
    #     # TODO: maybe do not need to update the modificationDate here
    #     note.modificationDate = time.time()
    #     _note, status = API.update_note(note.__dict__)
    #     assert status == 0, "Error updating note"
    #     assert isinstance(_note, dict)
    #     self.d = note


if __name__ == "__main__":
    empty_note = Note(v=1)
    print(empty_note)
    print(empty_note.__dict__)
    print(empty_note._nest_dict())
    note = {
        # "id": "1",
        "v": 1,
        "d": {
            "tags": ["tag1", "tag2"],
            "deleted": False,
            "shareURL": "",
            "systemTags": ["systemtag1", "systemtag2"],
            "content": "content",
            "publishURL": "",
            "modificationDate": 0,
            "creationDate": 0,
        },
    }
    note = Note(**note)
    print(note)
    # print(note.id)
    print(note.d)
    # print(note.d.tags)
    # print(note.tags)
    # print(type(note.__dict__), note.__dict__)
    # print(note.d.__dict__)
    # print(note.d.__annotations__)
    # print(note.__annotations__)
    # print(note.d.__dataclass_fields__)
    # print(note.__dataclass_fields__)
    # print(note.d.__dataclass_params__)
    # note.d.tags = ["tag3", "tag4"]
