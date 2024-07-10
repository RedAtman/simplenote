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
    mapper_path_note: ClassVar[WeakValueDictionary[str, "Note"]] = WeakValueDictionary()

    id: str = field(default_factory=lambda: uuid4().hex)
    v: int = 0
    d: _Note = field(default_factory=_Note)

    modifydate: float = 0
    systemtags: List[str] = field(default_factory=list)

    _content: str = field(default_factory=str)
    _view: Any = field(default_factory=str)

    def __new__(cls, id: str = "", **kwargs):
        if not id:
            id = uuid4().hex

        if id not in Note.mapper_id_note:
            instance = super().__new__(cls)
            Note.mapper_id_note[id] = instance
            instance.__dict__["__kwargs"] = kwargs
            return instance
        instance = Note.mapper_id_note[id]
        # kwargs["_content"] = getattr(instance, "_content", "")
        kwargs["_content"] = getattr(instance, "_content", "")
        kwargs["_view"] = getattr(instance, "_view", "")
        # logger.info((getattr(instance, "_content", "")))
        # logger.info(instance)
        # logger.info(kwargs)
        instance.__dict__.update(kwargs)
        # kwargs["id"] = id
        # logger.info(instance.__dict__.keys())
        logger.info(instance)
        logger.info(kwargs)
        instance.__dict__["__kwargs"] = kwargs
        return instance

    def __post_init__(self, **kwargs):
        if isinstance(self.d, dict):
            d = _Note(**self.d)
            self.d = d
        self._add_extra_fields()

    def _add_extra_fields(self):
        logger.info((id(self), self))
        self.modifydate = self.d.modificationDate
        self.systemtags = self.d.systemTags
        self._content = self.__dict__["__kwargs"].get("_content", "")
        self._view = self.__dict__["__kwargs"].get("_view", "")
        # logger.info((id(self), self))

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
    def need_flush(self) -> bool:
        # if not self._content:
        #     self._content = self.d.content
        return self._content != self.d.content

    def flush(self):
        self._content = self.d.content

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str):
        # self._content = value
        self.d.content = value

    @property
    def _title(self):
        # if self._content is None:
        #     self._content = self.d.content
        try:
            content = self._content
        except Exception:
            return SIMPLENOTE_DEFAULT_NOTE_TITLE
        return self.get_title(content)

    @property
    def title(self):
        try:
            content = self.content
        except Exception:
            return SIMPLENOTE_DEFAULT_NOTE_TITLE
        return self.get_title(content)

    @staticmethod
    def get_title(content: str) -> str:
        index = content.find("\n")
        if index > -1:
            title = content[:index]
        else:
            if content:
                title = content
            else:
                title = SIMPLENOTE_DEFAULT_NOTE_TITLE
        return title

    @property
    def _filename(self) -> str:
        return self.get_filename(self.id, self._title)

    @property
    def filename(self) -> str:
        filename = self.get_filename(self.id, self.title)
        # logger.info((filename, self._filename))
        # logger.info((id(self), self))
        return filename
        # if self._filename is None:
        #     self._filename = filename
        #     # TODO: self.open()
        #     return self._filename
        if self._filename != filename:
            # self.on_open_filename_change()
            self._close(self._filename)
            self._filename = filename
            self.write_content_to_path(filename, self.d.content)
            Note.mapper_path_note[filename] = self
        return self._filename

    # @filename.setter
    # def filename(self, value: str):
    #     self._filename = value

    @staticmethod
    def get_filename(id: str, title: str) -> str:
        title_extension_map: List[Dict[str, str]] = SETTINGS.get("title_extension_map")
        assert isinstance(title_extension_map, list), f"Invalid title_extension_map: {title_extension_map}"
        base = "".join(c for c in title if c in VALID_CHARS)
        # Determine extension based on title
        extension = ""
        if title_extension_map:
            for item in title_extension_map:
                pattern = re.compile(item["title_regex"], re.UNICODE)
                if re.search(pattern, title):
                    extension = "." + item["extension"]
                    break
        return base + " (" + id + ")" + extension

    @property
    def _filepath(self) -> str:
        return self.get_filepath(self._filename)

    @property
    def filepath(self) -> str:
        return self.get_filepath(self.filename)
        filename = self._filename
        if not filename:
            filename = self.filename
        return self.get_filepath(filename)

    @staticmethod
    def get_filepath(filename: str):
        return os.path.join(SIMPLENOTE_TEMP_PATH, filename)

    @staticmethod
    def write_content_to_path(filepath: str, content: str = ""):
        with open(filepath, "wb") as f:
            try:
                f.write(content.encode("utf-8"))
            except Exception as err:
                logger.exception(err)
                raise err

    # @classmethod
    # def _open(cls, filepath: str):
    #     # cls.write_content_to_path(
    #     #     filepath,
    #     # )
    #     Note.mapper_path_note[filepath] = self
    #     return filepath

    def open(self):
        filepath = self.filepath
        self.write_content_to_path(filepath, self.content)
        # Note.mapper_path_note[filepath] = self
        return filepath

    @staticmethod
    def _close(filepath: str):
        if not filepath:
            return
        # del Note.mapper_path_note[filepath]
        try:
            os.remove(filepath)
        except OSError as err:
            logger.exception(err)

    def close(self):
        self._close(self.filepath)

    @staticmethod
    def get_note_from_filepath(view_absolute_filepath: str):
        assert isinstance(view_absolute_filepath, str), "view_absolute_filepath must be a string"
        view_note_dir, view_note_filename = os.path.split(view_absolute_filepath)
        # logger.info(("view_note_filename", view_note_dir, view_note_filename))
        if view_note_dir != SIMPLENOTE_TEMP_PATH:
            return
        pattern = re.compile(r"\((.*?)\)")
        for note in Note.mapper_id_note.values():
            if note.filename == view_note_filename:
                return note

        # TODO: maybe results include more than one
        results = re.findall(pattern, view_note_filename)
        # logger.info(("results", results))
        if results:
            note_id = results[len(results) - 1]
            # logger.info(note_id)
            return Note.mapper_id_note[note_id]
        return


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
