import logging

import sublime

from .._config import CONFIG
from ..utils.lock.thread import OptimisticLockingDict
from ..utils.patterns.singleton.base import Singleton
from .gui import edit_settings, remove_status, show_message
from .operations import OperationManager


logger = logging.getLogger()


class GlobalStorage(Singleton, OptimisticLockingDict):
    __mapper_key_type = {CONFIG.SIMPLENOTE_SYNC_TIMES_KEY: int, CONFIG.SIMPLENOTE_STARTED_KEY: bool}

    def optimistic_update(self, key, new_value):
        _type = self.__mapper_key_type.get(key)
        if not _type is None:
            if not isinstance(new_value, _type):
                raise TypeError("Value of %s must be type %s, got %s" % (key, _type, type(new_value)))

        if key == CONFIG.SIMPLENOTE_SYNC_TIMES_KEY:
            import time

            logger.warning((time.time(), key, new_value))
        return super().optimistic_update(key, new_value)


manager = OperationManager()
global_storage = GlobalStorage()


def sync_once():
    if not manager.running:
        sublime.run_command("simplenote_sync")
    else:
        logger.debug("Sync omitted")


def sync(sync_every: int = 30):
    sync_once()
    sublime.set_timeout(sync, sync_every * 1000)


def start():
    settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
    username = settings.get("username")
    password = settings.get("password")

    if username and password:
        if global_storage.get(CONFIG.SIMPLENOTE_SYNC_TIMES_KEY) != 0:
            return
        sync_every = settings.get("sync_every", 0)
        if not isinstance(sync_every, int):
            show_message("`sync_every` must be an integer. Please check settings file.")
            return
        if sync_every <= 0:
            return
        sync(sync_every)
        return
    show_message("Simplenote: Please configure username/password in settings file.")
    edit_settings()
    sublime.set_timeout(remove_status, 2000)
