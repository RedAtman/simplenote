from datetime import datetime
import functools
import logging
import os
import pickle
import re
import time
from typing import Any, Dict, List, Optional

from api import Simplenote
from models import Note

# https://www.sublimetext.com/docs/api_reference.html
import sublime
from utils.patterns.singleton.base import Singleton
from utils.sublime import close_view
from utils.tools import Settings


logger = logging.getLogger()


SIMPLENOTE_PROJECT_NAME = os.environ.get("SIMPLENOTE_PROJECT_NAME", "Simplenote")
SIMPLENOTE_PACKAGE_PATH = os.path.join(sublime.packages_path(), SIMPLENOTE_PROJECT_NAME)
SIMPLENOTE_DEFAULT_NOTE_TITLE = os.environ.get("SIMPLENOTE_DEFAULT_NOTE_TITLE", "Untitled")
SIMPLENOTE_TEMP_PATH = os.path.join(SIMPLENOTE_PACKAGE_PATH, "temp")
_SIMPLENOTE_NOTE_CACHE_FILE = os.environ.get("SIMPLENOTE_NOTE_CACHE_FILE", "note_cache.pkl")
SIMPLENOTE_NOTE_CACHE_FILE = os.path.join(SIMPLENOTE_PACKAGE_PATH, _SIMPLENOTE_NOTE_CACHE_FILE)
SIMPLENOTE_NOTE_FETCH_LENGTH = int(os.environ.get("SIMPLENOTE_NOTE_FETCH_LENGTH", 1000))
_SIMPLENOTE_SETTINGS_FILE = os.environ.get("SIMPLENOTE_SETTINGS_FILE", "simplenote.sublime-settings")
SIMPLENOTE_SETTINGS_FILE = os.path.join(SIMPLENOTE_PACKAGE_PATH, _SIMPLENOTE_SETTINGS_FILE)
# SETTINGS = sublime.load_settings(SIMPLENOTE_SETTINGS_FILE)
SETTINGS: Settings = Settings(SIMPLENOTE_SETTINGS_FILE)
API = Simplenote(SETTINGS.get("username", ""), SETTINGS.get("password", ""))


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
                logger.info((f"Created new objects cache file: {SIMPLENOTE_NOTE_CACHE_FILE}"))
        # logger.info(("Loaded objects length: ", len(cls.objects)))

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

    @staticmethod
    def get_filename_for_note(title_extension_map: List[Dict], note: Note) -> str:
        # Take out invalid characters from title and use that as base for the name
        import string

        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        note_name = get_note_name(note)
        base = "".join(c for c in note_name if c in valid_chars)
        # Determine extension based on title
        extension = ""
        if title_extension_map:
            for item in title_extension_map:
                pattern = re.compile(item["title_regex"], re.UNICODE)
                # logger.info(("pattern", pattern, "note_name", note_name, re.search(pattern, note_name)))
                if re.search(pattern, note_name):
                    extension = "." + item["extension"]
                    break
        # logger.info(("extension", extension, "base", base, "note_name", note_name, "note.id", note.id))
        return base + " (" + note.id + ")" + extension

    # @classmethod
    def _get_filename_for_note(cls, note: Note) -> str:
        title_extension_map = SETTINGS.get("title_extension_map")
        assert isinstance(title_extension_map, list), f"Invalid title_extension_map: {title_extension_map}"
        return cls.get_filename_for_note(title_extension_map, note)

    # @classmethod
    def get_path_for_note(cls, note: Note):
        return os.path.join(SIMPLENOTE_TEMP_PATH, cls._get_filename_for_note(note))

    # @classmethod
    def get_note_from_path(cls, view_filepath: str):
        note = None
        if view_filepath:
            if os.path.dirname(view_filepath) == SIMPLENOTE_TEMP_PATH:
                view_note_filename = os.path.split(view_filepath)[1]
                list__note_filename = [
                    note for note in cls._objects if cls._get_filename_for_note(note) == view_note_filename
                ]
                # logger.info((("cls._objects", cls._objects)))
                # logger.info(("view_note_filename", view_note_filename, "list__note_filename", list__note_filename))
                if not list__note_filename:
                    pattern = re.compile(r"\((.*?)\)")
                    results = re.findall(pattern, view_note_filename)
                    if results:
                        noteKey = results[len(results) - 1]
                        note = [note for note in cls._objects if note.id == noteKey]
                        logger.info(("noteKey", noteKey, "note", note))
                if list__note_filename:
                    note = list__note_filename[0]
        # logger.info(("note", note))
        return note


class Remote(_BaseManager):
    _api: Simplenote

    @functools.cached_property
    def api(self) -> Simplenote:
        if not isinstance(getattr(self, "_api"), Simplenote):
            # SETTINGS = sublime.load_settings(SIMPLENOTE_SETTINGS_FILE)
            SETTINGS = Settings(SIMPLENOTE_SETTINGS_FILE)
            self._api: Simplenote = Simplenote(
                username=SETTINGS.get("username", ""), password=SETTINGS.get("password", "")
            )
        assert isinstance(self._api, Simplenote), f"Invalid Simplenote instance: {self._api}"
        return self._api

    @property
    def notes(self) -> List[Note]:
        try:
            status, note_resume = self.api.index(data=True)
            assert status == 0, "Error getting notes"
            assert isinstance(note_resume, dict), "note_resume is not a dict"
            assert "index" in note_resume, "index not in note_resume"

            note_objects = []
            for note in note_resume["index"]:
                obj = Note(**note)
                note_objects.append(obj)
            return note_objects
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


def cmp_to_key(mycmp):
    "Convert a cmp= function into a key= function"

    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            logger.info((mycmp, mycmp(self.obj, other.obj), self.obj, other.obj))
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0

    return K


def sort_notes(a_note: Note, b_note: Note):
    if "pinned" in a_note.systemtags:
        return 1
    elif "pinned" in b_note.systemtags:
        return -1
    else:
        date_a = datetime.fromtimestamp(float(a_note.modifydate))
        date_b = datetime.fromtimestamp(float(b_note.modifydate))
        return (date_a > date_b) - (date_a < date_b)


def write_note_to_path(note: Note, filepath):
    f = open(filepath, "wb")
    try:
        content = note.d.content
        f.write(content.encode("utf-8"))
    except KeyError as err:
        logger.exception(err)
        pass
    f.close()


def open_note(note: Note, window: Optional[sublime.Window] = None):
    # if isinstance(note, dict):
    #     note = sm.local.dict_to_model(note)
    if window is None:
        window: sublime.Window = sublime.active_window()
    filepath = sm.local.get_path_for_note(note)
    write_note_to_path(note, filepath)
    return window.open_file(filepath)


def get_note_name(note: Note):
    try:
        content = note.d.content
    except Exception as err:
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


def handle_open_filename_change(old_file_path, updated_note: Note):
    new_file_path = sm.local.get_path_for_note(updated_note)
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
            new_view = open_note(updated_note, old_note_view.window())
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
        # logger.info(("key", key, getattr(updated_note_resume.d, key)))
        setattr(existing_note_entry.d, key, getattr(updated_note_resume.d, key))


def update_note(existing_note: Note, updated_note: Note):
    logger.info(("existing_note", existing_note, "updated_note", updated_note))
    synch_note_resume(existing_note, updated_note)
    # existing_note["local_modifydate"] = time.time()
    # existing_note["needs_update"] = False
    # filename = sm.local._get_filename_for_note(existing_note)
    # logger.info(("Updating note", "filename", filename, "existing_note", existing_note))
    # existing_note["filename"] = filename
    existing_note.local_modifydate = time.time()
    existing_note.needs_update = False
    filename = sm.local._get_filename_for_note(existing_note)
    # logger.info(("Updating note", "filename", filename, "existing_note", existing_note))
    existing_note.filename = filename
