print(__file__)
from collections import deque
import logging
import re
import sys
from threading import Lock, Thread
import time
from typing import Callable, List, Optional

from api import Simplenote
from models import Note
import sublime
from utils.patterns.singleton.base import Singleton
from utils.sublime import remove_status, show_message
from simplenote import SimplenoteManager

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
    update_run_text = None
    run_finished_text = None
    simplenote_instance: Simplenote
    callback: Optional[Callable]
    callback_kwargs: Optional[dict]
    exception_callback: Optional[Callable]

    def __init__(self, *args, sm=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(sm, SimplenoteManager):
            raise Exception(f"Invalid SimplenoteManager instance, expected SimplenoteManager got {type(sm)}, {sm}")
        self.sm = sm
        self.callback = None
        self.exception_callback = None
        self.result = None

    def set_callback(self, callback: Callable, kwargs={}):
        self.callback = callback
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
            logger.warning(result)
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
        note, status = self.sm.remote.api.add_note("")
        if status == 0:
            self.result = note
            """
            {
                "tags": [],
                "deleted": False,
                "shareURL": "",
                "publishURL": "",
                "content": "",
                "systemTags": [],
                "modificationDate": 1718908023.767616,
                "creationDate": 1718908023.767616,
                "key": "902e9249ea7b4896af633c610b8c67fa",
                "version": 1,
                "modifydate": 1718908023.767616,
                "createdate": 1718908023.767616,
                "systemtags": [],
            }
            """
        else:
            self.result = OperationError(note)


class NoteDownloader(Operation):
    def __init__(self, note_id, semaphore, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.note_id = note_id
        self.semaphore = semaphore

    def run(self):
        logger.warning(("# STEP: 8"))
        self.semaphore.acquire()
        logger.info(("Simplenote: Downloading:", self.note_id))
        result, status = self.sm.remote.api.get_note(self.note_id)
        if status == 0:
            self.result = result
        else:
            self.result = OperationError(result)
        self.semaphore.release()

    def join(self):
        logger.info(("caller", sys._getframe(1).f_code.co_name))
        Thread.join(self)
        return self.result


class MultipleNoteContentDownloader(Operation):
    update_run_text = "Simplenote: Downloading contents"
    run_finished_text = "Simplenote: Done"

    def __init__(self, semaphore, *args, notes=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.notes = notes
        self.semaphore = semaphore

    def run(self):
        logger.warning(("# STEP: 7"))
        threads = []
        for current_note in self.notes:
            new_thread = NoteDownloader(
                current_note["key"],
                self.semaphore,
                sm=self.sm,
            )
            threads.append(new_thread)
            new_thread.start()

        operation_result = [thread.join() for thread in threads]

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
            result: List[Note] = self.sm.remote.notes
            self.result: List[Note] = result
        except Exception as err:
            logger.exception(err)
            raise err
            self.result = OperationError(err)


class NoteDeleter(Operation):
    update_run_text = "Simplenote: Deleting note"
    run_finished_text = None

    def __init__(self, *args, note=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.note = note

    def run(self):
        logger.info(("Simplenote: Deleting", self.note["key"]))
        result, status = self.sm.remote.api.trash_note(self.note["key"])
        if status == 0:
            self.result = True
        else:
            self.result = OperationError(result)


class NoteUpdater(Operation):
    update_run_text = "Simplenote: Updating note"
    run_finished_text = "Simplenote: Done"

    def __init__(self, *args, note=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.note = note

    def run(self):
        logger.info((self.update_run_text, self.note))
        self.note["modifydate"] = time.time()

        try:
            note_update, status = self.sm.remote.api.update_note(self.note)
            logger.info((status, type(note_update), len(note_update), note_update))
            assert status == 0, "Error updating note"
            assert isinstance(note_update, dict)
            self.result = note_update
            # if status == 0:
            #     self.result = note_update[0]
            # else:
            #     raise OperationError(note_update)
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

    def add_operation(self, operation):
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
