print(__file__)
from ast import Dict
from datetime import datetime
import functools
import logging
import os
import pickle
import re
import time
from typing import Any, List, Optional

from api import Simplenote
from config import CONFIG
from models import Note

# https://www.sublimetext.com/docs/api_reference.html
import sublime
from utils.patterns.singleton.base import Singleton
from utils.sublime import close_view


logger = logging.getLogger()


PACKAGE_PATH = os.path.join(sublime.packages_path(), CONFIG.PROJECT_NAME)
TEMP_PATH = os.path.join(PACKAGE_PATH, "temp")
SETTINGS = sublime.load_settings(CONFIG.SETTINGS_FILE)


class _BaseManager:
    pass


class Local(_BaseManager):
    _NOTE_CACHE_FILE_PATH = os.path.join(PACKAGE_PATH, CONFIG._NOTE_CACHE_FILE)
    NOTE_CACHE_FILE_PATH = os.path.join(PACKAGE_PATH, CONFIG.NOTE_CACHE_FILE)
    notes: List[Dict] = []
    objects: List[Note] = []

    def __init__(self):
        super().__init__()
        self.load_notes()

    @classmethod
    def load_notes(cls):
        try:
            with open(cls._NOTE_CACHE_FILE_PATH, "rb") as cache_file:
                cls.notes = pickle.load(cache_file, encoding="utf-8")
        except (EOFError, IOError, FileNotFoundError) as err:
            logger.exception(err)
            with open(cls._NOTE_CACHE_FILE_PATH, "w+b") as cache_file:
                pickle.dump(cls.notes, cache_file)
                logger.info((f"Created new note cache file: {cls._NOTE_CACHE_FILE_PATH}"))
        logger.info(("Loaded notes length: ", len(cls.notes)))
        try:
            with open(cls.NOTE_CACHE_FILE_PATH, "rb") as cache_file:
                cls.objects = pickle.load(cache_file, encoding="utf-8")
        except (EOFError, IOError, FileNotFoundError) as err:
            logger.exception(err)
            with open(cls.NOTE_CACHE_FILE_PATH, "w+b") as cache_file:
                pickle.dump(cls.objects, cache_file)
                logger.info((f"Created new objects cache file: {cls.NOTE_CACHE_FILE_PATH}"))
        logger.info(("Loaded objects length: ", len(cls.objects)))

    @staticmethod
    def _save_notes(NOTE_CACHE_FILE_PATH: str, notes: List[Any]):
        with open(NOTE_CACHE_FILE_PATH, "w+b") as cache_file:
            pickle.dump(notes, cache_file)

    @classmethod
    def save_notes(cls):
        cls._save_notes(cls.NOTE_CACHE_FILE_PATH, cls.notes)

    @classmethod
    def save(cls):
        cls.save_notes()

    @staticmethod
    def get_filename_for_note(title_extension_map: List[Dict], note: Dict) -> str:
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
                logger.info(("pattern", pattern, "note_name", note_name, re.search(pattern, note_name)))
                if re.search(pattern, note_name):
                    extension = "." + item["extension"]
                    break
        return base + " (" + note["key"] + ")" + extension

    @classmethod
    def _get_filename_for_note(cls, note: Dict):
        title_extension_map = SETTINGS.get("title_extension_map")
        assert isinstance(title_extension_map, list), f"Invalid title_extension_map: {title_extension_map}"
        return cls.get_filename_for_note(title_extension_map, note)

    @classmethod
    def get_path_for_note(cls, note: Dict):
        return os.path.join(TEMP_PATH, cls._get_filename_for_note(note))

    @classmethod
    def get_note_from_path(cls, view_filepath: str):
        note = None
        if view_filepath:
            if os.path.dirname(view_filepath) == TEMP_PATH:
                view_note_filename = os.path.split(view_filepath)[1]
                note = [note for note in cls.notes if cls._get_filename_for_note(note) == view_note_filename]
                if not note:

                    pattern = re.compile(r"\((.*?)\)")
                    results = re.findall(pattern, view_note_filename)
                    if results:
                        noteKey = results[len(results) - 1]
                        note = [note for note in cls.notes if note["key"] == noteKey]
                if note:
                    note = note[0]
        return note


class Remote(_BaseManager):
    def __init__(self):
        # self._api: Simplenote = Simplenote(SETTINGS.get("username", ""), SETTINGS.get("password", ""))
        # self._api: Simplenote = Simplenote(CONFIG.SIMPLENOTE_USERNAME, CONFIG.SIMPLENOTE_PASSWORD)
        self._api: Optional[Simplenote] = None

    @functools.cached_property
    def api(self) -> Simplenote:
        logger.info(("instance", self._api))
        if not isinstance(self._api, Simplenote):
            SETTINGS = sublime.load_settings(CONFIG.SETTINGS_FILE)
            self._api: Simplenote = Simplenote(
                username=SETTINGS.get("username", ""), password=SETTINGS.get("password", "")
            )
            # self._instance = Simplenote(CONFIG.SIMPLENOTE_USERNAME, CONFIG.SIMPLENOTE_PASSWORD)
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


def sort_notes(a_note, b_note):
    if "pinned" in a_note["systemtags"]:
        return 1
    elif "pinned" in b_note["systemtags"]:
        return -1
    else:
        date_a = datetime.fromtimestamp(float(a_note["modifydate"]))
        date_b = datetime.fromtimestamp(float(b_note["modifydate"]))
        return (date_a > date_b) - (date_a < date_b)


def write_note_to_path(note, filepath):
    f = open(filepath, "wb")
    try:
        content = note["content"]
        f.write(content.encode("utf-8"))
    except KeyError as err:
        logger.exception(err)
        pass
    f.close()


def open_note(note, window=None):
    if not window:
        window = sublime.active_window()
    filepath = sm.local.get_path_for_note(note)
    write_note_to_path(note, filepath)
    return window.open_file(filepath)


def get_note_name(note):
    try:
        content = note["content"]
    except Exception as err:
        return CONFIG.DEFAULT_NOTE_TITLE
    index = content.find("\n")
    if index > -1:
        title = content[:index]
    else:
        if content:
            title = content
        else:
            title = CONFIG.DEFAULT_NOTE_TITLE
    return title


def handle_open_filename_change(old_file_path, updated_note):
    new_file_path = sm.local.get_path_for_note(updated_note)
    old_note_view = None
    new_view = None
    # If name changed
    if old_file_path != new_file_path:
        # Save the current active view because we might lose the focus
        old_active_view = sublime.active_window().active_view()
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


def synch_note_resume(existing_note_entry, updated_note_resume):
    for key in updated_note_resume:
        existing_note_entry[key] = updated_note_resume[key]


def update_note(existing_note, updated_note):
    logger.info(("existing_note", existing_note, "updated_note", updated_note))
    synch_note_resume(existing_note, updated_note)
    existing_note["local_modifydate"] = time.time()
    existing_note["needs_update"] = False
    filename = sm.local._get_filename_for_note(existing_note)
    logger.info(("Updating note", "filename", filename, "existing_note", existing_note))
    existing_note["filename"] = filename
