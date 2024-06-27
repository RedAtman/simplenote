import logging
from typing import Any
from unittest import TestCase, main

from _config import CONFIG
from models import Note


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


class TestNote(TestCase):

    # def test_note(self):
    #     note = Note(**_note_kwargs)
    #     assert note.content == "SimplenoteTitle\n\n\nSimplenoteBody"
    #     assert note.tags == ["tag1", "tag2"]
    #     assert note.systemTags == ["system_tag1", "system_tag2"]
    #     assert note.deleted is False

    def test_note(self):
        note = Note(**_d_kwargs)
        assert note.id == "123abc"
        assert note.v == 2
        assert isinstance(note.d, Note)
        assert note.d.content == "SimplenoteTitle\n\n\nSimplenoteBody"
        logger.info(note.__dict__)

    def test_mapper_id_note(self):
        _d_kwargs["id"] = "note"
        note = Note(**_d_kwargs)
        logger.debug((note.id, id(note), note.d.content))
        logger.warning([[k, id(v), v.d.content] for k, v in Note.mapper_id_note.items()])
        assert note.id in Note.mapper_id_note
        assert len(Note.mapper_id_note) == 1
        note_id = id(note)

        _d_kwargs["id"] = "note2"
        note2 = Note(**_d_kwargs)
        logger.debug((note2.id, id(note2), note2.d.content))
        logger.warning([[k, id(v), v.d.content] for k, v in Note.mapper_id_note.items()])
        assert len(Note.mapper_id_note) == 2

        _d_kwargs["id"] = "note"
        _d_kwargs["d"]["content"] = "note3 content"
        note3 = Note(**_d_kwargs)
        logger.debug((note3.id, id(note3), note3.d.content))
        logger.warning([[k, id(v), v.d.content] for k, v in Note.mapper_id_note.items()])
        assert note is note3
        assert len(Note.mapper_id_note) == 2


if __name__ == "__main__":
    main()
