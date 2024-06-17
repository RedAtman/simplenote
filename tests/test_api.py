import logging
import time
from typing import Any
from unittest import TestCase, main

from api import Simplenote
from config import CONFIG


logger = logging.getLogger()
logger.info(CONFIG)

_note_kwargs: dict[str, Any] = {
    "tags": [],
    "deleted": False,
    "shareURL": "",
    "systemTags": [],
    "content": "SimplenoteTitle\n\n\nSimplenoteBody",
    "publishURL": "",
    "modificationDate": 1539088227.272,
    "creationDate": 1529054831.73117,
}

_d_kwargs: dict[str, Any] = {
    "d": _note_kwargs,
    "id": "123abc",
    "v": 2,
}


class TestSimplenoteApi(TestCase):
    def __get_random_note_id(self):
        status, result = self.API.index(limit=1, data=True)
        assert status == 0
        assert isinstance(result, dict)
        logger.info((status, result))
        note_id = result["index"][0]["id"]
        assert isinstance(note_id, str)
        logger.info(note_id)
        return note_id

    def setUp(self):
        self.API = Simplenote(CONFIG.SIMPLENOTE_USERNAME, CONFIG.SIMPLENOTE_PASSWORD)

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
        _note_kwargs["creationDate"] = time.time()
        _note_kwargs["modificationDate"] = time.time()
        status, note_d = self.API.modify(_note_kwargs)
        logger.info((status, note_d))
        assert status == 0

    def test_index(self):
        status, result = self.API.index(limit=1, data=True)
        assert isinstance(result, dict)
        logger.info((status, result))
        assert status == 0

    def test_retrieve(self):
        status, note_d = self.API.retrieve(self.__get_random_note_id())
        assert isinstance(note_d, dict)
        logger.info((status, note_d))
        assert status == 0

    def test_modify(self):
        random_note_id = self.__get_random_note_id()
        status, random_note_d = self.API.retrieve(random_note_id)
        logger.info(random_note_d)
        assert status == 0
        assert isinstance(random_note_d, dict)
        _time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        random_note_d["content"] = f"Updated content at {_time}"
        status, note = self.API.modify(random_note_d, random_note_id)
        logger.info((status, note))
        assert status == 0

    def test_delete(self):
        random_note_id = self.__get_random_note_id()
        status, note_d = self.API.retrieve(random_note_id)
        assert status == 0
        assert isinstance(note_d, dict)
        status, note = self.API.delete(random_note_id)
        logger.info((status, note))
        assert status == 0

    def test_trash(self):
        random_note_id = self.__get_random_note_id()
        status, note_d = self.API.retrieve(random_note_id)
        assert status == 0
        assert isinstance(note_d, dict)
        status, note = self.API.trash(random_note_id)
        logger.info((status, note))
        assert status == 0


if __name__ == "__main__":
    main()
