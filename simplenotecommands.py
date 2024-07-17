from functools import cached_property
import logging
from threading import Lock
from typing import Any, Dict, List

import sublime
import sublime_plugin

from models import Note
from operations import NoteCreator, NoteDeleter, NotesIndicator, NoteUpdater, OperationManager
from settings import get_settings
from simplenote import clear_orphaned_filepaths, on_note_changed
from utils.sublime import close_view, open_view, show_message


__all__ = [
    "SimplenoteViewCommand",
    "SimplenoteListCommand",
    "SimplenoteSyncCommand",
    "SimplenoteCreateCommand",
    "SimplenoteDeleteCommand",
    "sync",
    "start",
    "reload_if_needed",
    "plugin_loaded",
]


logger = logging.getLogger()


SIMPLENOTE_RELOAD_CALLS = -1
SIMPLENOTE_STARTED = False


class SimplenoteViewCommand(sublime_plugin.EventListener):

    waiting_to_save: List[Dict[str, Any]] = []

    @cached_property
    def autosave_debounce_time(self) -> int:
        _autosave_debounce_time = get_settings("autosave_debounce_time", default=1)
        if not isinstance(_autosave_debounce_time, int):
            show_message(
                "autosave_debounce_time is not an int: %s, Please check your settings" % type(autosave_debounce_time)
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
    #     note_syntax = get_settings("note_syntax")
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

    def on_select(self, selected_index: int):
        note_id = self.list__modificationDate[selected_index]
        selected_note = Note.tree.find(note_id)
        filepath = selected_note.open()
        selected_note.flush()
        view = open_view(filepath)

    def run(self):
        global SIMPLENOTE_STARTED
        if not SIMPLENOTE_STARTED:
            if not start():
                return

        self.list__modificationDate: List[float] = []
        self.list__title: List[str] = []
        for note in Note.tree.iter(reverse=True):
            if not isinstance(note, Note):
                raise Exception("note is not a Note: %s" % type(note))
            if note.d.deleted == True:
                continue
            self.list__modificationDate.append(note.d.modificationDate)
            self.list__title.append(note.title)

        sublime.active_window().show_quick_panel(
            self.list__title,
            self.on_select,
            flags=sublime.KEEP_OPEN_ON_FOCUS_LOST,
            # on_highlight=self.on_select,
            placeholder="Select Note press key 'enter' to open",
        )


class SimplenoteSyncCommand(sublime_plugin.ApplicationCommand):

    def merge_note(self, updated_notes: List[Note]):
        for note in updated_notes:
            if note.need_flush:
                on_note_changed(note)

    def run(self):
        show_message(self.__class__.__name__)
        sync_note_number = get_settings("sync_note_number", 1000)
        if not isinstance(sync_note_number, int):
            show_message("`sync_note_number` must be an integer. Please check settings file.")
            return
        note_indicator = NotesIndicator(sync_note_number=sync_note_number)
        note_indicator.set_callback(self.merge_note)
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


def sync():
    manager = OperationManager()
    if not manager.running:
        sublime.run_command("simplenote_sync")
    else:
        logger.debug("Sync omitted")

    sync_every = get_settings("sync_every", 0)
    logger.debug(("Simplenote sync_every", sync_every))
    if not isinstance(sync_every, int):
        show_message("`sync_every` must be an integer. Please check settings file.")
        return

    if sync_every > 0:
        sublime.set_timeout(sync, sync_every * 1000)


def start():
    global SIMPLENOTE_STARTED
    sync()
    SIMPLENOTE_STARTED = True
    return SIMPLENOTE_STARTED


def reload_if_needed():
    global SIMPLENOTE_RELOAD_CALLS

    # Sublime calls this twice for some reason :(
    SIMPLENOTE_RELOAD_CALLS += 1
    if SIMPLENOTE_RELOAD_CALLS % 2 != 0:
        logger.debug("Simplenote Reload call %s" % SIMPLENOTE_RELOAD_CALLS)
        return

    autostart = get_settings("autostart")
    if bool(autostart):
        autostart = True
    logger.debug(("Simplenote Reloading", autostart))
    if autostart:
        sublime.set_timeout(start, 2000)
        logger.debug("Auto Starting")


def plugin_loaded():
    # load_notes()
    logger.debug(("Loaded notes number: ", len(Note.mapper_id_note)))
    clear_orphaned_filepaths()

    # logger.debug(("SETTINGS.__dict__: ", SETTINGS.__dict__))
    # logger.debug(("SETTINGS.username: ", SETTINGS.get("username")))
    # SETTINGS.clear_on_change("username")
    # SETTINGS.clear_on_change("password")
    # SETTINGS.add_on_change("username", reload_if_needed)
    # SETTINGS.add_on_change("password", reload_if_needed)

    reload_if_needed()
