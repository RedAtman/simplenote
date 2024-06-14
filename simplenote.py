import copy
from datetime import datetime
import functools
import logging
from os import listdir, makedirs, path, remove
import pickle
import sys
from threading import Lock, Semaphore
import time
from typing import Any, List

# https://www.sublimetext.com/docs/api_reference.html
import sublime
import sublime_plugin

from api import Simplenote
from config import CONFIG
from operations import (
    GetNotesDelta,
    MultipleNoteContentDownloader,
    NoteCreator,
    NoteDeleter,
    NoteUpdater,
    OperationManager,
)
from utils.patterns.singleton.base import Singleton
from utils.sublime import show_message


logger = logging.getLogger()


PACKAGE_PATH = path.join(sublime.packages_path(), CONFIG.PROJECT_NAME)
TEMP_PATH = path.join(PACKAGE_PATH, "temp")


class SimplenoteManager(Singleton):
    SETTINGS = sublime.load_settings(CONFIG.SETTINGS_FILE)
    NOTE_CACHE_FILE_PATH = path.join(PACKAGE_PATH, CONFIG.NOTE_CACHE_FILE)
    notes: List[Any] = []

    def __init__(self):
        # self._instance: Simplenote = Simplenote(self.SETTINGS.get("username"), self.SETTINGS.get("password"))
        self._instance: Simplenote = Simplenote(CONFIG.SIMPLENOTE_USERNAME, CONFIG.SIMPLENOTE_PASSWORD)

    @functools.cached_property
    def instance(self):
        logger.info(("instance", self._instance))
        assert isinstance(self._instance, Simplenote), f"Invalid Simplenote instance: {self._instance}"
        return self._instance

    @classmethod
    def load_notes(cls):
        try:
            with open(cls.NOTE_CACHE_FILE_PATH, "rb") as cache_file:
                cls.notes = pickle.load(cache_file, encoding="utf-8")
        except (EOFError, IOError, FileNotFoundError) as err:
            logger.exception(err)
            with open(cls.NOTE_CACHE_FILE_PATH, "w+b") as cache_file:
                pickle.dump(cls.notes, cache_file)

        logger.info(("Loaded notes length: ", len(cls.notes)))
        return cls.notes

    @staticmethod
    def _save_notes(NOTE_CACHE_FILE_PATH: str, notes: List[Any]):
        with open(NOTE_CACHE_FILE_PATH, "w+b") as cache_file:
            pickle.dump(notes, cache_file)

    @classmethod
    def save_notes(cls):
        cls._save_notes(cls.NOTE_CACHE_FILE_PATH, cls.notes)


simplenote_manager = SimplenoteManager()


def cmp_to_key(mycmp):
    "Convert a cmp= function into a key= function"

    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            logger.info((mycmp, mycmp(self.obj, other.obj), self.obj, other.obj))
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0

    return K


def sort_notes(a_note, b_note):
    if "pinned" in a_note["systemtags"]:
        return 1
    elif "pinned" in b_note["systemtags"]:
        return -1
    else:
        date_a = datetime.fromtimestamp(float(a_note["modifydate"]))
        date_b = datetime.fromtimestamp(float(b_note["modifydate"]))
        return (date_a > date_b) - (date_a < date_b)


def write_note_to_path(note, filepath):
    f = open(filepath, "wb")
    try:
        content = note["content"]
        f.write(content.encode("utf-8"))
    except KeyError as err:
        logger.exception(err)
        pass
    f.close()


def open_note(note, window=None):
    if not window:
        window = sublime.active_window()
    filepath = get_path_for_note(note)
    write_note_to_path(note, filepath)
    return window.open_file(filepath)


def get_note_name(note):
    try:
        content = note["content"]
    except Exception as err:
        return CONFIG.DEFAULT_NOTE_TITLE
    index = content.find("\n")
    if index > -1:
        title = content[:index]
    else:
        if content:
            title = content
        else:
            title = CONFIG.DEFAULT_NOTE_TITLE
    return title


def get_filename_for_note(note):
    # Take out invalid characters from title and use that as base for the name
    import string

    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    note_name = get_note_name(note)
    base = "".join(c for c in note_name if c in valid_chars)
    # Determine extension based on title
    extension_map = simplenote_manager.SETTINGS.get("title_extension_map")
    extension = ""
    if extension_map:
        for item in extension_map:
            import re

            pattern = re.compile(item["title_regex"], re.UNICODE)
            if re.search(pattern, note_name):
                extension = "." + item["extension"]
                break

    return base + " (" + note["key"] + ")" + extension


def get_path_for_note(note):
    return path.join(TEMP_PATH, get_filename_for_note(note))


def get_note_from_path(view_filepath):
    note = None
    if view_filepath:
        if path.dirname(view_filepath) == TEMP_PATH:
            note_filename = path.split(view_filepath)[1]
            note = [note for note in simplenote_manager.notes if get_filename_for_note(note) == note_filename]
            if not note:
                import re

                pattern = re.compile(r"\((.*?)\)")
                results = re.findall(pattern, note_filename)
                if results:
                    noteKey = results[len(results) - 1]
                    note = [note for note in simplenote_manager.notes if note["key"] == noteKey]
            if note:
                note = note[0]

    return note


def handle_open_filename_change(old_file_path, updated_note):
    new_file_path = get_path_for_note(updated_note)
    old_note_view = None
    new_view = None
    # If name changed
    if old_file_path != new_file_path:
        # Save the current active view because we might lose the focus
        old_active_view = sublime.active_window().active_view()
        # Search for the view of the open note
        for view_list in [window.views() for window in sublime.windows()]:
            for view in view_list:
                if view.file_name() == old_file_path:
                    old_note_view = view
                    break
        # If found
        if old_note_view:
            # Open the note in a new view
            new_view = open_note(updated_note, old_note_view.window())
            # Close the old dirty note
            old_note_view_id = old_note_view.id()
            old_active_view_id = old_active_view.id()
            if old_note_view.window():
                old_note_window_id = old_note_view.window().id()
            else:
                old_note_window_id = sublime.active_window()  # Sometimes this happens on Sublime 2...
            close_view(old_note_view)
            # Focus on the new view or on the previous one depending
            # on where we were
            if old_note_view_id == old_active_view_id:
                old_note_window = [window for window in sublime.windows() if window.id() == old_note_window_id]
                if old_note_window:
                    old_note_window[0].focus_view(new_view)
            else:
                sublime.active_window().focus_view(old_active_view)
        try:
            remove(old_file_path)
        except OSError as err:
            logger.exception(err)
        return True
    return False


def close_view(view):
    view.set_scratch(True)
    view_window = view.window()
    if not view_window:
        view_window = sublime.active_window()
    view_window.focus_view(view)
    view_window.run_command("close_file")


def synch_note_resume(existing_note_entry, updated_note_resume):
    for key in updated_note_resume:
        existing_note_entry[key] = updated_note_resume[key]


def update_note(existing_note, updated_note):
    logger.info(("existing_note", existing_note, "updated_note", updated_note))
    synch_note_resume(existing_note, updated_note)
    existing_note["local_modifydate"] = time.time()
    existing_note["needs_update"] = False
    filename = get_filename_for_note(existing_note)
    logger.info(("Updating note", "filename", filename, "existing_note", existing_note))
    existing_note["filename"] = filename


class HandleNoteViewCommand(sublime_plugin.EventListener):

    waiting_to_save = []

    def on_modified(self, view):

        def flush_saves():
            if OperationManager().running:
                sublime.set_timeout(flush_saves, 1000)
                return

            for entry in HandleNoteViewCommand.waiting_to_save:
                if entry["note_key"] == note["key"]:

                    with entry["lock"]:
                        entry["count"] = entry["count"] - 1
                        if entry["count"] == 0:
                            view.run_command("save")
                    break

        view_filepath = view.file_name()
        note = get_note_from_path(view_filepath)
        if note:
            debounce_time = simplenote_manager.SETTINGS.get("autosave_debounce_time")
            if not debounce_time:
                return
            debounce_time = debounce_time * 1000

            found = False
            for entry in HandleNoteViewCommand.waiting_to_save:
                if entry["note_key"] == note["key"]:
                    with entry["lock"]:
                        entry["count"] = entry["count"] + 1
                    found = True
                    break
            if not found:
                new_entry = {}
                new_entry["note_key"] = note["key"]
                new_entry["lock"] = Lock()
                new_entry["count"] = 1
                HandleNoteViewCommand.waiting_to_save.append(new_entry)
            sublime.set_timeout(flush_saves, debounce_time)

    def on_load(self, view):
        view_filepath = view.file_name()
        note = get_note_from_path(view_filepath)
        SETTINGS = sublime.load_settings(CONFIG.SETTINGS_FILE)
        note_syntax = SETTINGS.get("note_syntax")
        logger.info(("note_syntax", note_syntax))
        if note and note_syntax:
            view.set_syntax_file(note_syntax)

    def get_current_content(self, view):
        return view.substr(sublime.Region(0, view.size()))

    def handle_note_changed(self, modified_note_resume, content, old_file_path, open_view):
        # We get all the resume data back. We have to merge it
        # with our data (extended fields and content)
        for note in simplenote_manager.notes:
            if note["key"] == modified_note_resume["key"]:
                # Set content to the updated one
                # or to the view's content if we don't have any update
                updated_from_server = False
                if not "content" in modified_note_resume:
                    modified_note_resume["content"] = content
                else:
                    updated_from_server = True

                logger.info(("note", note))
                update_note(note, modified_note_resume)  # Update all fields
                name_changed = handle_open_filename_change(old_file_path, note)
                # If we didn't reopen the view with the name changed, but the content has changed
                # we have to update the view anyway
                if updated_from_server and not name_changed:
                    filepath = get_path_for_note(note)
                    write_note_to_path(note, filepath)
                    sublime.set_timeout(functools.partial(open_view.run_command, "revert"), 0)
                break
        simplenote_manager.notes.sort(key=cmp_to_key(sort_notes), reverse=True)
        simplenote_manager.save_notes()

    def on_post_save(self, view):
        view_filepath = view.file_name()
        note = get_note_from_path(view_filepath)
        if note:
            # Update with new content
            updated_note = copy.deepcopy(note)
            # Handle when the note changes elsewhere and the user goes to that tab:
            # sublime reloads the view, it's handled as changed and sent here
            if "content" in updated_note and updated_note["content"] == self.get_current_content(view):
                return
            updated_note["content"] = self.get_current_content(view)
            # Send update
            update_op = NoteUpdater(note=updated_note, simplenote_instance=simplenote_manager.instance)
            update_op.set_callback(
                self.handle_note_changed,
                {"content": updated_note["content"], "old_file_path": view_filepath, "open_view": view},
            )
            OperationManager().add_operation(update_op)


class ShowNotesCommand(sublime_plugin.ApplicationCommand):

    def handle_selected(self, selected_index):
        if not selected_index > -1:
            return

        selected_note = simplenote_manager.notes[selected_index]
        open_note(selected_note)

    def run(self):
        if not CONFIG.STARTED:
            if not start():
                return

        i = 0
        keys = []
        for note in simplenote_manager.notes:
            i += 1
            title = get_note_name(note)
            keys.append(title)
        logger.info("ShowNotesCommand: notes len: %s" % len(keys))
        sublime.active_window().show_quick_panel(keys, self.handle_selected)


class StartSyncCommand(sublime_plugin.ApplicationCommand):

    def set_result(self, new_notes):
        simplenote_manager.notes = new_notes
        simplenote_manager.notes.sort(key=cmp_to_key(sort_notes), reverse=True)

    def merge_delta(self, updated_note_resume, existing_notes):
        logger.warning(("# STEP: 5"))
        logger.info(("caller", sys._getframe(1).f_code.co_name))
        logger.info(("updated_note_resume", updated_note_resume, "existing_notes", existing_notes))
        # Here we create the note_resume we use on the rest of the app.
        # The note_resume we store consists of:
        #   The note resume as it comes from the simplenote api.
        #   The title, filename and last modified date of the local cache entry

        # Look at the new resume and find existing entries
        for current_updated_note_resume in updated_note_resume:
            existing_note_entry = None
            for existing_note in existing_notes:
                if existing_note["key"] == current_updated_note_resume["key"]:
                    existing_note_entry = existing_note
                    break
            # If we have it already
            if existing_note_entry:
                # Mark for update if needed
                try:
                    # Note with old content
                    if existing_note_entry["local_modifydate"] < float(current_updated_note_resume["modifydate"]):
                        synch_note_resume(existing_note_entry, current_updated_note_resume)
                        existing_note_entry["needs_update"] = True
                    else:
                        # Up to date note
                        existing_note_entry["needs_update"] = False
                except KeyError as e:
                    # Note that never got the content downloaded:
                    existing_note_entry["needs_update"] = True

            # New note
            else:
                new_note_entry = {"needs_update": True}
                synch_note_resume(new_note_entry, current_updated_note_resume)
                existing_notes.append(new_note_entry)

        # Look at the existing notes to find deletions
        updated_note_resume_keys = [note["key"] for note in updated_note_resume]
        deleted_notes = [
            deleted_note for deleted_note in existing_notes if deleted_note["key"] not in updated_note_resume_keys
        ]
        for deleted_note in deleted_notes:
            existing_notes.remove(deleted_note)

        simplenote_manager.notes = existing_notes
        simplenote_manager.save_notes()
        self.notes_synch(existing_notes)

    def notes_synch(self, notes):
        logger.warning(("# STEP: 6"))
        # Here we synch updated notes in order of priority.
        # Open notes:
        #   Locally unsaved
        #   Locally saved
        # Other notes in order of modifydate and priority
        logger.info(("caller", sys._getframe(1).f_code.co_name, "notes", notes))
        open_files_dirty = []
        open_files_ok = []
        for view_list in [window.views() for window in sublime.windows()]:
            for view in view_list:
                if view.file_name() == None:
                    continue

                if view.is_dirty():
                    open_files_dirty.append(path.split(view.file_name())[1])
                else:
                    open_files_ok.append(path.split(view.file_name())[1])

        # Classify notes
        lu = []
        ls = []
        others = []
        for note in notes:

            if not note["needs_update"]:
                continue

            try:
                filename = note["filename"]
            except KeyError as err:
                # logger.exception(err)
                others.append(note)
                continue

            if filename in open_files_dirty:
                lu.append(note)
            elif filename in open_files_ok:
                ls.append(note)
            else:
                others.append(note)

        # Sorted by priority/importance
        lu.sort(key=cmp_to_key(sort_notes), reverse=True)
        ls.sort(key=cmp_to_key(sort_notes), reverse=True)
        others.sort(key=cmp_to_key(sort_notes), reverse=True)
        logger.info(("lu", lu, "ls", ls, "others", others))

        # Start updates
        sem = Semaphore(3)
        show_message("Downloading content")
        if lu:
            down_op = MultipleNoteContentDownloader(sem, simplenote_instance=simplenote_manager.instance, notes=lu)
            down_op.set_callback(self.merge_open, {"existing_notes": notes, "dirty": True})
            OperationManager().add_operation(down_op)
        if ls:
            down_op = MultipleNoteContentDownloader(sem, simplenote_instance=simplenote_manager.instance, notes=ls)
            down_op.set_callback(self.merge_open, {"existing_notes": notes})
            OperationManager().add_operation(down_op)
        if others:
            down_op = MultipleNoteContentDownloader(sem, simplenote_instance=simplenote_manager.instance, notes=others)
            down_op.set_callback(self.merge_notes, {"existing_notes": notes})
            OperationManager().add_operation(down_op)

    def merge_open(self, updated_notes, existing_notes, dirty=False):
        logger.info(("caller", sys._getframe(1).f_code.co_name))
        logger.info(("updated_notes", updated_notes, "existing_notes", existing_notes, "dirty", dirty))
        auto_overwrite_on_conflict = simplenote_manager.SETTINGS.get("on_conflict_use_server")
        do_nothing_on_conflict = simplenote_manager.SETTINGS.get("on_conflict_leave_alone")
        update = False

        # If it's not a conflict or it's a conflict we can resolve
        if (not dirty) or (dirty and not do_nothing_on_conflict):

            # If we don't have an overwrite policy, ask the user
            if (not auto_overwrite_on_conflict) and dirty and len(updated_notes) > 0:
                note_names = "\n".join([get_note_name(updated_note) for updated_note in updated_notes])
                update = sublime.ok_cancel_dialog("Note(s):\n%s\nAre in conflict. Overwrite?" % note_names, "Overwrite")

            if (not dirty) or update or auto_overwrite_on_conflict:
                # Update notes if the change is clean, or we were asked to update
                for note in existing_notes:
                    for updated_note in updated_notes:
                        # If we find the updated note
                        if note["key"] == updated_note["key"]:
                            old_file_path = get_path_for_note(note)
                            new_file_path = get_path_for_note(updated_note)
                            # Update contents
                            write_note_to_path(updated_note, new_file_path)
                            # Handle filename change (note has the old filename value)
                            handle_open_filename_change(old_file_path, updated_note)
                            # Reload view of the note if it's selected
                            for view in [window.active_view() for window in sublime.windows()]:
                                if view.file_name() == new_file_path:
                                    sublime.set_timeout(functools.partial(view.run_command, "revert"), 0)
                            break

            # Merge
            self.merge_notes(updated_notes, existing_notes)

    def merge_notes(self, updated_notes, existing_notes):
        logger.info(("caller", sys._getframe(1).f_code.co_name))
        logger.info(("updated_notes", updated_notes, "existing_notes", existing_notes))
        # Merge
        for note in existing_notes:

            if not note["needs_update"]:
                continue

            for updated_note in updated_notes:
                try:
                    if note["key"] == updated_note["key"]:
                        update_note(note, updated_note)
                except KeyError as err:
                    logger.exception(err)
                    logger.info(("caller", sys._getframe(1).f_code.co_name))
                    logger.warning(("note", note, "updated_note", updated_note))

        simplenote_manager.notes = existing_notes
        simplenote_manager.save_notes()
        self.set_result(existing_notes)

    def run(self):
        logger.warning(("# STEP: 1"))
        show_message("show_message: Synching")
        get_delta_op = GetNotesDelta(simplenote_instance=simplenote_manager.instance)
        logger.info(("notes", simplenote_manager.notes))
        get_delta_op.set_callback(self.merge_delta, {"existing_notes": simplenote_manager.notes})
        OperationManager().add_operation(get_delta_op)


class CreateNoteCommand(sublime_plugin.ApplicationCommand):

    def handle_new_note(self, result):
        if result:
            logger.info(("result", result))
            update_note(result, result)
            simplenote_manager.notes.append(result)
            simplenote_manager.notes.sort(key=cmp_to_key(sort_notes), reverse=True)
            simplenote_manager.save_notes()
            open_note(result)

    def run(self):
        creation_op = NoteCreator(simplenote_instance=simplenote_manager.instance)
        creation_op.set_callback(self.handle_new_note)
        OperationManager().add_operation(creation_op)


class DeleteNoteCommand(sublime_plugin.ApplicationCommand):

    def handle_deletion(self, result):
        logger.info((simplenote_manager.notes, self.note))
        simplenote_manager.notes.remove(self.note)
        simplenote_manager.save_notes()
        try:
            # TODO: FileNotFoundError: [Errno 2] No such file or directory: '/Users/nut/Library/Application Support/Sublime Text/Packages/Simplenote/temp/555 (2b6b91f48c4042548d8cbb78dc3afc7e)'
            remove(get_path_for_note(self.note))
        except OSError as err:
            logger.exception(err)
            pass
        close_view(self.note_view)

    def run(self):

        self.note_view = sublime.active_window().active_view()
        self.note = get_note_from_path(self.note_view.file_name())
        if self.note:
            deletion_op = NoteDeleter(note=self.note, simplenote_instance=simplenote_manager.instance)
            deletion_op.set_callback(self.handle_deletion)
            OperationManager().add_operation(deletion_op)


def sync():
    try:
        logger.info("Sync OperationManager: %s" % OperationManager)
        manager = OperationManager()
    except (ImportError, Exception) as err:
        logger.exception(err)
        return
    if not isinstance(manager, OperationManager):
        raise TypeError("Invalid OperationManager instance: %s" % type(manager))
    if not manager.running:
        logger.info(("Syncing", time.time()))
        sublime.run_command("start_sync")
    else:
        logger.info("Sync omited")
        # logger.info("Sync omited %s" % time.time())
    sync_every = simplenote_manager.SETTINGS.get("sync_every", 0) or 0
    if sync_every > 0:
        sublime.set_timeout(sync, sync_every * 1000)


def start():
    sync()
    CONFIG.STARTED = True
    return CONFIG.STARTED


def reload_if_needed():
    logger.info(("Reloading", simplenote_manager.SETTINGS.get("autostart")))
    # RELOAD_CALLS = locals().get("RELOAD_CALLS", -1)
    RELOAD_CALLS = CONFIG.RELOAD_CALLS
    # Sublime calls this twice for some reason :(
    RELOAD_CALLS += 1
    if RELOAD_CALLS % 2 != 0:
        logger.info("Reload call %s" % RELOAD_CALLS)
        return

    if simplenote_manager.SETTINGS.get("autostart"):
        sublime.set_timeout(start, 2000)  # I know...
        logger.info("Auto Starting")


def plugin_loaded():
    simplenote_manager.load_notes()
    if len(simplenote_manager.notes):
        logger.info(("Loaded notes: ", simplenote_manager.notes[0]))
    note_files = [note["filename"] for note in simplenote_manager.notes]
    if not path.exists(TEMP_PATH):
        makedirs(TEMP_PATH)
    for f in listdir(TEMP_PATH):
        if f not in note_files:
            remove(path.join(TEMP_PATH, f))

    logger.info(("SETTINGS.username: ", simplenote_manager.SETTINGS.get("username")))
    simplenote_manager.SETTINGS.clear_on_change("username")
    simplenote_manager.SETTINGS.clear_on_change("password")
    simplenote_manager.SETTINGS.add_on_change("username", reload_if_needed)
    simplenote_manager.SETTINGS.add_on_change("password", reload_if_needed)

    reload_if_needed()
