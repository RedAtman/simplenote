from dataclasses import dataclass, field
import logging
import time
from typing import Dict, List, Optional, TypedDict
import uuid

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
    systemTags: List[str] = field(default_factory=list)
    content: str = ""
    publishURL: str = ""
    modificationDate: float = field(default_factory=time.time)
    creationDate: float = field(default_factory=time.time)


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
    id: str = uuid.uuid4().hex
    v: int = 0
    d: _Note = field(default_factory=_Note)

    modifydate: float = 0
    createdate: float = 0
    systemtags: List[str] = field(default_factory=list)
    needs_update: Optional[bool] = None
    local_modifydate: float = field(default_factory=time.time)
    filename: Optional[str] = None

    def _add_extra_fields(self):
        self.modifydate = self.d.modificationDate
        self.createdate = self.d.creationDate
        self.systemtags = self.d.systemTags

    def __post_init__(self):
        if isinstance(self.d, dict):
            d = _Note(**self.d)
            self.d = d
        self._add_extra_fields()

    def _nest_dict(self) -> Dict:
        result = self.__dict__
        result["d"] = self.d.__dict__
        return result

    def __eq__(self, value: "Note") -> bool:
        return self.id == value.id

    @staticmethod
    def index(limit: int = 1000, data: bool = True) -> List["Note"]:
        status, msg, result = API.index(limit, data)
        assert status == 0, msg
        assert isinstance(result, dict)
        assert "index" in result
        _notes = result.get("index", [])
        assert isinstance(_notes, list)
        return [Note(**note) for note in _notes]

    @staticmethod
    def retrieve(note_id: str) -> "Note":
        status, msg, _note = API.retrieve(note_id)
        assert status == 0, msg
        assert isinstance(_note, dict)
        return Note(**_note)

    def create(self) -> "Note":
        self.d.creationDate = time.time()
        status, msg, _note = API.modify(self.d.__dict__, self.id)
        assert status == 0, msg
        assert isinstance(_note, dict)
        assert self.id == _note["id"]
        return self

    def modify(self, version: Optional[int] = None) -> "Note":
        # TODO: maybe do not need to update the modificationDate here
        self.d.modificationDate = time.time()
        status, msg, _note = API.modify(self.d.__dict__, self.id, version)
        assert status == 0, msg
        assert isinstance(_note, dict)
        self = Note(**_note)
        return self

    @classmethod
    def _trash(cls, note_id: str) -> "Note":
        status, msg, _note = API.trash(note_id)
        assert status == 0, msg
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
        status, msg, _note = API.modify(self.d.__dict__, self.id)
        assert status == 0, "Error deleting note"
        assert isinstance(_note, dict)
        self = Note(**_note)
        return self

    def delete(self) -> "Note":
        status, msg, _note = API.delete(self.id)
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
