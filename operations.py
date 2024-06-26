from collections import deque
import logging
import sys
from threading import Event, Lock, Semaphore, Thread
from typing import Any, Callable, Dict, List, Optional

from models import Note
from simplenote import SimplenoteManager
import sublime
from utils.patterns.singleton.base import Singleton
from utils.sublime import remove_status, show_message


__all__ = [
    "Operation",
    "NoteCreator",
    "MultipleNoteDownloader",
    "NotesIndicator",
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
    sm: SimplenoteManager
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
        logger.info(("# STEP: 4"))
        logger.debug(("caller", sys._getframe(1).f_code.co_name))
        Thread.join(self)
        if not self.callback is None:
            logger.debug((self, self.callback, self.callback_kwargs, self.exception_callback))
            logger.debug(self.result)
            if not isinstance(self.result, Exception):
                self.callback(self.result, **self.callback_kwargs)
            elif self.exception_callback:
                self.exception_callback(self.result)
            else:
                logger.debug(str(self.result))


class NoteCreator(Operation):
    update_run_text = "Simplenote: Creating note"
    run_finished_text = "Simplenote: Done"

    def run(self):
        logger.debug("Simplenote: Creating note")
        try:
            note = Note()
            saved_note = note.create()
            assert isinstance(saved_note, Note), "Expected Note got %s" % type(saved_note)
            self.result = note
        except Exception as err:
            self.result = OperationError(err)


class MultipleNoteDownloader(Operation):
    update_run_text = "Simplenote: Downloading contents"
    run_finished_text = "Simplenote: Done"

    def __init__(self, notes: List[Note], *args, semaphore: int = 9, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore = semaphore
        logger.debug(("notes", notes))
        self.notes: List[Note] = notes

    def run(self):
        logger.info(("# STEP: 7"))
        sem = Semaphore(self.semaphore)
        done_event = Event()

        def note_retriever(note_id: str, results: List[Note]):
            with sem:
                note = Note.retrieve(note_id)
                results.append(note)
                done_event.set()

        threads: List[Thread] = []
        results: List[Note] = []
        for note in self.notes:
            assert isinstance(note, Note)
            assert isinstance(note.id, str)
            new_thread = Thread(
                target=note_retriever,
                args=(
                    note.id,
                    results,
                ),
            )
            threads.append(new_thread)
            new_thread.start()

        _ = [th.join() for th in threads]
        logger.info((self.__class__, "results", results))

        for result in results:
            if isinstance(result, Exception):
                self.result = result
                return
        self.result = results


class NotesIndicator(Operation):
    update_run_text = "Simplenote: Downloading note list"
    run_finished_text = "Simplenote: Done"

    def run(self):
        logger.info(("# STEP: 2"))
        try:
            result: List[Note] = Note.index()
            self.result: List[Note] = result
        except Exception as err:
            logger.exception(err)
            self.result = OperationError(str(err))
            raise err


class NoteDeleter(Operation):
    update_run_text = "Simplenote: Deleting note"
    run_finished_text = None

    def __init__(self, *args, note: Optional[Note] = None, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(note, Note), "note is not a Note object"
        logger.debug(("Simplenote: Deleting", note))
        self.note: Note = note

    def run(self):
        logger.debug(("Simplenote: Deleting", self.note))
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
        logger.debug((self.update_run_text, self.note))

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
    #     # logger.debug((Thread.ident, cls.__instance))
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
        assert isinstance(value, bool), "Invalid value for running, expected bool got %s" % type(value)
        self._running = value

    def add_operation(self, operation: Operation):
        logger.info(("# STEP: 3", operation))
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
        # logger.debug(("self.operations", self.operations))
        self.current_operation = self.operations.popleft()
        # logger.debug(("Starting operation", self.current_operation))
        self.current_operation.start()
