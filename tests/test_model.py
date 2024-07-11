import logging
from typing import Any
from unittest import TestCase, main

from _config import CONFIG
from models import Note


logger = logging.getLogger()
logger.info(CONFIG)

content = "# SimplenoteTitle\n\nSimplenoteBody"
_note_kwargs: dict[str, Any] = {
    "tags": [],
    "deleted": False,
    "systemTags": [],
    "content": content,
}
_d_kwargs: dict[str, Any] = {
    "d": _note_kwargs,
    "id": "123abc",
    "v": 2,
}


class TestNote(TestCase):

    def test_note(self):
        note = Note(**_d_kwargs)
        assert note.id == "123abc"
        assert note.v == 2
        assert isinstance(note, Note)
        assert note.d.content == content
        logger.info(note.__dict__)

    def test_mapper_id_note(self):
        _d_kwargs["id"] = "001"
        note = Note(**_d_kwargs)
        logger.debug((note.id, id(note), note.d.content))
        logger.warning([[k, id(v), v.d.content] for k, v in Note.mapper_id_note.items()])
        assert note.id in Note.mapper_id_note
        assert len(Note.mapper_id_note) == 1
        note_id = id(note)
        logger.info(note)
        note._content = note.d.content
        assert note._filename == " SimplenoteTitle (001).md"

        _d_kwargs["id"] = "002"
        note2 = Note(**_d_kwargs)
        logger.debug((note2.id, id(note2), note2.d.content))
        logger.warning([[k, id(v), v.d.content] for k, v in Note.mapper_id_note.items()])
        assert len(Note.mapper_id_note) == 2

        _d_kwargs["id"] = "001"
        _d_kwargs["d"]["content"] = "note3 content"
        note3 = Note(**_d_kwargs)
        logger.debug((note3.id, id(note3), note3.d.content))
        logger.warning([[k, id(v), v.d.content] for k, v in Note.mapper_id_note.items()])
        assert note is note3
        assert len(Note.mapper_id_note) == 2
        logger.info(note3)
        note3.flush()
        assert note._filename == "note3 content (001)"

    def test__content(self):
        _d_kwargs["id"] = "001"
        note = Note(**_d_kwargs)
        logger.info(note._content)
        assert note._content == _d_kwargs["d"]["content"]

        new_content = "note3 content"
        _d_kwargs["d"]["content"] = new_content
        note3 = Note(**_d_kwargs)
        logger.info(note._content)
        assert note._content == content
        note.flush()
        logger.info(note3._content)
        assert note._content == new_content
        assert note3._content == new_content


if __name__ == "__main__":
    main()
