import sublime


def show_message(message):
    if not message:
        message = ""
    for window in sublime.windows():
        for currentView in window.views():
            currentView.set_status("Simplenote", message)


def remove_status():
    show_message(None)
