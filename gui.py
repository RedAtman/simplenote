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

settings_content = """
{
    // --------------------------------
    // Credentials:
    // --------------------------------
    "username": ""
    ,"password": ""
    // --------------------------------
    // Sync settings:
    // --------------------------------
    // Sync when sublime text starts:
    ,"autostart": true
    // Sync automatically (in seconds)
    ,"sync_every": 30
    // Number of notes synchronized each time
    ,"sync_note_number": 1000
    // Conflict resolution (If a file was edited on another client and also here, on sync..)
    // Server Wins (Same as selecting 'Overwrite')
    ,"on_conflict_use_server": false
    // Local is left unchanged (Same as selecting 'Cancel')
    ,"on_conflict_leave_alone": false
    // --------------------------------
    // Autosave (beta)
    // --------------------------------
    // Activate autosave and tell how much (in seconds) to wait
    // after you stop typing to send the save
    ,"autosave_debounce_time": 1
    // --------------------------------
    // File extension support
    // --------------------------------
    // Which file extension should the temporal files use?
    // This allows you to interact with other plugins such as
    // PlainTasks defining an extension for certain note title
    ,"title_extension_map": [{
        "title_regex": "\\[ST\\]"
        ,"extension": "todo"
    },
    {
        "title_regex": "\\# "
        ,"extension": "md"
        ,"systemTags": ["markdown"]
    }]
}
"""


def edit_settings():
    installed_package_settings_file = os.path.join(
        CONFIG.SIMPLENOTE_INSTALLED_PACKAGE_DIR, CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH
    )
    package_settings_file = os.path.join(CONFIG.SIMPLENOTE_PACKAGE_DIR, CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
    logger.warning((os.path.exists(installed_package_settings_file), installed_package_settings_file))
    logger.warning((os.path.exists(package_settings_file), package_settings_file))
    if os.path.exists(installed_package_settings_file):
        settings_file = installed_package_settings_file
    elif os.path.exists(package_settings_file):
        settings_file = package_settings_file
    else:
        settings_file = CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH

    # logger.warning(("CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH", CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH))

    # settings_file = os.path.join(
    #     sublime.installed_packages_path(), "Simplenote.sublime-package", CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH
    # )
    # settings_file = (
    #     """/Users/nut/Library/Application Support/Sublime Text/Packages/Simplenote/Simplenote.sublime-settings"""
    # )
    # settings_file = os.path.join(os.path.dirname(__file__), settings_file)
    logger.warning((type(settings_file), settings_file))
    # with open(settings_file) as f:
    #     settings = f.read()
    #     logger.warning(settings)
    # sublime.run_command("open_file", {"file": settings_file})
    sublime.run_command(
        "edit_settings",
        {"base_file": settings_file, "default": "// Simplenote Settings - User\n{\n\t$0\n}\n" + settings_content},
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
