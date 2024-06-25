from collections import deque
import logging
import sys
from threading import Lock, Semaphore, Thread
from typing import Any, Callable, Dict, List, Optional

from api import Simplenote
from models import Note
from simplenote import SimplenoteManager
import sublime
from utils.patterns.singleton.base import Singleton
from utils.sublime import remove_status, show_message


__all__ = [
    "Operation",
    "NoteCreator",
    "NoteDownloader",
    "MultipleNoteContentDownloader",
    "GetNotesDelta",
    "NoteDeleter",
    "NoteUpdater",
    "OperationManager",
]

logger = logging.getLogger()


class OperationError(Exception):
    pass


class Operation(Thread):
    update_run_text: str = ""
    run_finished_text: str = ""
    simplenote_instance: Simplenote
    callback: Optional[Callable[..., Any]]
    callback_kwargs: Dict[str, Any]
    exception_callback: Optional[Callable[..., Any]]

    def __init__(self, *args, sm=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(sm, SimplenoteManager):
            raise Exception(f"Invalid SimplenoteManager instance, expected SimplenoteManager got {type(sm)}, {sm}")
        self.sm = sm
        self.callback = None
        self.exception_callback = None
        self.result = None

    def set_callback(self, callback: Callable[..., Any], kwargs: Optional[Dict[str, Any]] = None):
        self.callback = callback
        if kwargs is None:
            kwargs = {}
        self.callback_kwargs = kwargs

    def set_exception_callback(self, callback: Optional[Callable]):
        self.exception_callback = callback

    def join(self):
        logger.warning(("# STEP: 4"))
        logger.info(("caller", sys._getframe(1).f_code.co_name))
        Thread.join(self)
        if not self.callback is None:
            result = self.get_result()
            logger.warning((self, self.callback, self.callback_kwargs, self.exception_callback))
            # logger.warning(result)
            if not isinstance(result, Exception):
                self.callback(result, **self.callback_kwargs)
            elif self.exception_callback:
                self.exception_callback(result)
            else:
                logger.info(str(result))

    def get_result(self):
        return self.result


class NoteCreator(Operation):
    update_run_text = "Simplenote: Creating note"
    run_finished_text = "Simplenote: Done"

    def run(self):
        logger.info("Simplenote: Creating note")
        try:
            note = Note()
            saved_note = note.create()
            assert isinstance(saved_note, Note), "Expected Note got %s" % type(saved_note)
            self.result = note
        except Exception as err:
            self.result = OperationError(err)


class NoteDownloader(Operation):

    def __init__(self, note_id: str, semaphore: Semaphore, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.note_id = note_id
        self.semaphore = semaphore

    def run(self):
        logger.warning(("# STEP: 8"))
        self.semaphore.acquire()
        logger.info(("Simplenote: Downloading:", self.note_id))
        # result, status = self.sm.remote.api.get_note(self.note_id)
        # if status == 0:
        #     self.result = result
        # else:
        #     self.result = OperationError(result)
        note: Note = Note.retrieve(self.note_id)
        self.result = note
        self.semaphore.release()

    def join(self):
        # logger.info(("caller", sys._getframe(1).f_code.co_name))
        Thread.join(self)
        return self.result


class MultipleNoteContentDownloader(Operation):
    update_run_text = "Simplenote: Downloading contents"
    run_finished_text = "Simplenote: Done"

    def __init__(self, semaphore: Semaphore, notes: List[Note], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore = semaphore
        logger.info(("notes", notes))
        self.notes: List[Note] = notes

    def run(self):
        logger.warning(("# STEP: 7"))
        threads: List[Thread] = []
        for current_note in self.notes:
            assert isinstance(current_note, Note)
            assert isinstance(current_note.id, str)
            new_thread = NoteDownloader(
                current_note.id,
                self.semaphore,
                sm=self.sm,
            )
            threads.append(new_thread)
            new_thread.start()

        operation_result = [thread.join() for thread in threads]

        logger.info(("operation_result", operation_result))

        error = False
        for an_object in operation_result:
            if isinstance(an_object, Exception):
                error = True
        if not error:
            self.result = operation_result
        else:
            self.result = OperationError("MultipleNoteContentDownloader")


class GetNotesDelta(Operation):
    update_run_text = "Simplenote: Downloading note list"
    run_finished_text = "Simplenote: Done"

    def run(self):
        logger.warning(("# STEP: 2"))
        try:
            # status, note_resume = self.sm.remote.api.index(data=True)
            # assert status == 0, "Error getting notes"
            # assert isinstance(note_resume, dict), "note_resume is not a dict"
            # assert "index" in note_resume, "index not in note_resume"

            # note_objects = []
            # list__note_dict = []
            # for note in note_resume["index"]:
            #     obj = Note(**note)
            #     note_objects.append(obj)
            #     list__note_dict.append(obj.d.__dict__)
            # # logger.info(list__note_dict)
            # # logger.warning(note_objects)
            # self.result = [note for note in list__note_dict if note["deleted"] == 0]
            result: List[Note] = Note.index()
            self.result: List[Note] = result
        except Exception as err:
            logger.exception(err)
            raise err
            self.result = OperationError(err)


class NoteDeleter(Operation):
    update_run_text = "Simplenote: Deleting note"
    run_finished_text = None

    def __init__(self, *args, note: Optional[Note] = None, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(note, Note), "note is not a Note object"
        logger.info(("Simplenote: Deleting", note))
        self.note: Note = note

    def run(self):
        # logger.info(("Simplenote: Deleting", self.note["key"]))
        # result, status = self.sm.remote.api.trash_note(self.note["key"])
        logger.info(("Simplenote: Deleting", self.note))
        note: Note = self.note.trash()
        if isinstance(note, Note):
            self.result = True
        else:
            self.result = OperationError(note)


class NoteUpdater(Operation):
    update_run_text = "Simplenote: Updating note"
    run_finished_text = "Simplenote: Done"

    def __init__(self, *args, note: Optional[Note] = None, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(note, Note)
        self.note: Note = note

    def run(self):
        logger.info((self.update_run_text, self.note))

        try:
            note: Note = self.note.modify()
            self.result = note
        except Exception as err:
            logger.exception(err)
            self.result = err


class OperationManager(Singleton):
    __lock = Lock()

    # def __new__(cls, *args, **kwargs):
    #     with cls.__lock:
    #         if not cls.__instance:
    #             cls.__instance = super().__new__(cls, *args, **kwargs)
    #     # logger.info((Thread.ident, cls.__instance))
    #     return cls.__instance

    def __init__(self):
        self.operations: deque[Operation] = deque([])
        self._running = False
        self.current_operation = None

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value: bool):
        if not isinstance(value, bool):
            raise Exception(f"Invalid value for running, expected bool got {type(value)}")
        self._running = value

    def add_operation(self, operation: Operation):
        logger.warning(("# STEP: 3", operation))
        self.operations.append(operation)
        if not self.running:
            self.run()

    def check_operations(self):

        if self.current_operation == None:
            return

        # If it's still running, update the status
        if self.current_operation.is_alive():
            text = self.current_operation.update_run_text
        else:
            # If not running, show finished text call callback with result and do the next operation
            text = self.current_operation.run_finished_text
            self.current_operation.join()
            if len(self.operations) > 0:
                self.start_next_operation()
            else:
                self.running = False
                sublime.set_timeout(remove_status, 1000)

        show_message(text)
        if self.running:
            sublime.set_timeout(self.check_operations, 1000)

    def run(self):
        self.start_next_operation()
        sublime.set_timeout(self.check_operations, 1000)
        self.running = True

    def start_next_operation(self):
        # logger.info(("self.operations", self.operations))
        self.current_operation = self.operations.popleft()
        # logger.info(("Starting operation", self.current_operation))
        self.current_operation.start()
