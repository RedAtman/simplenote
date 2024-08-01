import logging

import sublime

from ._config import CONFIG
from .lib.core import start
from .lib.models import Note


logger = logging.getLogger()

SIMPLENOTE_RELOAD_CALLS = -1


def reload_if_needed():
    # global SIMPLENOTE_RELOAD_CALLS

    # # Sublime calls this twice for some reason :(
    # SIMPLENOTE_RELOAD_CALLS += 1
    # if SIMPLENOTE_RELOAD_CALLS % 2 != 0:
    #     logger.debug("Simplenote Reload call %s" % SIMPLENOTE_RELOAD_CALLS)
    #     return

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
