print(__file__)
import copy
import functools
from functools import cmp_to_key
import logging
import os
import sys
from threading import Lock, Semaphore
import time
from typing import List

from models import Note

# from config import CONFIG
from operations import (
    GetNotesDelta,
    MultipleNoteContentDownloader,
    NoteCreator,
    NoteDeleter,
    NoteUpdater,
    OperationManager,
)
from simplenote import (  # cmp_to_key,
    CONFIG,
    SETTINGS,
    TEMP_PATH,
    SimplenoteManager,
    get_note_name,
    handle_open_filename_change,
    open_note,
    sort_notes,
    synch_note_resume,
    update_note,
    write_note_to_path,
)
import sublime
import sublime_plugin
from utils.sublime import close_view, show_message


logger = logging.getLogger()

sm = SimplenoteManager()


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
        note = sm.local.get_note_from_path(view_filepath)
        if note:
            debounce_time = SETTINGS.get("autosave_debounce_time")
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
        note = sm.local.get_note_from_path(view_filepath)
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
        for note in sm.local.notes:
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
                    filepath = sm.local.get_path_for_note(note)
                    write_note_to_path(note, filepath)
                    sublime.set_timeout(functools.partial(open_view.run_command, "revert"), 0)
                break
        sm.local.notes.sort(key=cmp_to_key(sort_notes), reverse=True)
        sm.local.save_notes()

    def on_post_save(self, view):
        view_filepath = view.file_name()
        note = sm.local.get_note_from_path(view_filepath)
        if note:
            # Update with new content
            updated_note = copy.deepcopy(note)
            # Handle when the note changes elsewhere and the user goes to that tab:
            # sublime reloads the view, it's handled as changed and sent here
            if "content" in updated_note and updated_note["content"] == self.get_current_content(view):
                return
            updated_note["content"] = self.get_current_content(view)
            # Send update
            update_op = NoteUpdater(note=updated_note, sm=sm)
            update_op.set_callback(
                self.handle_note_changed,
                {"content": updated_note["content"], "old_file_path": view_filepath, "open_view": view},
            )
            OperationManager().add_operation(update_op)


class ShowNotesCommand(sublime_plugin.ApplicationCommand):

    def handle_selected(self, selected_index):
        if not selected_index > -1:
            return

        selected_note = sm.local.notes[selected_index]
        open_note(selected_note)

    def run(self):
        if not CONFIG.STARTED:
            if not start():
                return

        i = 0
        keys = []
        for note in sm.local.notes:
            i += 1
            title = get_note_name(note)
            keys.append(title)
        logger.info("ShowNotesCommand: notes len: %s" % len(keys))
        sublime.active_window().show_quick_panel(keys, self.handle_selected)


class StartSyncCommand(sublime_plugin.ApplicationCommand):

    def set_result(self, new_notes):
        sm.local.notes = new_notes
        sm.local.notes.sort(key=cmp_to_key(sort_notes), reverse=True)

    def merge_delta(self, _updated_note_resume: List[Note], existing_notes):
        logger.warning(("# STEP: 5"))
        logger.info(("caller", sys._getframe(1).f_code.co_name))
        updated_note_resume = [note.d.__dict__ for note in _updated_note_resume if note.d.deleted == 0]
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

        sm.local.notes = existing_notes
        sm.local.save_notes()
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
                    open_files_dirty.append(os.path.split(view.file_name())[1])
                else:
                    open_files_ok.append(os.path.split(view.file_name())[1])

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
            down_op = MultipleNoteContentDownloader(sem, sm=sm, notes=lu)
            down_op.set_callback(self.merge_open, {"existing_notes": notes, "dirty": True})
            OperationManager().add_operation(down_op)
        if ls:
            down_op = MultipleNoteContentDownloader(sem, sm=sm, notes=ls)
            down_op.set_callback(self.merge_open, {"existing_notes": notes})
            OperationManager().add_operation(down_op)
        if others:
            down_op = MultipleNoteContentDownloader(sem, sm=sm, notes=others)
            down_op.set_callback(self.merge_notes, {"existing_notes": notes})
            OperationManager().add_operation(down_op)

    def merge_open(self, updated_notes, existing_notes, dirty=False):
        logger.info(("caller", sys._getframe(1).f_code.co_name))
        logger.info(("updated_notes", updated_notes, "existing_notes", existing_notes, "dirty", dirty))
        auto_overwrite_on_conflict = SETTINGS.get("on_conflict_use_server")
        do_nothing_on_conflict = SETTINGS.get("on_conflict_leave_alone")
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
                            old_file_path = sm.local.get_path_for_note(note)
                            new_file_path = sm.local.get_path_for_note(updated_note)
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

        sm.local.notes = existing_notes
        sm.local.save_notes()
        self.set_result(existing_notes)

    def run(self):
        logger.warning(("# STEP: 1"))
        show_message("show_message: Synching")
        get_delta_op = GetNotesDelta(sm=sm)
        # logger.info(("notes", sm.local.notes))
        get_delta_op.set_callback(self.merge_delta, {"existing_notes": sm.local.notes})
        OperationManager().add_operation(get_delta_op)


class CreateNoteCommand(sublime_plugin.ApplicationCommand):

    def handle_new_note(self, result):
        if result:
            update_note(result, result)
            sm.local.notes.append(result)
            sm.local.notes.sort(key=cmp_to_key(sort_notes), reverse=True)
            sm.local.save_notes()
            open_note(result)

    def run(self):
        creation_op = NoteCreator(sm=sm)
        creation_op.set_callback(self.handle_new_note)
        OperationManager().add_operation(creation_op)


class DeleteNoteCommand(sublime_plugin.ApplicationCommand):

    def handle_deletion(self, result):
        logger.info((sm.local.notes, self.note))
        sm.local.notes.remove(self.note)
        sm.local.save_notes()
        try:
            # TODO: FileNotFoundError: [Errno 2] No such file or directory: '/Users/nut/Library/Application Support/Sublime Text/Packages/Simplenote/temp/555 (2b6b91f48c4042548d8cbb78dc3afc7e)'
            os.remove(sm.local.get_path_for_note(self.note))
        except OSError as err:
            logger.exception(err)
            pass
        close_view(self.note_view)

    def run(self):

        self.note_view = sublime.active_window().active_view()
        self.note = sm.local.get_note_from_path(self.note_view.file_name())
        if self.note:
            deletion_op = NoteDeleter(note=self.note, sm=sm)
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
    sync_every = SETTINGS.get("sync_every", 0) or 0
    if sync_every > 0:
        sublime.set_timeout(sync, sync_every * 1000)


def start():
    sync()
    CONFIG.STARTED = True
    return CONFIG.STARTED


def reload_if_needed():
    logger.info(("Reloading", SETTINGS.get("autostart")))
    # RELOAD_CALLS = locals().get("RELOAD_CALLS", -1)
    RELOAD_CALLS = CONFIG.RELOAD_CALLS
    # Sublime calls this twice for some reason :(
    RELOAD_CALLS += 1
    if RELOAD_CALLS % 2 != 0:
        logger.info("Reload call %s" % RELOAD_CALLS)
        return

    if SETTINGS.get("autostart"):
        sublime.set_timeout(start, 2000)  # I know...
        logger.info("Auto Starting")


def plugin_loaded():
    # sm.local.load_notes()
    if len(sm.local.notes):
        logger.info(("Loaded notes: ", sm.local.notes[0]))
    note_files = [note["filename"] for note in sm.local.notes]
    if not os.path.exists(TEMP_PATH):
        os.makedirs(TEMP_PATH)
    for f in os.listdir(TEMP_PATH):
        if f not in note_files:
            os.remove(os.path.join(TEMP_PATH, f))

    logger.info(("SETTINGS.username: ", SETTINGS.get("username")))
    SETTINGS.clear_on_change("username")
    SETTINGS.clear_on_change("password")
    SETTINGS.add_on_change("username", reload_if_needed)
    SETTINGS.add_on_change("password", reload_if_needed)

    reload_if_needed()
