import logging
from typing import Optional

from models import Note
import sublime


logger = logging.getLogger()


__all__ = [
    "show_message",
    "remove_status",
    "close_view",
]


def show_message(message: str):
    if not message:
        message = ""
    for window in sublime.windows():
        for currentView in window.views():
            currentView.set_status("Simplenote", message)


def remove_status():
    show_message(None)


def get_view_window(view: Optional[sublime.View] = None) -> sublime.Window:
    window = None
    if isinstance(view, sublime.View):
        window = view.window()
    if window is None:
        window = sublime.active_window()
    return window


def open_view(note: Note, view: Optional[sublime.View] = None):
    filepath = note.open()
    window = get_view_window(view)
    return window.open_file(filepath)


def close_view(view: sublime.View):
    view.set_scratch(True)
    window = get_view_window(view)
    window.focus_view(view)
    window.run_command("close_file")
