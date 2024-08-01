import base64
import os
import sys
import typing

from sublime import cache_path, installed_packages_path, packages_path


# try:
#     from dotenv import load_dotenv
# except ImportError:
#     import subprocess

#     subprocess.run(["pip", "install", "python-dotenv"], check=True)
#     from dotenv import load_dotenv

#     load_dotenv()
# else:
#     load_dotenv()


__all__ = [
    "CONFIG",
]


class _BaseConfig:
    # All subclasses of BaseConfig will be added to this mapping.
    mapping: typing.Dict[str, type] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.mapping[cls.__name__.lower()] = cls

    DEBUG: bool = False
    TESTING: bool = False
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, BASE_DIR)
    # LOG_DIR: str = os.path.join(BASE_DIR, "logs")
    # os.makedirs(LOG_DIR, exist_ok=True)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    SIMPLENOTE_PROJECT_NAME: str = "Simplenote"
    SIMPLENOTE_PROJECT_VERSION: str = "0.0.1"
    SIMPLENOTE_PROJECT_DESCRIPTION: str = "Sublime Text 3 & 4 plugin for Simplenote."

    SIMPLENOTE_APP_ID: str = os.getenv("SIMPLENOTE_APP_ID", "chalk-bump-f49")
    __SIMPLENOTE_APP_KEY: str = os.getenv("SIMPLENOTE_APP_KEY", "YzhjMmI4NjMzNzE1NGNkYWJjOTg5YjIzZTMwYzZiZjQ=")
    # There is no way for us to hide this key, only obfuscate it.
    # So please be kind and don't (ab)use it.
    # Simplenote/Simperium didn't have to provide us with this.
    # SIMPLENOTE_APP_KEY: bytes = base64.b64decode(__SIMPLENOTE_APP_KEY)
    SIMPLENOTE_APP_KEY: str = base64.b64decode("YzhjMmI4NjMzNzE1NGNkYWJjOTg5YjIzZTMwYzZiZjQ=").decode("utf-8")
    SIMPLENOTE_BUCKET: str = os.getenv("SIMPLENOTE_BUCKET", "note")
    SIMPLENOTE_USERNAME: str = os.getenv("SIMPLENOTE_USERNAME", "")
    SIMPLENOTE_PASSWORD: str = os.getenv("SIMPLENOTE_PASSWORD", "")
    SIMPLENOTE_DEFAULT_NOTE_TITLE: str = "untitled"
    SIMPLENOTE_SETTINGS_FILE: str = "Simplenote.sublime-settings"

    SIMPLENOTE_INSTALLED_PACKAGE_DIR = os.path.join(installed_packages_path(), SIMPLENOTE_PROJECT_NAME)
    SIMPLENOTE_PACKAGE_DIR = os.path.join(packages_path(), SIMPLENOTE_PROJECT_NAME)
    # os.makedirs(SIMPLENOTE_PACKAGE_DIR, exist_ok=True)

    SUBLIME_USER_DIR = os.path.join(packages_path(), "User")
    SIMPLENOTE_SETTINGS_FILE_PATH = SIMPLENOTE_SETTINGS_FILE
    # SIMPLENOTE_SETTINGS_FILE_PATH = os.path.join(SUBLIME_USER_DIR, SIMPLENOTE_SETTINGS_FILE)
    # if not os.path.exists(SIMPLENOTE_SETTINGS_FILE_PATH):
    #     import shutil

    #     default_settings = os.path.join(os.path.dirname(__file__), SIMPLENOTE_SETTINGS_FILE)
    #     shutil.copy(default_settings, SIMPLENOTE_SETTINGS_FILE_PATH)

    SIMPLENOTE_CACHE_DIR = os.path.join(cache_path(), SIMPLENOTE_PROJECT_NAME)
    os.makedirs(SIMPLENOTE_CACHE_DIR, exist_ok=True)
    SIMPLENOTE_TOKEN_FILE_PATH = os.path.join(SIMPLENOTE_CACHE_DIR, "token.json")
    SIMPLENOTE_NOTE_CACHE_FILE_PATH = os.path.join(SIMPLENOTE_CACHE_DIR, "note_cache.pkl")
    SIMPLENOTE_NOTES_DIR = os.path.join(SIMPLENOTE_CACHE_DIR, "notes")
    os.makedirs(SIMPLENOTE_NOTES_DIR, exist_ok=True)

    # SIMPLENOTE_STARTED: bool = False
    # SIMPLENOTE_RELOAD_CALLS: int = -1


class Development(_BaseConfig):
    """Development environment configuration"""

    DEBUG = True


class Testing(_BaseConfig):
    """Testing environment configuration"""

    TESTING = True


class Production(_BaseConfig):
    """Production environment configuration"""

    LOG_LEVEL = "WARNING"


env = os.getenv("ENV", "development")
CONFIG: typing.Type[_BaseConfig] = _BaseConfig.mapping.get(env, Development)

# Set environment variables
for attr in dir(CONFIG):
    if attr.startswith("_"):
        continue
    if attr.startswith(("SIMPLENOTE", "LOG_LEVEL")):
        os.environ[attr] = str(getattr(CONFIG, attr))
        # print("set %s: %s" % (attr, getattr(CONFIG, attr)))


if __name__ == "Simplenote._config":
    from .utils.logger import init
