from importlib import import_module
import logging
from typing import Any
from unittest import TestCase, main

from models import Note, _Note


import_module("utils.logger.init")

logger = logging.getLogger()


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
        _d_kwargs["d"]["modificationDate"] = 1
        logger.debug(("old modificationDate", note.d.modificationDate))
        logger.debug(("new modificationDate", _d_kwargs["d"]["modificationDate"]))
        note3 = Note(**_d_kwargs)
        logger.debug(("old modificationDate", note.d.modificationDate))
        logger.debug(("new modificationDate", note3.d.modificationDate))
        logger.debug((note3.id, id(note3), note3.d.content))
        logger.warning([[k, id(v), v.d.content] for k, v in Note.mapper_id_note.items()])
        assert note is note3
        assert note == note3
        assert note.id == note3.id
        assert id(note) == id(note3)
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

    def test__(self):
        note = Note(**_d_kwargs)
        logger.info(note.__dataclass_params__)

    def test_id(self):
        note = Note(**_d_kwargs)
        note2 = Note(**_d_kwargs)
        assert note.id == note2.id
        _d_kwargs["id"] = "003"
        note3 = Note(**_d_kwargs)
        assert note.id != note3.id

    def test_d(self):
        note = Note(**_d_kwargs)
        logger.info(type(note.d))
        assert isinstance(note.d, _Note)
        note.d = _note_kwargs
        logger.info(type(note.d))
        assert isinstance(note.d, _Note)

    def test_setattr(self):
        note = Note(**_d_kwargs)
        assert isinstance(note.d, _Note)
        note2 = Note(**_d_kwargs)
        assert isinstance(note2.d, _Note)
        assert note.id == note2.id
        # assert False
        # # logger.info(note.__dict__)
        # note.d.content = "1"
        # # logger.info(note.__dict__)
        # note.content = "2"
        # # logger.info(note.__dict__)
        # note.d = _note_kwargs
        # logger.info(note.__dict__)
        # logger.info(note)
        # assert note._content == content
        # # assert note.d.content == content

    def test_note_tree(self):
        # check same id
        note = Note(**_d_kwargs)
        assert Note.tree.count == 1
        find_note1 = Note.tree.find_item(note.d.modificationDate)
        assert note is find_note1
        assert note.d.modificationDate == find_note1.d.modificationDate
        # logger.info((note.d.modificationDate, find_note.d.modificationDate))
        logger.info([note.d.modificationDate for note in Note.tree])
        logger.info("-" * 100)
        note2 = Note(**_d_kwargs)
        assert note is note2
        find_note2 = Note.tree.find_item(note2.d.modificationDate)
        assert note is find_note2
        assert note.d.modificationDate == find_note2.d.modificationDate
        logger.info((note.d.modificationDate, find_note2.d.modificationDate))
        assert note2 is find_note2
        assert note2.d.modificationDate == find_note2.d.modificationDate
        logger.info((note2.d.modificationDate, find_note2.d.modificationDate))
        logger.info([note.d.modificationDate for note in Note.tree])
        logger.info((len(Note.mapper_id_note), Note.tree.count))
        assert Note.tree.count == 1
        assert len(Note.mapper_id_note) == 1

        _d_kwargs["id"] = "003"
        note3 = Note(**_d_kwargs)
        assert note is not note3
        # check note count
        assert Note.tree.count == 2
        assert len(Note.mapper_id_note) == 2
        logger.info([note.d.modificationDate for note in Note.mapper_id_note.values()])
        logger.info([note.d.modificationDate for note in Note.tree])
        # check order is restored after modificationDate is changed
        note3.d.modificationDate = 0
        logger.info([note.d.modificationDate for note in Note.tree])


if __name__ == "__main__":
    main()
