from importlib import import_module
import logging
from unittest import TestCase

from utils.tools import Json2Obj as Settings


import_module("utils.logger.init")
logger = logging.getLogger()


class TestSettings(TestCase):
    def test_settings(self):
        settings = Settings("simplenote.sublime-settings")
        logger.info(settings)
        logger.info(settings.username)
        logger.info(settings.get("username"))
        assert isinstance(settings, dict)
        assert isinstance(settings, Settings)
        assert isinstance(settings.autostart, bool)
