from __future__ import annotations

import logging
import os
import re
import string
import time
from typing import Any, ClassVar, Dict, List, Optional, TypedDict
from uuid import uuid4

import sublime

from ._config import CONFIG
from .api import Simplenote
from .utils.decorator import class_property
from .utils.tree.redblacktree import rbtree as RedBlackTree


# from typing_extensions import Unpack


logger = logging.getLogger()


# Take out invalid characters from title and use that as base for the name
VALID_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)


class _Note:
    """Data class for a note object"""

    __serialize_fields = [
        "tags",
        "deleted",
        "shareURL",
        "systemTags",
        "content",
        "publishURL",
        "modificationDate",
        "creationDate",
    ]

    def __init__(
        self,
        _note: Optional[Note] = None,
        tags: Optional[List[str]] = None,
        deleted: bool = False,
        shareURL: str = "",
        systemTags: Optional[List[str]] = None,
        content: str = "",
        publishURL: str = "",
        modificationDate: float = 0,
        creationDate: float = 0,
    ):
        self._note: Optional[Note] = _note
        self.tags: List[str] = tags or []
        self.deleted: bool = deleted
        self.shareURL: str = shareURL
        self.systemTags: List[str] = systemTags or []
        self.content: str = content
        self.publishURL: str = publishURL
        self._modificationDate: float = modificationDate or time.time()
        self.creationDate: float = creationDate or time.time()
        setattr(self, "modificationDate", self._modificationDate)

    @property
    def modificationDate(self) -> float:
        return self._modificationDate

    @modificationDate.setter
    def modificationDate(self, value: float) -> None:
        # TODO:
        # logger.info(("@modificationDate.setter", value))
        # note = getattr(self, "_note", None)
        # if not isinstance(note, Note):
        #     raise Exception("modificationDate can only be set on Note objects, not %s" % type(note))
        # Note.tree.insert(value, note)
        self._modificationDate = value

    def _nest_dict(self) -> Dict[str, Any]:
        return {filed: getattr(self, filed) for filed in self.__serialize_fields}


class NoteType(TypedDict):
    tags: List[str]
    deleted: bool
    shareURL: str
    systemTags: List[str]
    content: str
    publishURL: str
    modificationDate: float
    creationDate: float


class Note:
    mapper_id_note: ClassVar[Dict[str, "Note"]] = dict()
    # TODO: use weakref
    # mapper_id_note: ClassVar[WeakValueDictionary[str, "Note"]] = WeakValueDictionary()
    tree: ClassVar[RedBlackTree] = RedBlackTree()

    def __new__(cls, id: str = "", **kwargs):
        if id not in Note.mapper_id_note:
            instance = super().__new__(cls)
            # TODO:
            instance.__dict__["_content"] = kwargs.get("d", {}).get("content", "")

            return instance
        instance = Note.mapper_id_note[id]
        return instance

    def __init__(self, id: str = "", v: int = 0, d: Dict[str, Any] = {}, **kwargs):
        if not isinstance(id, str) or len(id) not in (32, 36):
            logger.warning(("Note id %s is not a valid UUID", id, type(id), len(id)))
            id = str(uuid4())
        self.id: str = id
        Note.mapper_id_note[self.id] = self
        # Note.tree.remove(self.d.modificationDate)
        self.v: int = v
        _d = getattr(self, "d", None)
        if isinstance(_d, _Note):
            old_modificationDate = _d.modificationDate
            Note.tree.remove(old_modificationDate)
        d["_note"] = self
        self.d: _Note = _Note(**d)
        Note.tree.insert(self.d.modificationDate, self)
        # TODO:
        self._content = self.__dict__.get("_content", "")

    # TODO:
    # def __setattr__(self, name: str, value: Any) -> None:
    #     if name == "d":
    #         if isinstance(value, dict):
    #             value["_note"] = self
    #             value = _Note(**value)
    #     super().__setattr__(name, value)

    # TODO: use __eq__ to compare notes
    # def __eq__(self, value: "Note") -> bool:
    #     return self.d.modificationDate == value.d.modificationDate
    #     return self.id == value.id

    @class_property
    def API(cls) -> Simplenote:
        settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
        username = settings.get("username")
        password = settings.get("password")
        if not all([username, password]):
            raise Exception(
                "Missing username or password, Please check settings file: %s" % CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH
            )
        if not isinstance(username, str) or not isinstance(password, str):
            raise Exception(
                "username and password must be strings, Please check settings file: %s"
                % CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH
            )
        return Simplenote(username, password)

    @classmethod
    def index(cls, limit: int = 1000, data: bool = True) -> List["Note"]:
        result = cls.API.index(limit, data)
        assert isinstance(result, dict)
        assert "index" in result
        _notes = result.get("index", [])
        assert isinstance(_notes, list)
        return [Note(**note) for note in _notes]

    @classmethod
    def retrieve(cls, note_id: str) -> "Note":
        _note = cls.API.retrieve(note_id)
        assert isinstance(_note, dict)
        return Note(**_note)

    def create(self) -> "Note":
        _note = self.API.modify(self.d._nest_dict(), self.id)
        assert isinstance(_note, dict)
        assert self.id == _note["id"]
        return self

    def modify(self, version: Optional[int] = None) -> "Note":
        _note = self.API.modify(self.d._nest_dict(), self.id, version)
        assert isinstance(_note, dict)
        self = Note(**_note)
        return self

    @classmethod
    def _trash(cls, note_id: str) -> Dict[str, Any]:
        _note = cls.API.trash(note_id)
        assert isinstance(_note, dict)
        if note_id in Note.mapper_id_note:
            del Note.mapper_id_note[note_id]
        return _note

    def trash(self) -> Dict[str, Any]:
        assert not self.id is None, "Note id is None"
        return self._trash(self.id)

    def restore(self) -> "Note":
        self.d.deleted = False
        _note = self.API.modify(self.d._nest_dict(), self.id)
        assert isinstance(_note, dict)
        self = Note(**_note)
        return self

    def delete(self) -> "Note":
        _note = self.API.delete(self.id)
        assert isinstance(_note, dict)
        self = Note(**_note)
        return self

    @property
    def need_flush(self) -> bool:
        return self._content != self.d.content

    def flush(self):
        self._content = self.d.content

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str):
        self.d.content = value

    @property
    def _title(self):
        try:
            content = self._content
        except Exception:
            return CONFIG.SIMPLENOTE_DEFAULT_NOTE_TITLE
        return self.get_title(content)

    @property
    def title(self):
        try:
            content = self.d.content
        except Exception:
            return CONFIG.SIMPLENOTE_DEFAULT_NOTE_TITLE
        return self.get_title(content)

    @staticmethod
    def get_title(content: str) -> str:
        index = content.find("\n")
        if index > -1:
            title = content[:index]
        else:
            title = content or CONFIG.SIMPLENOTE_DEFAULT_NOTE_TITLE
        return title

    @property
    def _filename(self) -> str:
        return self.get_filename(self.id, self._title)

    @property
    def filename(self) -> str:
        filename = self.get_filename(self.id, self.title)
        return filename

    @staticmethod
    def get_filename(id: str, title: str) -> str:
        settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
        title_extension_map: List[Dict[str, str]] = settings.get("title_extension_map")
        if not isinstance(title_extension_map, list):
            logger.info(
                "`title_extension_map` must be a list. Please check settings file: %s."
                % CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH
            )
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

    @staticmethod
    def get_filepath(filename: str):
        return os.path.join(CONFIG.SIMPLENOTE_NOTES_DIR, filename)

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
    #     return filepath

    def open(self):
        filepath = self.filepath
        self.write_content_to_path(filepath, self.content)
        return filepath

    @staticmethod
    def _close(filepath: str):
        if not filepath:
            return
        try:
            os.remove(filepath)
        except (OSError, FileNotFoundError) as err:
            logger.exception(err)
        except Exception as err:
            logger.exception(err)

    def close(self):
        self._close(self.filepath)

    @staticmethod
    def get_note_from_filepath(view_absolute_filepath: str):
        assert isinstance(view_absolute_filepath, str), "view_absolute_filepath must be a string"
        view_note_dir, view_note_filename = os.path.split(view_absolute_filepath)
        if view_note_dir != CONFIG.SIMPLENOTE_NOTES_DIR:
            return
        pattern = re.compile(r"\((.*?)\)")
        for note in Note.mapper_id_note.values():
            if note.filename == view_note_filename:
                return note

        # TODO: maybe results include more than one
        results = re.findall(pattern, view_note_filename)
        if results:
            note_id = results[len(results) - 1]
            return Note.mapper_id_note.get(note_id)
        return


if __name__ == "__main__":
    from importlib import import_module
    from pprint import pprint

    import_module("_config")
    kwargs = {
        "id": uuid4().hex,
        "v": 1,
        "d": {
            "tags": [],
            "deleted": False,
            "systemTags": [],
            "content": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        },
    }
    note = Note(**kwargs)
    # pprint(note.create())
    note.d.content = "new content"
    # pprint(note.modify())
    # pprint(note._nest_dict())
    pprint(Note.__dict__)
    # empty_note = Note(v=1)
    # pprint(empty_note)
    # pprint(empty_note.__dict__)
    # pprint(empty_note._nest_dict())
    note = {
        # "id": "1",
        "v": 1,
        "d": {
            "tags": ["tag1", "tag2"],
            "deleted": False,
            "systemTags": ["systemtag1", "systemtag2"],
            "content": "content",
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
