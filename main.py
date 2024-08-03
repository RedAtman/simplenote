import logging

import sublime

from ._config import CONFIG
from .lib.core import GlobalStorage, show_message, start
from .lib.models import Note


logger = logging.getLogger()


global_storage = GlobalStorage()
global_storage.optimistic_update(CONFIG.SIMPLENOTE_STARTED_KEY, False)
global_storage.optimistic_update(CONFIG.SIMPLENOTE_SYNC_TIMES_KEY, 0)


def reload_if_needed():
    # global SIMPLENOTE_RELOAD_CALLS

    # # Sublime calls this twice for some reason :(
    # SIMPLENOTE_RELOAD_CALLS += 1
    # logger.warning((SIMPLENOTE_RELOAD_CALLS, SIMPLENOTE_RELOAD_CALLS % 2))
    # if SIMPLENOTE_RELOAD_CALLS % 2 != 0:
    #     logger.debug("Simplenote Reload call %s" % SIMPLENOTE_RELOAD_CALLS)
    #     return

    settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
    autostart = settings.get("autostart", True)
    if not isinstance(autostart, bool):
        show_message("`autostart` must be a boolean. Please check settings file.")
        return
    if autostart:
        start()


def plugin_loaded():
    # load_notes()
    logger.debug(("Loaded notes number: ", Note.tree.count))

    settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
    # logger.debug(("SETTINGS.__dict__: ", SETTINGS.__dict__))
    # logger.debug(("SETTINGS.username: ", SETTINGS.get("username")))

    settings.clear_on_change("username")
    settings.clear_on_change("password")
    settings.add_on_change("username", reload_if_needed)
    settings.add_on_change("password", reload_if_needed)

    reload_if_needed()
