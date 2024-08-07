from datetime import datetime
from functools import partial
import logging
import os
import sys
from threading import Thread
from typing import List, Optional

import sublime

from .._config import CONFIG
from ..utils.lock.thread import OptimisticLockingDict
from ..utils.patterns.singleton.base import Singleton
from .models import Note


logger = logging.getLogger()

__all__ = [
    "GlobalStorage",
    "sync",
    "start",
    "edit_settings",
    "show_message",
    "remove_status",
    "get_view_window",
    "open_view",
    "close_view",
    "on_note_changed",
    "clear_orphaned_filepaths",
    "QuickPanelPlaceholder",
    "show_quick_panel",
    "PreserveSelectionAndView",
]


class GlobalStorage(Singleton, OptimisticLockingDict):
    __mapper_key_type = {CONFIG.SIMPLENOTE_SYNC_TIMES_KEY: int, CONFIG.SIMPLENOTE_STARTED_KEY: bool}

    def optimistic_update(self, key, new_value):
        """Validate the type of the value before it is stored"""
        _type = self.__mapper_key_type.get(key)
        if not _type is None:
            if not isinstance(new_value, _type):
                raise TypeError("Value of %s must be type %s, got %s" % (key, _type, type(new_value)))
        return super().optimistic_update(key, new_value)


global_storage = GlobalStorage()


def sync(sync_interval: int = 30):
    sublime.run_command("simplenote_sync")
    sublime.set_timeout(sync, sync_interval * 1000)


def start():
    global_storage.optimistic_update(CONFIG.SIMPLENOTE_STARTED_KEY, False)
    global_storage.optimistic_update(CONFIG.SIMPLENOTE_SYNC_TIMES_KEY, 0)

    settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
    username = settings.get("username")
    password = settings.get("password")
    if username and password:
        if global_storage.get(CONFIG.SIMPLENOTE_SYNC_TIMES_KEY) != 0:
            return
        sync_interval = settings.get("sync_interval", 30)
        if not isinstance(sync_interval, int):
            show_message("`sync_interval` must be an integer. Please check settings file.")
            return
        if sync_interval <= 0:
            return
        logger.debug(("Loaded notes number: ", Note.tree.count))
        sync(sync_interval)
        return

    show_message("Simplenote: Please configure username/password in settings file.")
    edit_settings()
    sublime.set_timeout(remove_status, 2000)


def edit_settings():
    settings_file = CONFIG.SIMPLENOTE_SETTINGS_USER_FILE_PATH
    sublime.run_command(
        "edit_settings",
        {
            "base_file": settings_file,
            # "default": "// Simplenote Settings - User\n{\n\t$0\n}\n",
        },
    )


def _show_message(message: str = ""):
    if not isinstance(message, str):
        try:
            message = str(message)
        except Exception:
            message = ""
    for window in sublime.windows():
        for currentView in window.views():
            currentView.set_status("Simplenote", message)


def show_message(message: str):
    _show_message(message)
    sublime.message_dialog(message)


def remove_status():
    _show_message()


def get_view_window(view: Optional[sublime.View] = None) -> sublime.Window:
    window = None
    if isinstance(view, sublime.View):
        window = view.window()
    if window is None:
        window = sublime.active_window()
    return window


def open_view(filepath: str, view: Optional[sublime.View] = None):
    window = get_view_window(view)
    return window.open_file(filepath)


def close_view(view: sublime.View):
    view.set_scratch(True)
    window = get_view_window(view)
    window.focus_view(view)
    window.run_command("close_file")


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


def on_select(list__item: List[float], selected_index: int, *args, **kwargs):
    if selected_index == -1:
        return
    selected_item = list__item[selected_index]
    selected_note = getattr(selected_item, "note", None)
    if not isinstance(selected_note, Note):
        show_message("Note not found: note id(%s), Please restart simplenote or sublime text." % selected_index)
        return
    filepath = selected_note.open()
    selected_note.flush()
    view = open_view(filepath)


def clear_orphaned_filepaths(list__filename: List[str] = []):
    if not list__filename:
        list__filename = [note.filename for note in Note.mapper_id_note.values()]
    for filename in os.listdir(CONFIG.SIMPLENOTE_NOTES_DIR):
        if filename not in list__filename:
            os.remove(os.path.join(CONFIG.SIMPLENOTE_NOTES_DIR, filename))


from enum import Enum


class QuickPanelPlaceholder(str, Enum):
    DEFAULT = "Select Note press key 'enter' to open"
    FIRST_SYNC = "Sync complete. Press [super+shift+s] [super+shift+l] to display the note list again."


class QuickPanelItem(sublime.QuickPanelItem):
    def __init__(self, note: Note, trigger, details="", annotation="", kind=sublime.KIND_AMBIGUOUS):
        super().__init__(trigger, details, annotation, kind)
        self.note = note

    def __repr__(self):
        return "QuickPanelItem(%s)" % self.trigger


def show_quick_panel(first_sync: bool = False):
    if Note.tree.count <= 0:
        show_message(
            "No notes found. Please wait for the synchronization to complete, or press [super+shift+s, super+shift+c] to create a note."
        )
        return

    list__filename: List[str] = []
    list__item = []
    for note in Note.tree.iter(reverse=True):
        if not isinstance(note, Note):
            raise Exception("note is not a Note: %s" % type(note))
        if note.d.deleted:
            continue
        item = QuickPanelItem(
            note,
            note.title,
            [
                note.body[:120] + "..." if len(note.body) > 120 else note.body,
                # f"tags: {note.d.tags}",
            ],  # type: ignore
            f"version:{note.v} | update:{datetime.fromtimestamp(note.d.modificationDate).strftime('%Y-%m-%d %H:%M:%S')}",
            kind=(sublime.KIND_ID_SNIPPET, "", ""),
        )
        list__item.append(item)

    placeholder = QuickPanelPlaceholder.DEFAULT
    if first_sync:
        task = Thread(target=clear_orphaned_filepaths, args=(list__filename,))
        task.start()
        placeholder = QuickPanelPlaceholder.FIRST_SYNC

    def show_panel():
        sublime.active_window().show_quick_panel(
            list__item,
            partial(on_select, list__item),
            flags=sublime.MONOSPACE_FONT | sublime.KEEP_OPEN_ON_FOCUS_LOST | sublime.WANT_EVENT,
            # on_highlight=self.on_select,
            placeholder=placeholder,
        )

    sublime.set_timeout(show_panel, 500)


if not sys.version_info >= (3, 0):

    class PreserveSelectionAndView:
        """
        Context manager to preserve selection and view when text is replaced.

        Sublime Text 2 sucks at this, hence the manual lifting.
        """

        def __init__(self, view):
            """Preserve the view (single open document)."""
            self.view = view

        def __enter__(self):
            """Save selection and view."""
            self.sel = list(self.view.sel())
            self.visible_region_begin = self.view.visible_region().begin()
            self.viewport_position = self.view.viewport_position()
            return self

        def __exit__(self, type, value, traceback):
            """Restore selection."""
            self.view.sel().clear()
            for s in self.sel:
                self.view.sel().add(s)

            # restore view (this is somewhat cargo cultish, not sure why a
            # single statement does not suffice)
            self.view.show(self.visible_region_begin)
            self.view.set_viewport_position(self.viewport_position)

else:

    class PreserveSelectionAndView:
        """
        Context manager to preserve selection and view when text is replaced.

        Sublime Text 3 already does a good job preserving the view.
        """

        def __init__(self, view):
            """Preserve view."""
            self.view = view

        def __enter__(self):
            """Save selection."""
            self.sel = list(self.view.sel())
            return self

        def __exit__(self, type, value, traceback):
            """Restore selection."""
            self.view.sel().clear()
            for s in self.sel:
                self.view.sel().add(s)
