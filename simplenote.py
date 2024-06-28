from datetime import datetime
import logging
import os
import pickle
import re
import time
from typing import Any, Dict, List

from models import Note

# https://www.sublimetext.com/docs/api_reference.html
import sublime
from utils.patterns.singleton.base import Singleton
from utils.sublime import close_view
from utils.tools import Json2Obj as Settings


logger = logging.getLogger()


SIMPLENOTE_PROJECT_NAME = os.environ.get("SIMPLENOTE_PROJECT_NAME", "Simplenote")
SIMPLENOTE_PACKAGE_PATH = os.path.join(sublime.packages_path(), SIMPLENOTE_PROJECT_NAME)
SIMPLENOTE_DEFAULT_NOTE_TITLE = os.environ.get("SIMPLENOTE_DEFAULT_NOTE_TITLE", "untitled")
SIMPLENOTE_TEMP_PATH = os.path.join(SIMPLENOTE_PACKAGE_PATH, "temp")
_SIMPLENOTE_NOTE_CACHE_FILE = os.environ.get("SIMPLENOTE_NOTE_CACHE_FILE", "note_cache.pkl")
SIMPLENOTE_NOTE_CACHE_FILE = os.path.join(SIMPLENOTE_PACKAGE_PATH, _SIMPLENOTE_NOTE_CACHE_FILE)
SIMPLENOTE_NOTE_FETCH_LENGTH = int(os.environ.get("SIMPLENOTE_NOTE_FETCH_LENGTH", 1000))
_SIMPLENOTE_SETTINGS_FILE = os.environ.get("SIMPLENOTE_SETTINGS_FILE", "simplenote.sublime-settings")
SIMPLENOTE_SETTINGS_FILE = os.path.join(SIMPLENOTE_PACKAGE_PATH, _SIMPLENOTE_SETTINGS_FILE)
# SETTINGS = sublime.load_settings(SIMPLENOTE_SETTINGS_FILE)
SETTINGS: Settings = Settings(SIMPLENOTE_SETTINGS_FILE)


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

    # @classmethod
    def load_notes(self):
        try:
            with open(SIMPLENOTE_NOTE_CACHE_FILE, "rb") as cache_file:
                self.objects = pickle.load(cache_file, encoding="utf-8")
        except (EOFError, IOError, FileNotFoundError) as err:
            logger.exception(err)
            with open(SIMPLENOTE_NOTE_CACHE_FILE, "w+b") as cache_file:
                pickle.dump(self._objects, cache_file)
                logger.debug((f"Created new objects cache file: {SIMPLENOTE_NOTE_CACHE_FILE}"))

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

    # @classmethod
    def get_note_from_path(cls, view_filepath: str):
        note = None
        if view_filepath:
            if os.path.dirname(view_filepath) == SIMPLENOTE_TEMP_PATH:
                view_note_filename = os.path.split(view_filepath)[1]
                list__note_filename = [note for note in cls._objects if note.get_filename() == view_note_filename]

                if not list__note_filename:
                    pattern = re.compile(r"\((.*?)\)")
                    results = re.findall(pattern, view_note_filename)
                    if results:
                        noteKey = results[len(results) - 1]
                        note = [note for note in cls._objects if note.id == noteKey]
                        logger.debug(("noteKey", noteKey, "note", note))
                if list__note_filename:
                    note = list__note_filename[0]
        return note


class Remote(_BaseManager):

    @property
    def notes(self) -> List[Note]:
        try:
            return Note.index()
        except Exception as err:
            logger.exception(err)
            raise err


class SimplenoteManager(Singleton):
    def __init__(self):
        super().__init__()
        self.local: Local = Local()
        self.remote: Remote = Remote()

    # def save(self, local=False):
    #     if local:
    #         self.local.save()
    #     self.remote.save()

    @property
    def instance(self):
        return self.remote.api


sm = SimplenoteManager()


def sort_notes(a_note: Note, b_note: Note):
    if "pinned" in a_note.systemtags:
        return 1
    elif "pinned" in b_note.systemtags:
        return -1
    else:
        date_a = datetime.fromtimestamp(float(a_note.modifydate))
        date_b = datetime.fromtimestamp(float(b_note.modifydate))
        return (date_a > date_b) - (date_a < date_b)


def handle_open_filename_change(old_file_path, updated_note: Note):
    new_file_path = updated_note.get_filepath()
    old_note_view = None
    new_view = None
    # If name changed
    if old_file_path != new_file_path:
        # Save the current active view because we might lose the focus
        old_active_view = sublime.active_window().active_view()
        assert isinstance(old_active_view, sublime.View), "old_active_view is not a sublime.View"
        # Search for the view of the open note
        for view_list in [window.views() for window in sublime.windows()]:
            for view in view_list:
                if view.file_name() == old_file_path:
                    old_note_view = view
                    break
        # If found
        if old_note_view:
            # Open the note in a new view
            new_view = updated_note.open(old_note_view.window())
            # Close the old dirty note
            old_note_view_id = old_note_view.id()
            old_active_view_id = old_active_view.id()
            if old_note_view.window():
                old_note_window_id = old_note_view.window().id()
            else:
                old_note_window_id = sublime.active_window()  # Sometimes this happens on Sublime 2...
            close_view(old_note_view)
            # Focus on the new view or on the previous one depending
            # on where we were
            if old_note_view_id == old_active_view_id:
                old_note_window = [window for window in sublime.windows() if window.id() == old_note_window_id]
                if old_note_window:
                    old_note_window[0].focus_view(new_view)
            else:
                sublime.active_window().focus_view(old_active_view)
        try:
            os.remove(old_file_path)
        except OSError as err:
            logger.exception(err)
        return True
    return False


def synch_note_resume(existing_note_entry: Note, updated_note_resume: Note):
    for key in updated_note_resume.d.__dict__:
        setattr(existing_note_entry.d, key, getattr(updated_note_resume.d, key))


def update_note(existing_note: Note, updated_note: Note):
    logger.debug(("existing_note", existing_note, "updated_note", updated_note))
    synch_note_resume(existing_note, updated_note)
    existing_note.local_modifydate = time.time()
    existing_note.needs_update = False
    filename = existing_note.get_filename()
    existing_note.filename = filename
