SETTINGS = None


# def init_settings(reload_if_needed: Optional(Callable) = None):
#     global SETTINGS
#     if SETTINGS is None:
#         SETTINGS = sublime.load_settings("simplenote.sublime-settings")
#         # logger.debug(("SETTINGS.__dict__: ", SETTINGS.__dict__))
#         # logger.debug(("SETTINGS.username: ", SETTINGS.get("username")))
#     if reload_if_needed:
#         SETTINGS.clear_on_change("username")
#         SETTINGS.clear_on_change("password")
#         SETTINGS.add_on_change("username", reload_if_needed)
#         SETTINGS.add_on_change("password", reload_if_needed)


def get_settings(key: str, default=None):
    "Returns value of given Emmet setting"
    global SETTINGS
    if SETTINGS is None:
        import sublime

        SETTINGS = sublime.load_settings("simplenote.sublime-settings")
    return SETTINGS.get(key, default)


# Settings = type(
#     "Settings",
#     (
#         Json2Obj,
#         Singleton,
#     ),
#     {},
# )
