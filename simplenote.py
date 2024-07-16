from datetime import datetime
from functools import partial
import logging
import os
import pickle
from typing import Any, Dict, List

# https://www.sublimetext.com/docs/api_reference.html
import sublime

from models import SIMPLENOTE_NOTES_DIR, Note
from utils.patterns.singleton.base import Singleton
from utils.sublime import close_view, open_view


__all__: List[str] = [
    "SIMPLENOTE_SETTINGS_FILE",
    "Local",
    "load_notes",
    "clear_orphaned_filepaths",
    "sort_notes",
    "on_note_changed",
]


logger = logging.getLogger()


SIMPLENOTE_PROJECT_NAME = "Simplenote"
SIMPLENOTE_CACHE_DIR = os.path.join(sublime.cache_path(), SIMPLENOTE_PROJECT_NAME)
os.makedirs(SIMPLENOTE_CACHE_DIR, exist_ok=True)
SIMPLENOTE_NOTE_CACHE_FILE = os.path.join(SIMPLENOTE_CACHE_DIR, "note_cache.pkl")
SIMPLENOTE_SETTINGS_FILE = "simplenote.sublime-settings"


class _BaseManager(Singleton):
    pass


class Local(_BaseManager):

    def __init__(self):
        super().__init__()
        self._notes: List[Dict[str, Any]] = []
        self._objects: List[Note] = []
        # self.load_notes()

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
    def _save_objects(SIMPLENOTE_NOTE_CACHE_FILE: str, objects: List[Note]):
        with open(SIMPLENOTE_NOTE_CACHE_FILE, "w+b") as cache_file:
            pickle.dump(objects, cache_file)

    # @classmethod
    def save_objects(cls):
        return
        cls._save_objects(SIMPLENOTE_NOTE_CACHE_FILE, cls._objects)

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
        with open(SIMPLENOTE_NOTE_CACHE_FILE, "rb") as cache_file:
            Note.mapper_id_note = pickle.load(cache_file, encoding="utf-8")
    except (EOFError, IOError, FileNotFoundError) as err:
        logger.exception(err)
        with open(SIMPLENOTE_NOTE_CACHE_FILE, "w+b") as cache_file:
            pickle.dump(Note.mapper_id_note, cache_file)
            logger.debug((f"Created new objects cache file: {SIMPLENOTE_NOTE_CACHE_FILE}"))


def clear_orphaned_filepaths():
    list__filepath = [note.filename for note in Note.mapper_id_note.values()]
    if not os.path.exists(SIMPLENOTE_NOTES_DIR):
        os.makedirs(SIMPLENOTE_NOTES_DIR)
    for filepath in os.listdir(SIMPLENOTE_NOTES_DIR):
        if filepath not in list__filepath:
            os.remove(os.path.join(SIMPLENOTE_NOTES_DIR, filepath))


def sort_notes(a_note: Note, b_note: Note):
    if "pinned" in a_note.d.systemTags:
        return 1
    elif "pinned" in b_note.d.systemTags:
        return -1
    else:
        date_a = datetime.fromtimestamp(float(a_note.d.modificationDate))
        date_b = datetime.fromtimestamp(float(b_note.d.modificationDate))
        return (date_a > date_b) - (date_a < date_b)


def on_note_changed(note: Note):
    old_window = sublime.active_window()
    old_view = old_window.find_open_file(note._filepath)
    # if note is not open in the current window
    if not isinstance(old_view, sublime.View):
        note.flush()
        return

    if note._filepath == note.filepath:
        note.flush()
        note.open()
        return

    note._close(note._filepath)
    note.flush()
    close_view(old_view)
    note.open()
    new_view = open_view(note.filepath, old_view)

    # TODO: maybe not needed, or needed to be tested
    old_active_view = old_window.active_view()
    assert isinstance(old_active_view, sublime.View), "old_active_view is not a sublime.View"
    if isinstance(old_active_view, sublime.View):
        # old_window.focus_view(old_active_view)
        if old_view.id() == old_active_view.id():
            old_note_window = [window for window in sublime.windows() if window.id() == old_window.id()]
            if old_note_window:
                old_note_window[0].focus_view(new_view)
        else:
            old_window.focus_view(old_active_view)

    sublime.set_timeout(partial(new_view.run_command, "revert"), 0)
