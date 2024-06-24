from dataclasses import dataclass, field
import logging
import time
from typing import Dict, List, Optional, TypedDict
import uuid

from _config import CONFIG
from api import Simplenote


# from typing_extensions import Unpack


logger = logging.getLogger()

API = Simplenote()


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
    needs_update: Optional[bool] = None
    local_modifydate: float = field(default_factory=time.time)
    filename: Optional[str] = None

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
        if self.id is None:
            self.id = uuid.uuid4().hex
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

    # def __getattribute__(self, name: str) -> Any:
    #     value = None
    #     try:
    #         value = super().__getattribute__(name)
    #     except AttributeError:
    #         value = getattr(self.d, name)
    #     # print(f"__getattribute__({name})", value)
    #     return value

    @staticmethod
    def index(limit: int = CONFIG.NOTE_FETCH_LENGTH, data: bool = True) -> List["Note"]:
        status, result = API.index(limit, data)
        assert status == 0
        assert isinstance(result, dict)
        assert "index" in result
        _notes = result.get("index", [])
        assert status == 0, "Error retrieving notes"
        assert isinstance(_notes, list)
        logger.warning(_notes)
        return [Note(**note) for note in _notes]

    @staticmethod
    def retrieve(note_id: str) -> "Note":
        status, _note = API.retrieve(note_id)
        assert status == 0, "Error retrieving note"
        assert isinstance(_note, dict)
        return Note(**_note)

    def create(self) -> "Note":
        self.d.creationDate = time.time()
        status, _note = API.modify(self.d.__dict__, self.id)
        assert status == 0, "Error creating note"
        assert isinstance(_note, dict)
        return self

    # def update(self, **kwargs: Unpack[NoteType]):
    def modify(self, version: Optional[int] = None) -> "Note":
        # note = _Note(**kwargs)
        # TODO: maybe do not need to update the modificationDate here
        self.d.modificationDate = time.time()
        # self.d.content += "\n\n" + kwargs.get("content", "")
        status, _note = API.modify(self.d.__dict__, self.id, version)
        assert status == 0, "Error updating note"
        assert isinstance(_note, dict)
        self = Note(**_note)
        return self

    @classmethod
    def _trash(cls, note_id: str) -> "Note":
        status, _note = API.trash(note_id)
        assert status == 0, "Error deleting note"
        assert isinstance(_note, dict)
        return Note(**_note)

    def trash(self) -> "Note":
        assert not self.id is None, "Note id is None"
        return self._trash(self.id)
        self.d.deleted = True
        self.d.modificationDate = time.time()
        status, _note = API.modify(self.d.__dict__, self.id)
        assert status == 0, "Error deleting note"
        assert isinstance(_note, dict)
        self = Note(**_note)
        return self

    def restore(self) -> "Note":
        self.d.deleted = False
        self.d.modificationDate = time.time()
        status, _note = API.modify(self.d.__dict__, self.id)
        assert status == 0, "Error deleting note"
        assert isinstance(_note, dict)
        self = Note(**_note)
        return self

    def delete(self) -> "Note":
        status, _note = API.delete(self.id)
        assert status == 0, "Error deleting note"
        assert isinstance(_note, dict)
        self = Note(**_note)
        return self


if __name__ == "__main__":
    _now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    note = Note(d={"content": _now})
    print(note.create())
    print(note.modify(content="new content"))
    print(note._nest_dict())
    print(Note.__dict__)
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
    print(note.__dataclass_fields__)
    # print(note.d.__dataclass_params__)
    # note.d.tags = ["tag3", "tag4"]
