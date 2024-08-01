import logging

import sublime

from .._config import CONFIG
from .gui import edit_settings, remove_status, show_message
from .operations import OperationManager


logger = logging.getLogger()
SIMPLENOTE_STARTED = False


def sync():
    manager = OperationManager()
    if not manager.running:
        sublime.run_command("simplenote_sync")
    else:
        logger.debug("Sync omitted")

    settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
    sync_every = settings.get("sync_every", 0)
    logger.debug(("Simplenote sync_every", sync_every))
    if not isinstance(sync_every, int):
        show_message("`sync_every` must be an integer. Please check settings file.")
        return

    if sync_every > 0:
        sublime.set_timeout(sync, sync_every * 1000)


def start():
    global SIMPLENOTE_STARTED
    logger.warning(("CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH", CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH))
    settings = sublime.load_settings("Simplenote.sublime-settings")
    username = settings.get("username")
    password = settings.get("password")

    if username and password:
        sync()
        SIMPLENOTE_STARTED = True
    else:
        edit_settings()
        show_message("Simplenote: Please configure username/password, Please check settings file.")
        sublime.set_timeout(remove_status, 2000)
        SIMPLENOTE_STARTED = False
    return SIMPLENOTE_STARTED
