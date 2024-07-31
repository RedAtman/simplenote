import logging
import os
from typing import Optional

import sublime


logger = logging.getLogger()


__all__ = [
    "SIMPLENOTE_PACKAGE_DIR",
    "SIMPLENOTE_SETTINGS_FILE",
    "SIMPLENOTE_BASE_DIR",
    "show_message",
    "remove_status",
    "get_view_window",
    "open_view",
    "close_view",
]

SIMPLENOTE_PACKAGE_DIR = sublime.packages_path()
SIMPLENOTE_SETTINGS_FILE = "Default.sublime-settings"
SIMPLENOTE_BASE_DIR = os.path.join(SIMPLENOTE_PACKAGE_DIR, "Simplenote")


# def init_settings(reload_if_needed: Optional(Callable) = None):
#     global SETTINGS
#     if SETTINGS is None:
#         SETTINGS = sublime.load_settings("SIMPLENOTE_SETTINGS_FILE")
#         # logger.debug(("SETTINGS.__dict__: ", SETTINGS.__dict__))
#         # logger.debug(("SETTINGS.username: ", SETTINGS.get("username")))
#     if reload_if_needed:
#         SETTINGS.clear_on_change("username")
#         SETTINGS.clear_on_change("password")
#         SETTINGS.add_on_change("username", reload_if_needed)
#         SETTINGS.add_on_change("password", reload_if_needed)


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
