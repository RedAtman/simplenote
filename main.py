import functools
import logging

import sublime

from ._config import CONFIG
from .lib.core import GlobalStorage, start, sync
from .lib.models import Note


logger = logging.getLogger()

SIMPLENOTE_RELOAD_CALLS = -1


global_storage = GlobalStorage()
global_storage.optimistic_update(CONFIG.SIMPLENOTE_STARTED_KEY, False)
global_storage.optimistic_update(CONFIG.SIMPLENOTE_SYNC_TIMES_KEY, 0)


def reload_if_needed(autostart: bool = True):
    # global SIMPLENOTE_RELOAD_CALLS

    # # Sublime calls this twice for some reason :(
    # SIMPLENOTE_RELOAD_CALLS += 1
    # if SIMPLENOTE_RELOAD_CALLS % 2 != 0:
    #     logger.debug("Simplenote Reload call %s" % SIMPLENOTE_RELOAD_CALLS)
    #     return

    logger.debug(("Simplenote Reloading", autostart))
    start()
    if autostart:
        sublime.set_timeout_async(sync, 2000)
        logger.debug("Auto Starting")


def plugin_loaded():
    # load_notes()
    logger.debug(("Loaded notes number: ", Note.tree.count))

    settings = sublime.load_settings("Simplenote.sublime-settings")
    # logger.debug(("SETTINGS.__dict__: ", SETTINGS.__dict__))
    # logger.debug(("SETTINGS.username: ", SETTINGS.get("username")))
    autostart = settings.get("autostart", True)
    if not isinstance(autostart, bool):
        autostart = True
    callback = functools.partial(reload_if_needed, autostart)
    settings.clear_on_change("username")
    settings.clear_on_change("password")
    settings.add_on_change("username", callback)
    settings.add_on_change("password", callback)

    reload_if_needed(autostart=autostart)
