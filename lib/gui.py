from functools import partial
import logging
import os
from typing import List, Optional

import sublime

from .._config import CONFIG
from .models import Note


logger = logging.getLogger()


__all__ = [
    "edit_settings",
    "show_message",
    "remove_status",
    "get_view_window",
    "open_view",
    "close_view",
    "clear_orphaned_filepaths",
    "on_note_changed",
]


def edit_settings():
    settings_file = CONFIG.SIMPLENOTE_SETTINGS_USER_FILE_PATH
    logger.warning((type(settings_file), settings_file))
    # with open(settings_file) as f:
    #     settings = f.read()
    #     logger.warning(settings)
    # sublime.run_command("open_file", {"file": settings_file})
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


def clear_orphaned_filepaths(list__filename: List[str] = []):
    if not list__filename:
        list__filename = [note.filename for note in Note.mapper_id_note.values()]
    for filename in os.listdir(CONFIG.SIMPLENOTE_NOTES_DIR):
        if filename not in list__filename:
            os.remove(os.path.join(CONFIG.SIMPLENOTE_NOTES_DIR, filename))


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
