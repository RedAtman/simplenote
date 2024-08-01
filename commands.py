from functools import cached_property
import logging
from threading import Lock
from typing import Any, Dict, List

import sublime
import sublime_plugin

from ._config import CONFIG
from .lib.core import start
from .lib.gui import close_view, on_note_changed, open_view, show_message, show_quick_panel
from .lib.models import Note
from .lib.operations import NoteCreator, NoteDeleter, NotesIndicator, NoteUpdater, OperationManager


__all__ = [
    "SimplenoteViewCommand",
    "SimplenoteListCommand",
    "SimplenoteSyncCommand",
    "SimplenoteCreateCommand",
    "SimplenoteDeleteCommand",
]


logger = logging.getLogger()


SIMPLENOTE_STARTED = False


class SimplenoteViewCommand(sublime_plugin.EventListener):

    waiting_to_save: List[Dict[str, Any]] = []

    @cached_property
    def autosave_debounce_time(self) -> int:
        settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
        _autosave_debounce_time = settings.get("autosave_debounce_time", 1)
        if not isinstance(_autosave_debounce_time, int):
            show_message(
                "autosave_debounce_time is not an int: %s, Please check your settings" % type(_autosave_debounce_time)
            )
            _autosave_debounce_time = 1
        return _autosave_debounce_time * 1000

    def on_close(self, view: sublime.View):
        """
        A method that handles the closing of a view. Retrieves the file name from the view, gets the corresponding note using the file name, closes the note, removes the '_view' attribute from the note, and logs the note information.
        """
        return
        view_filepath = view.file_name()
        assert isinstance(view_filepath, str), "file_name is not a string: %s" % type(file_name)
        note = Note.get_note_from_filepath(view_filepath)
        assert isinstance(note, Note), "note is not a Note: %s" % type(note)
        assert isinstance(note, Note), "note is not a Note: %s" % type(note)
        # note.close()

    def on_modified(self, view: sublime.View):

        def flush_saves():
            if OperationManager().running:
                sublime.set_timeout(flush_saves, self.autosave_debounce_time)
                return
            if not isinstance(note, Note):
                return

            for entry in SimplenoteViewCommand.waiting_to_save:
                if entry["note_id"] == note.id:

                    with entry["lock"]:
                        entry["count"] = entry["count"] - 1
                        if entry["count"] == 0:
                            view.run_command("save")
                    break

        view_filepath = view.file_name()
        if not isinstance(view_filepath, str):
            return
        note = Note.get_note_from_filepath(view_filepath)
        if not isinstance(note, Note):
            return

        found = False
        for entry in SimplenoteViewCommand.waiting_to_save:
            if entry["note_id"] == note.id:
                with entry["lock"]:
                    entry["count"] = entry["count"] + 1
                found = True
                break
        if not found:
            new_entry = {}
            new_entry["note_id"] = note.id
            new_entry["lock"] = Lock()
            new_entry["count"] = 1
            SimplenoteViewCommand.waiting_to_save.append(new_entry)
        sublime.set_timeout(flush_saves, self.autosave_debounce_time)

    # def on_load(self, view: sublime.View):
    #     settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
    #     note_syntax = settings.get("note_syntax")
    #     if not isinstance(note_syntax, str):
    #         show_message("`note_syntax` must be a string. Please check settings file.")
    #         return
    #     view.set_syntax_file(note_syntax)

    def on_post_save(self, view: sublime.View):
        view_filepath = view.file_name()
        if not isinstance(view_filepath, str):
            return
        note = Note.get_note_from_filepath(view_filepath)
        if not isinstance(note, Note):
            return
        # get the current content of the view
        view_content = view.substr(sublime.Region(0, view.size()))
        if note.d.content == view_content:
            return
        note.content = view_content
        note_updater = NoteUpdater(note=note)
        note_updater.set_callback(on_note_changed)
        OperationManager().add_operation(note_updater)


class SimplenoteListCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        global SIMPLENOTE_STARTED
        if not SIMPLENOTE_STARTED:
            if not start():
                return
        show_quick_panel()


class SimplenoteSyncCommand(sublime_plugin.ApplicationCommand):

    def merge_note(self, updated_notes: List[Note]):
        for note in updated_notes:
            if note.need_flush:
                on_note_changed(note)

    def callback(self, updated_notes: List[Note], first_sync: bool = False):
        self.merge_note(updated_notes)
        if first_sync:
            show_quick_panel(first_sync)

    def run(self, first_sync: bool = False):
        settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
        sync_note_number = settings.get("sync_note_number", 1000)
        if not isinstance(sync_note_number, int):
            show_message("`sync_note_number` must be an integer. Please check settings file.")
            return
        note_indicator = NotesIndicator(sync_note_number=sync_note_number)
        note_indicator.set_callback(self.callback, {"first_sync": first_sync})
        OperationManager().add_operation(note_indicator)


class SimplenoteCreateCommand(sublime_plugin.ApplicationCommand):

    def handle_new_note(self, note: Note):
        view = open_view(note.filepath)

    def run(self):
        note_creator = NoteCreator()
        note_creator.set_callback(self.handle_new_note)
        OperationManager().add_operation(note_creator)


class SimplenoteDeleteCommand(sublime_plugin.ApplicationCommand):

    def handle_deletion(self, note: Note, view: sublime.View):
        close_view(view)
        note.close()

    def run(self):
        view: sublime.View | None = sublime.active_window().active_view()
        if not isinstance(view, sublime.View):
            return
        view_filepath = view.file_name()
        if not isinstance(view_filepath, str):
            return
        note = Note.get_note_from_filepath(view_filepath)
        if not isinstance(note, Note):
            return
        note_deleter = NoteDeleter(note=note)
        note_deleter.set_callback(self.handle_deletion, {"view": view})
        OperationManager().add_operation(note_deleter)
