from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
import logging
import os
import re
import string
import time
from typing import Any, ClassVar, Dict, List, Optional, TypedDict
from uuid import uuid4
from weakref import WeakValueDictionary

from settings import Settings
import sublime


# from typing_extensions import Unpack


logger = logging.getLogger()


SIMPLENOTE_DEFAULT_NOTE_TITLE = os.environ.get("SIMPLENOTE_DEFAULT_NOTE_TITLE", "untitled")
SIMPLENOTE_BASE_DIR = os.environ.get("SIMPLENOTE_BASE_DIR", os.path.abspath(os.path.dirname(__file__)))
SIMPLENOTE_TEMP_PATH = os.path.join(SIMPLENOTE_BASE_DIR, "temp")
_SIMPLENOTE_SETTINGS_FILE = os.environ.get("SIMPLENOTE_SETTINGS_FILE", "simplenote.sublime-settings")
SIMPLENOTE_SETTINGS_FILE = os.path.join(SIMPLENOTE_BASE_DIR, _SIMPLENOTE_SETTINGS_FILE)
SETTINGS = Settings(SIMPLENOTE_SETTINGS_FILE)
# api = import_module("api")
from api import Simplenote


# Take out invalid characters from title and use that as base for the name
VALID_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)
API = Simplenote(SETTINGS.username, SETTINGS.password)
logger.warning((API, API.token))


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
    mapper_id_note: ClassVar[WeakValueDictionary[str, "Note"]] = WeakValueDictionary()

    id: str = field(default_factory=lambda: uuid4().hex)
    v: int = 0
    d: _Note = field(default_factory=_Note)

    modifydate: float = 0
    createdate: float = 0
    systemtags: List[str] = field(default_factory=list)
    needs_update: Optional[bool] = None
    local_modifydate: float = field(default_factory=time.time)
    filename: Optional[str] = None

    def __new__(cls, id: str = "", **kwargs):
        if not id:
            id = uuid4().hex

        if id not in Note.mapper_id_note:
            instance = super().__new__(cls)
            Note.mapper_id_note[id] = instance
        return Note.mapper_id_note[id]

    def _add_extra_fields(self):
        self.modifydate = self.d.modificationDate
        self.createdate = self.d.creationDate
        self.systemtags = self.d.systemTags

    def __post_init__(self):
        if isinstance(self.d, dict):
            d = _Note(**self.d)
            self.d = d
        self._add_extra_fields()

    def _nest_dict(self) -> Dict[str, Any]:
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

    @property
    def title(self):
        try:
            content = self.d.content
        except Exception:
            return SIMPLENOTE_DEFAULT_NOTE_TITLE
        index = content.find("\n")
        if index > -1:
            title = content[:index]
        else:
            if content:
                title = content
            else:
                title = SIMPLENOTE_DEFAULT_NOTE_TITLE
        return title

    def _get_filename(self, title_extension_map: List[Dict[str, str]]) -> str:
        note_title = self.title
        base = "".join(c for c in note_title if c in VALID_CHARS)
        # Determine extension based on title
        extension = ""
        if title_extension_map:
            for item in title_extension_map:
                pattern = re.compile(item["title_regex"], re.UNICODE)
                if re.search(pattern, note_title):
                    extension = "." + item["extension"]
                    break
        return base + " (" + self.id + ")" + extension

    def get_filename(self):
        title_extension_map = SETTINGS.get("title_extension_map")
        assert isinstance(title_extension_map, list), f"Invalid title_extension_map: {title_extension_map}"
        filename = self._get_filename(title_extension_map)
        return filename

    def get_filepath(self):
        return os.path.join(SIMPLENOTE_TEMP_PATH, self.get_filename())

    def write_content_to_path(self, filepath: str):
        with open(filepath, "wb") as f:
            try:
                f.write(self.d.content.encode("utf-8"))
            except Exception as err:
                logger.exception(err)
                raise err

    def open(self, window: Optional[sublime.Window] = None):
        if not isinstance(window, sublime.Window):
            window: sublime.Window = sublime.active_window()
        filepath = self.get_filepath()
        assert isinstance(filepath, str)
        self.write_content_to_path(filepath)
        # Note.mapper_path_note[filepath] = self
        return window.open_file(filepath)


if __name__ == "__main__":
    from pprint import pprint

    import_module("_config")
    kwargs = {
        "id": uuid4().hex,
        "v": 1,
        "d": {
            "tags": [],
            "deleted": False,
            "shareURL": "",
            "systemTags": [],
            "content": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "publishURL": "",
            # "modificationDate": 0,
            # "creationDate": 0,
        },
    }
    note = Note(**kwargs)
    pprint(note.create())
    note.d.content = "new content"
    pprint(note.modify())
    pprint(note._nest_dict())
    pprint(Note.__dict__)
    empty_note = Note(v=1)
    pprint(empty_note)
    pprint(empty_note.__dict__)
    pprint(empty_note._nest_dict())
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
