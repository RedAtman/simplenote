import base64
import os
import sys
import typing


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
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    SIMPLENOTE_PROJECT_NAME: str = "Simplenote"
    SIMPLENOTE_PROJECT_VERSION: str = "0.0.1"
    SIMPLENOTE_PROJECT_DESCRIPTION: str = "Sublime Text 3/4 plugin for Simplenote."

    SIMPLENOTE_BASE_DIR: str = BASE_DIR
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
    SIMPLENOTE_SETTINGS_FILE: str = "simplenote.sublime-settings"
    SIMPLENOTE_TOKEN_FILE: str = os.getenv("SIMPLENOTE_TOKEN_FILE", "simplenote_token.pkl")
    SIMPLENOTE_STARTED: bool = False
    SIMPLENOTE_RELOAD_CALLS: int = -1
    SIMPLENOTE_NOTE_FETCH_LENGTH: int = 1
    SIMPLENOTE_NOTE_CACHE_FILE: str = "note_cache.pkl"
    SIMPLENOTE_DEFAULT_NOTE_TITLE: str = "untitled"


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


from importlib import import_module


import_module("utils.logger.init")
