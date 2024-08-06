from functools import cached_property
import logging
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

import sublime
import sublime_plugin

from ._config import CONFIG
from .lib.core import (
    GlobalStorage,
    PreserveSelectionAndView,
    close_view,
    on_note_changed,
    open_view,
    show_message,
    show_quick_panel,
)
from .lib.models import Note
from .lib.operations import NoteCreator, NoteDeleter, NotesIndicator, NoteUpdater, Operator


__all__ = [
    "SimplenoteMarkdownFormattingCommand",
    "SimplenoteViewCommand",
    "SimplenoteListCommand",
    "SimplenoteSyncCommand",
    "SimplenoteCreateCommand",
    "SimplenoteDeleteCommand",
]


logger = logging.getLogger()

operator = Operator()
global_storage = GlobalStorage()


# class SimplenoteTextChangeCommand(sublime_plugin.TextChangeListener):

#     def on_text_changed(self, view: sublime.View):
#         logger.warn("on_text_changed")


# class SimplenoteViewEventCommand(sublime_plugin.ViewEventListener):

#     def on_pre_save(self, view: sublime.View):
#         logger.warn("on_pre_save")


class SimplenoteMarkdownFormattingCommand(sublime_plugin.TextCommand):
    def view_is_markdown(self):
        try:
            return self.view.score_selector(0, "text.html.markdown") > 0
            return self.view.match_selector(view.sel()[0].begin(), "text.html.markdown")
        except IndexError:
            return False

    def is_enabled(self):
        """Only allow markdown documents."""
        settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
        markdown = settings.get("markdown")
        formatting = False
        if markdown and isinstance(markdown, dict):
            formatting = markdown.get("formatting")
        return formatting and self.view_is_markdown()

    def read_result(self, stdout):
        r = str(stdout, encoding="utf-8")
        return r.strip().replace("\r", "").replace("(stdin):", "")

    def run(self, edit: sublime.Edit, *args, **kwargs):
        with PreserveSelectionAndView(self.view):
            self._run(edit, *args, **kwargs)

    def _run(self, edit: sublime.Edit, *args, **kwargs):
        # logger.warning((args, kwargs, self.view.size(), os.getcwd()))
        document = sublime.Region(0, self.view.size())
        text_content = self.view.substr(document)
        title, body = Note.get_title_body(text_content)
        _body = body.encode("utf-8")

        popen_startup_info = None
        if sys.platform in ("win32", "cygwin"):
            popen_startup_info = subprocess.STARTUPINFO()
            popen_startup_info.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
            popen_startup_info.wShowWindow = subprocess.SW_HIDE

        file_obj, temp_filename = tempfile.mkstemp(suffix=".py")
        temp_handle = os.fdopen(file_obj, "wb" if sys.version_info >= (3, 0) else "w")
        temp_handle.write(_body)
        temp_handle.close()

        # command = ["~/.rbenv/shims/mdl", "-c", "~/.markdownlintrc"]
        command = ["markdownlint", "-c", "~/.markdownlintrc", temp_filename, "-f"]
        try:
            with subprocess.Popen(
                command,
                bufsize=1024 * 1024 + len(_body),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=popen_startup_info,
            ) as process:
                # process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                stdout, stderr = process.communicate()
                if stderr:
                    result = False
                    error = self.read_result(stderr)
                    outputtxt = error
                else:
                    result = self.read_result(stdout)
                    outputtxt = result
                logger.info((outputtxt))
                body = ""
                with open(temp_filename, "r") as f:
                    body = f.read()
                os.remove(temp_filename)
                content = title + "\n" + body
                # self.view.set_read_only(False)
                self.view.replace(edit, document, content)
                # self.view.set_read_only(True)
                self.view.set_status("simplenote_status_messages", "Simplenote: Markdown formatting complete")
        except FileNotFoundError as e:
            logger.error(e)
            self.view.set_status(f"simplenote_status_messages", "Simplenote: {e}")
            # _show_message(str(e))
        except Exception as e:
            logger.error(e)


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

    # def on_modified(self, view: sublime.View):
    #     logger.warn("on_modified")

    #     def flush_saves():
    #         if operator.running:
    #             sublime.set_timeout(flush_saves, self.autosave_debounce_time)
    #             return
    #         if not isinstance(note, Note):
    #             return

    #         for entry in SimplenoteViewCommand.waiting_to_save:
    #             if entry["note_id"] == note.id:

    #                 with entry["lock"]:
    #                     entry["count"] = entry["count"] - 1
    #                     if entry["count"] == 0:
    #                         view.run_command("save")
    #                 break

    #     view_filepath = view.file_name()
    #     if not isinstance(view_filepath, str):
    #         return
    #     note = Note.get_note_from_filepath(view_filepath)
    #     if not isinstance(note, Note):
    #         return

    #     found = False
    #     for entry in SimplenoteViewCommand.waiting_to_save:
    #         if entry["note_id"] == note.id:
    #             with entry["lock"]:
    #                 entry["count"] = entry["count"] + 1
    #             found = True
    #             break
    #     if not found:
    #         new_entry = {}
    #         new_entry["note_id"] = note.id
    #         new_entry["lock"] = Lock()
    #         new_entry["count"] = 1
    #         SimplenoteViewCommand.waiting_to_save.append(new_entry)
    #     sublime.set_timeout(flush_saves, self.autosave_debounce_time)

    # def on_load(self, view: sublime.View):
    #     settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
    #     note_syntax = settings.get("note_syntax")
    #     if not isinstance(note_syntax, str):
    #         show_message("`note_syntax` must be a string. Please check settings file.")
    #         return
    #     view.set_syntax_file(note_syntax)

    def on_pre_save(self, view: sublime.View):
        logger.warn(("on_pre_save"))
        view.run_command("simplenote_markdown_formatting")

    def on_post_save(self, view: sublime.View):
        logger.warn(("on_post_save", view.selection.__dict__))
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
        operator.add_operation(note_updater)


class SimplenoteListCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        if Note.tree.count:
            show_quick_panel()
        if not global_storage.get(CONFIG.SIMPLENOTE_STARTED_KEY):
            sublime.run_command("simplenote_sync")


class SimplenoteSyncCommand(sublime_plugin.ApplicationCommand):

    def merge_note(self, updated_notes: List[Note]):
        for note in updated_notes:
            if note.need_flush:
                on_note_changed(note)

    def callback(self, updated_notes: List[Note]):
        self.merge_note(updated_notes)

        sync_times = global_storage.get(CONFIG.SIMPLENOTE_SYNC_TIMES_KEY)
        if not isinstance(sync_times, int):
            global_storage.optimistic_update(CONFIG.SIMPLENOTE_SYNC_TIMES_KEY, 0)
            # raise TypeError(
            #     "Value of %s must be type %s, got %s" % (CONFIG.SIMPLENOTE_SYNC_TIMES_KEY, int, type(sync_times))
            # )
        first_sync = sync_times == 0
        if first_sync:
            show_quick_panel(True)
        global_storage.optimistic_update(CONFIG.SIMPLENOTE_SYNC_TIMES_KEY, sync_times + 1)
        global_storage.optimistic_update(CONFIG.SIMPLENOTE_STARTED_KEY, False)

    def run(self):
        if operator.running:
            return
        if global_storage.get(CONFIG.SIMPLENOTE_STARTED_KEY):
            return
        global_storage.optimistic_update(CONFIG.SIMPLENOTE_STARTED_KEY, True)

        settings = sublime.load_settings(CONFIG.SIMPLENOTE_SETTINGS_FILE_PATH)
        sync_note_number = settings.get("sync_note_number", 1000)
        if not isinstance(sync_note_number, int):
            show_message("`sync_note_number` must be an integer. Please check settings file.")
            return
        note_indicator = NotesIndicator(sync_note_number=sync_note_number)
        note_indicator.set_callback(self.callback)
        operator.add_operation(note_indicator)


class SimplenoteCreateCommand(sublime_plugin.ApplicationCommand):

    def handle_new_note(self, note: Note):
        view = open_view(note.filepath)

    def run(self):
        note_creator = NoteCreator()
        note_creator.set_callback(self.handle_new_note)
        operator.add_operation(note_creator)


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
        operator.add_operation(note_deleter)
