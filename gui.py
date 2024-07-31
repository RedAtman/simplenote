import logging
import os
from typing import Optional

import sublime

from ._config import CONFIG


logger = logging.getLogger()


__all__ = [
    "edit_settings",
    "show_message",
    "remove_status",
    "get_view_window",
    "open_view",
    "close_view",
]


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


def edit_settings():
    # sublime.run_command("open_file", {"file": CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH})
    sublime.run_command(
        "edit_settings",
        {
            "base_file": os.path.join(CONFIG.SIMPLENOTE_PACKAGE_DIR, CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH),
            "default": "// Simplenote Settings - User\n{\n\t$0\n}\n",
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
