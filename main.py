import logging

import sublime

from ._config import CONFIG
from .gui import edit_settings, remove_status, show_message
from .models import Note
from .operations import OperationManager


logger = logging.getLogger()

SIMPLENOTE_RELOAD_CALLS = -1
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


def reload_if_needed():
    global SIMPLENOTE_RELOAD_CALLS

    # Sublime calls this twice for some reason :(
    SIMPLENOTE_RELOAD_CALLS += 1
    if SIMPLENOTE_RELOAD_CALLS % 2 != 0:
        logger.debug("Simplenote Reload call %s" % SIMPLENOTE_RELOAD_CALLS)
        return

    logger.warning(("CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH", CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH))
    settings = sublime.load_settings("Simplenote.sublime-settings")
    autostart = settings.get("autostart")
    if bool(autostart):
        autostart = True
    logger.debug(("Simplenote Reloading", autostart))
    if autostart:
        sublime.set_timeout(start, 2000)
        logger.debug("Auto Starting")


def plugin_loaded():
    # load_notes()
    logger.debug(("Loaded notes number: ", Note.tree.count))

    logger.warning(("CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH", CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH))
    settings = sublime.load_settings("Simplenote.sublime-settings")
    # logger.debug(("SETTINGS.__dict__: ", SETTINGS.__dict__))
    # logger.debug(("SETTINGS.username: ", SETTINGS.get("username")))
    settings.clear_on_change("username")
    settings.clear_on_change("password")
    settings.add_on_change("username", reload_if_needed)
    settings.add_on_change("password", reload_if_needed)

    reload_if_needed()
