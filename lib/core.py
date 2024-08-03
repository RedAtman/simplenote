import logging

import sublime

from .._config import CONFIG
from ..utils.lock.thread import OptimisticLockingDict
from ..utils.patterns.singleton.base import Singleton
from .gui import edit_settings, remove_status, show_message
from .operations import Operator


logger = logging.getLogger()


class GlobalStorage(Singleton, OptimisticLockingDict):
    __mapper_key_type = {CONFIG.SIMPLENOTE_SYNC_TIMES_KEY: int, CONFIG.SIMPLENOTE_STARTED_KEY: bool}

    def optimistic_update(self, key, new_value):
        """Validate the type of the value before it is stored"""
        _type = self.__mapper_key_type.get(key)
        if not _type is None:
            if not isinstance(new_value, _type):
                raise TypeError("Value of %s must be type %s, got %s" % (key, _type, type(new_value)))

        if key == CONFIG.SIMPLENOTE_SYNC_TIMES_KEY:
            import time

            logger.warning((time.time(), key, new_value))
        return super().optimistic_update(key, new_value)


operator = Operator()
global_storage = GlobalStorage()


def sync_once():
    if not operator.running:
        sublime.run_command("simplenote_sync")
    else:
        logger.debug("Sync omitted")


def sync(sync_interval: int = 30):
    sync_once()
    sublime.set_timeout(sync, sync_interval * 1000)


def start():
    settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
    username = settings.get("username")
    password = settings.get("password")

    if username and password:
        if global_storage.get(CONFIG.SIMPLENOTE_SYNC_TIMES_KEY) != 0:
            return
        sync_interval = settings.get("sync_interval", 30)
        if not isinstance(sync_interval, int):
            show_message("`sync_interval` must be an integer. Please check settings file.")
            return
        if sync_interval <= 0:
            return
        sync(sync_interval)
        return
    show_message("Simplenote: Please configure username/password in settings file.")
    edit_settings()
    sublime.set_timeout(remove_status, 2000)
