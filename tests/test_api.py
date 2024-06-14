import logging
from typing import Any
from unittest import TestCase, main

from api import Note, NoteWrapper, Simplenote
from config import CONFIG


logger = logging.getLogger()
logger.info(CONFIG)


class TestNote(TestCase):
    _note_kwargs: dict[str, Any] = {
        "tags": ["tag1", "tag2"],
        "deleted": False,
        "shareURL": "",
        "systemTags": ["system_tag1", "system_tag2"],
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

    def test_note(self):
        note = Note(**self._note_kwargs)
        assert note.content == "SimplenoteTitle\n\n\nSimplenoteBody"
        assert note.tags == ["tag1", "tag2"]
        assert note.systemTags == ["system_tag1", "system_tag2"]
        assert note.deleted is False

    def test_note_wrapper(self):
        note = NoteWrapper(**self._d_kwargs)
        assert note.id == "123abc"
        assert note.v == 2
        assert isinstance(note.d, Note)
        assert note.d.content == "SimplenoteTitle\n\n\nSimplenoteBody"
        logger.info(note.__dict__)


class TestSimplenoteApi(TestCase):
    def setUp(self):
        self.instance = Simplenote(CONFIG.SIMPLENOTE_USERNAME, CONFIG.SIMPLENOTE_PASSWORD)

    def test_get_note_list(self):
        note_list, status = self.instance.get_note_list()
        logger.info((status, note_list))
        assert status == 0


if __name__ == "__main__":
    main()
