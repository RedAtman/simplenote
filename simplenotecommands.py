import logging
from threading import Lock
from typing import Any, Dict, List

from _config import CONFIG
from models import Note
from operations import NoteCreator, NoteDeleter, NotesIndicator, NoteUpdater, OperationManager
from settings import Settings
from simplenote import (
    SIMPLENOTE_SETTINGS_FILE,
    SimplenoteManager,
    clear_orphaned_filepaths,
    on_note_changed,
)
import sublime
import sublime_plugin
from utils.sublime import close_view, open_view, show_message


__all__ = [
    "HandleNoteViewCommand",
    "NoteListCommand",
    "NoteSyncCommand",
    "NoteCreateCommand",
    "NoteDeleteCommand",
    "sync",
    "start",
    "reload_if_needed",
    "plugin_loaded",
]


logger = logging.getLogger()


SETTINGS = Settings(SIMPLENOTE_SETTINGS_FILE)

sm = SimplenoteManager()


class HandleNoteViewCommand(sublime_plugin.EventListener):

    waiting_to_save: List[Dict[str, Any]] = []

    def on_close(self, view: sublime.View):
        """
        A method that handles the closing of a view. Retrieves the file name from the view, gets the corresponding note using the file name, closes the note, removes the '_view' attribute from the note, and logs the note information.
        """
        return
        view_filepath = view.file_name()
        assert isinstance(view_filepath, str), "file_name is not a string: %s" % type(file_name)
        note = Note.get_note_from_filepath(view_filepath)
        assert isinstance(note, Note), "note is not a Note: %s" % type(note)
        # logger.info(view)
        logger.info(note)
        assert isinstance(note, Note), "note is not a Note: %s" % type(note)
        # note.close()
        # logger.info(note)

    def on_modified(self, view: sublime.View):

        def flush_saves():
            assert isinstance(note, Note), "note is not a Note: %s" % type(note)
            if OperationManager().running:
                sublime.set_timeout(flush_saves, 1000)
                return

            for entry in HandleNoteViewCommand.waiting_to_save:
                if entry["note_key"] == note.id:

                    with entry["lock"]:
                        entry["count"] = entry["count"] - 1
                        if entry["count"] == 0:
                            view.run_command("save")
                    break

        view_filepath = view.file_name()
        assert isinstance(view_filepath, str), "view_filepath is not a string: %s" % type(view_filepath)
        note = Note.get_note_from_filepath(view_filepath)
        assert isinstance(note, Note), "note is not a Note: %s" % type(note)
        if note:
            debounce_time = SETTINGS.get("autosave_debounce_time")
            assert isinstance(debounce_time, int)
            if not debounce_time:
                return
            debounce_time = debounce_time * 1000

            found = False
            for entry in HandleNoteViewCommand.waiting_to_save:
                if entry["note_key"] == note.id:
                    with entry["lock"]:
                        entry["count"] = entry["count"] + 1
                    found = True
                    break
            if not found:
                new_entry = {}
                new_entry["note_key"] = note.id
                new_entry["lock"] = Lock()
                new_entry["count"] = 1
                HandleNoteViewCommand.waiting_to_save.append(new_entry)
            sublime.set_timeout(flush_saves, debounce_time)

    def on_load(self, view: sublime.View):
        view_filepath = view.file_name()
        assert isinstance(view_filepath, str), "view_filepath is not a string: %s" % type(view_filepath)
        note = Note.get_note_from_filepath(view_filepath)
        assert isinstance(note, Note), "note is not a Note: %s" % type(note)
        note_syntax = SETTINGS.get("note_syntax")
        assert isinstance(note_syntax, str)
        logger.info(("note_syntax", note_syntax))
        if note and note_syntax:
            view.set_syntax_file(note_syntax)

    def on_post_save(self, view: sublime.View):
        view_filepath = view.file_name()
        assert isinstance(view_filepath, str), "view_filepath is not a string: %s" % type(view_filepath)
        local_note = Note.get_note_from_filepath(view_filepath)
        assert isinstance(local_note, Note), "note is not a Note: %s" % type(local_note)
        if not local_note:
            return
        # get the current content of the view
        view_content = view.substr(sublime.Region(0, view.size()))
        if local_note.d.content == view_content:
            return
        local_note.d.content = view_content
        # Send update
        note_updater = NoteUpdater(note=local_note, sm=sm)
        note_updater.set_callback(on_note_changed)
        OperationManager().add_operation(note_updater)


class NoteListCommand(sublime_plugin.ApplicationCommand):

    def on_select(self, selected_index: int):
        note_id = self.list__id[selected_index]
        selected_note = Note.mapper_id_note[note_id]
        filepath = selected_note.open()
        selected_note.flush()
        view = open_view(filepath)
        logger.info(("selected_note", selected_note))
        logger.info(("view", id(view), view))

    def run(self):
        if not CONFIG.SIMPLENOTE_STARTED:
            if not start():
                return

        self.list__id: List[str] = []
        self.list__title: List[str] = []
        for id, note in Note.mapper_id_note.items():
            if note.d.deleted == True:
                continue
            self.list__id.append(id)
            self.list__title.append(note.title)
        sublime.active_window().show_quick_panel(
            self.list__title,
            self.on_select,
            flags=sublime.KEEP_OPEN_ON_FOCUS_LOST,
            # on_highlight=self.on_select,
            placeholder="Select Note press key 'enter' to open",
        )


class NoteSyncCommand(sublime_plugin.ApplicationCommand):

    def merge_note(self, updated_notes: List[Note]):
        for note in updated_notes:
            if note.need_flush:
                on_note_changed(note)

    def run(self):
        show_message(self.__class__.__name__)
        note_indicator = NotesIndicator(sm=sm)
        note_indicator.set_callback(self.merge_note)
        OperationManager().add_operation(note_indicator)


class NoteCreateCommand(sublime_plugin.ApplicationCommand):

    def handle_new_note(self, note: Note):
        assert isinstance(note, Note), "note must be a Note"
        view = open_view(note.filepath)

    def run(self):
        note_creator = NoteCreator(sm=sm)
        note_creator.set_callback(self.handle_new_note)
        OperationManager().add_operation(note_creator)


class NoteDeleteCommand(sublime_plugin.ApplicationCommand):

    def handle_deletion(self, note: Note, view: sublime.View):
        close_view(view)
        note.close()

    def run(self):
        note_view: sublime.View | None = sublime.active_window().active_view()
        assert isinstance(note_view, sublime.View), "note_view must be a sublime.View"
        view_filepath: str | None = note_view.file_name()
        assert isinstance(view_filepath, str), "view_name must be a str"
        note = Note.get_note_from_filepath(view_filepath)
        assert isinstance(note, Note), "note must be a Note"
        note_deleter = NoteDeleter(note=note, sm=sm)
        note_deleter.set_callback(self.handle_deletion, {"view": note_view})
        OperationManager().add_operation(note_deleter)


def sync():
    manager = OperationManager()
    if not manager.running:
        sublime.run_command("note_sync")
    else:
        logger.info("Sync omitted")
    sync_every = SETTINGS.get("sync_every", 0)

    if sync_every > 0:
        sublime.set_timeout(sync, sync_every * 1000)


def start():
    sync()
    CONFIG.SIMPLENOTE_STARTED = True
    return CONFIG.SIMPLENOTE_STARTED


def reload_if_needed():
    logger.info(("Reloading", SETTINGS.get("autostart")))
    # RELOAD_CALLS = locals().get("RELOAD_CALLS", -1)
    RELOAD_CALLS = CONFIG.SIMPLENOTE_RELOAD_CALLS
    # Sublime calls this twice for some reason :(
    RELOAD_CALLS += 1
    if RELOAD_CALLS % 2 != 0:
        logger.debug("Reload call %s" % RELOAD_CALLS)
        return

    if SETTINGS.get("autostart"):
        sublime.set_timeout(start, 2000)  # I know...
        logger.debug("Auto Starting")


def plugin_loaded():
    # load_notes()
    logger.info(("Loaded notes number: ", len(Note.mapper_id_note)))
    clear_orphaned_filepaths()

    logger.debug(("SETTINGS.__dict__: ", SETTINGS.__dict__))
    logger.debug(("SETTINGS.username: ", SETTINGS.get("username")))
    # SETTINGS.clear_on_change("username")
    # SETTINGS.clear_on_change("password")
    # SETTINGS.add_on_change("username", reload_if_needed)
    # SETTINGS.add_on_change("password", reload_if_needed)

    reload_if_needed()


CONFIG.SIMPLENOTE_STARTED = False
