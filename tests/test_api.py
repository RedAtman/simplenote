import logging
import time
from typing import Any
from unittest import TestCase, main

from _config import CONFIG
from api import Simplenote


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


class TestSimplenoteApi(TestCase):
    def __get_random_note_id(self):
        status, msg, result = self.API.index(limit=1, data=True)
        assert status == 0
        assert isinstance(result, dict)
        assert "index" in result
        _notes = result.get("index", [])
        assert isinstance(_notes, list)
        logger.info((status, result))
        note_id = _notes[0]["id"]
        assert isinstance(note_id, str)
        logger.info(note_id)
        return note_id

    def setUp(self):
        self.API = Simplenote(username=CONFIG.SIMPLENOTE_USERNAME, password=CONFIG.SIMPLENOTE_PASSWORD)

    def test_authenticate(self):
        result = self.API.authenticate(CONFIG.SIMPLENOTE_USERNAME, CONFIG.SIMPLENOTE_PASSWORD)
        assert isinstance(result, str)
        logger.info((result))

    def test_token(self):
        token = self.API.token
        assert isinstance(token, str)
        logger.info(token)

    def test_create(self):
        _note_kwargs["content"] = "New note content at %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logger.info(_note_kwargs)
        status, msg, note_d = self.API.modify(_note_kwargs, self.__get_random_note_id())
        logger.info((status, note_d))
        assert status == 0

    def test_index(self):
        status, msg, result = self.API.index(limit=1, data=True)
        assert isinstance(result, dict)
        logger.info((status, result))
        assert status == 0

    def test_retrieve(self):
        status, msg, note_d = self.API.retrieve(self.__get_random_note_id())
        assert isinstance(note_d, dict)
        logger.info((status, note_d))
        assert status == 0

    def test_modify(self):
        random_note_id = self.__get_random_note_id()
        status, msg, random_note_d = self.API.retrieve(random_note_id)
        logger.info(random_note_d)
        assert status == 0
        assert isinstance(random_note_d, dict)
        _time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        random_note_d["content"] = f"Updated content at {_time}"
        status, msg, note = self.API.modify(random_note_d, random_note_id)
        logger.info((status, note))
        assert status == 0

    def test_delete(self):
        random_note_id = self.__get_random_note_id()
        status, msg, note_d = self.API.retrieve(random_note_id)
        assert status == 0
        assert isinstance(note_d, dict)
        status, msg, note = self.API.delete(random_note_id)
        logger.info((status, note))
        assert status == 0

    def test_trash(self):
        random_note_id = self.__get_random_note_id()
        status, msg, note_d = self.API.retrieve(random_note_id)
        assert status == 0
        assert isinstance(note_d, dict)
        status, msg, note = self.API.trash(random_note_id)
        logger.info((status, note))
        assert status == 0


if __name__ == "__main__":
    main()
