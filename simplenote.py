from datetime import datetime
import logging
import pickle
from typing import Any, Dict, List

from ._config import CONFIG
from .models import Note
from .utils.patterns.singleton.base import Singleton


# https://www.sublimetext.com/docs/api_reference.html


__all__: List[str] = [
    "Local",
    "load_notes",
    "sort_notes",
]


logger = logging.getLogger()


class _BaseManager(Singleton):
    pass


class Local(_BaseManager):

    def __init__(self):
        super().__init__()
        self._notes: List[Dict[str, Any]] = []
        self._objects: List[Note] = []

    @property
    def notes(self) -> List[Dict[str, Any]]:
        return [note.d.__dict__ for note in self._objects]

    @notes.setter
    def notes(self, value: List[Dict[str, Any]]):
        self._notes = value

    @property
    def objects(self) -> List[Note]:
        return self._objects

    @objects.setter
    def objects(self, value: List[Note]):
        self._objects = value

    @staticmethod
    def _save_objects(SIMPLENOTE_NOTE_CACHE_FILE_PATH: str, objects: List[Note]):
        with open(SIMPLENOTE_NOTE_CACHE_FILE_PATH, "w+b") as cache_file:
            pickle.dump(objects, cache_file)

    @classmethod
    def save_objects(cls):
        return
        cls._save_objects(CONFIG.SIMPLENOTE_NOTE_CACHE_FILE_PATH, cls._objects)

    @staticmethod
    def dict_to_model(note: Dict[str, Any]) -> Note:
        d = {}
        for key in Note.__annotations__["d"].__annotations__.keys():
            if key in note:
                d[key] = note[key]
        kwargs = {
            "id": note["key"],
            "v": note["version"],
            "d": note,
        }
        return Note(**kwargs)

    # @staticmethod
    # def model_to_dict(note: Note) -> Dict[str, Any]:
    #     return note.d.__dict__


def load_notes():
    try:
        with open(CONFIG.SIMPLENOTE_NOTE_CACHE_FILE_PATH, "rb") as cache_file:
            Note.mapper_id_note = pickle.load(cache_file, encoding="utf-8")
    except (EOFError, IOError, FileNotFoundError) as err:
        logger.exception(err)
        with open(CONFIG.SIMPLENOTE_NOTE_CACHE_FILE_PATH, "w+b") as cache_file:
            pickle.dump(Note.mapper_id_note, cache_file)
            logger.debug((f"Created new objects cache file: {CONFIG.SIMPLENOTE_NOTE_CACHE_FILE_PATH}"))


def sort_notes(a_note: Note, b_note: Note):
    if "pinned" in a_note.d.systemTags:
        return 1
    elif "pinned" in b_note.d.systemTags:
        return -1
    else:
        date_a = datetime.fromtimestamp(float(a_note.d.modificationDate))
        date_b = datetime.fromtimestamp(float(b_note.d.modificationDate))
        return (date_a > date_b) - (date_a < date_b)
