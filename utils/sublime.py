import sublime


__all__ = [
    "show_message",
    "remove_status",
    "close_view",
]


def show_message(message: str):
    if not message:
        message = ""
    for window in sublime.windows():
        for currentView in window.views():
            currentView.set_status("Simplenote", message)


def remove_status():
    show_message(None)


def close_view(view: sublime.View):
    view.set_scratch(True)
    view_window = view.window()
    if not view_window:
        view_window = sublime.active_window()
    view_window.focus_view(view)
    view_window.run_command("close_file")
