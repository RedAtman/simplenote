import logging
from typing import Any
from unittest import TestCase

from _config import CONFIG
from utils.tools import Json2Obj as Settings


logger = logging.getLogger()
logger.info(CONFIG)

_note_kwargs: dict[str, Any] = {
    "tags": [],
    "deleted": False,
    "systemTags": [],
    "content": "SimplenoteTitle\n\n\nSimplenoteBody",
}

_d_kwargs: dict[str, Any] = {
    "d": _note_kwargs,
    "id": "123abc",
    "v": 2,
}


class TestSettings(TestCase):
    def test_settings(self):
        settings = Settings("Simplenote.sublime-settings")
        logger.info(settings)
        logger.info(settings.username)
        logger.info(settings.get("username"))
        assert isinstance(settings, dict)
        assert isinstance(settings, Settings)
        assert isinstance(settings.autostart, bool)
