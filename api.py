"""
:license: MIT, see LICENSE for more details.
:doc: https://simperium.com/docs/reference/http/#auth
"""

import functools
import logging
import os
import pickle
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode
import uuid

from utils.patterns.singleton.base import Singleton
from utils.request import request


logger = logging.getLogger()

__all__ = ["Simplenote"]

SIMPLENOTE_DIR = os.environ.get("SIMPLENOTE_DIR", "")
SIMPLENOTE_APP_ID: str = os.environ.get("SIMPLENOTE_APP_ID", "")
SIMPLENOTE_APP_KEY: str = os.environ.get("SIMPLENOTE_APP_KEY", "")
SIMPLENOTE_BUCKET: str = os.environ.get("SIMPLENOTE_BUCKET", "")
_SIMPLENOTE_TOKEN_FILE = os.environ.get("SIMPLENOTE_TOKEN_FILE", "simplenote_token.pkl")
SIMPLENOTE_TOKEN_FILE = os.path.join(SIMPLENOTE_DIR, _SIMPLENOTE_TOKEN_FILE)
simplenote_variables = [SIMPLENOTE_DIR, SIMPLENOTE_APP_ID, SIMPLENOTE_APP_KEY, SIMPLENOTE_BUCKET, SIMPLENOTE_TOKEN_FILE]
if not all(simplenote_variables):
    raise Exception("Simplenote variables %s must be set in environment variables" % simplenote_variables)


class URL:
    BASE: str = "https://api.simperium.com/1"
    DATA = f"{BASE}/{SIMPLENOTE_APP_ID}/{SIMPLENOTE_BUCKET}"
    __auth = f"{BASE}/{SIMPLENOTE_APP_ID}/authorize/"
    __index = DATA + "/index"
    __retrieve = DATA + "/i/%s"
    __modify = __retrieve
    __delete = __retrieve

    @classmethod
    def auth(cls):
        return cls.__auth

    @classmethod
    def index(cls, **kwargs: Dict[str, Any]):
        """
        e.g. "https://api.simperium.com/1/chalk-bump-f49/note/index?limit=10&data=true"
        """
        return cls.__index + "?" + urlencode(kwargs)

    @classmethod
    def retrieve(cls, note_id: str, version: Optional[int] = None):
        """
        e.g. "https://api.simperium.com/1/chalk-bump-f49/note/i/ba4f2735aab811e89fd89d5f0cfefda5"
        """
        if version is not None:
            return cls.__retrieve % note_id + "/v/%s" % version
        return cls.__retrieve % note_id

    @classmethod
    def modify(cls, note_id: str, version: Optional[int] = None, response: int = 1, **kwargs: Dict[str, Any]):
        """
        e.g. "https://api.simperium.com/1/chalk-bump-f49/note/i/ba4f2735aab811e89fd89d5f0cfefda5/v/2?response=1"
        """
        _: str = cls.__modify % note_id
        params = "?response=%s" % response + urlencode(kwargs)
        if version is not None:
            return _ + "/v/%s" % version + params
        return _ + params

    @classmethod
    def delete(cls, note_id: str, version: Optional[int] = None, **kwargs: Dict[str, Any]):
        """
        e.g. "https://api.simperium.com/1/chalk-bump-f49/note/i/ba4f2735aab811e89fd89d5f0cfefda5/v/2"
        """
        _: str = cls.__delete % note_id
        if version is not None:
            return _ + "/v/%s" % version + urlencode(kwargs)
        return _ + urlencode(kwargs)


class SimplenoteLoginFailed(Exception):
    pass


class Simplenote(Singleton):
    """Class for interacting with the simplenote web service"""

    def __init__(self, username: str = "", password: str = ""):
        """object constructor"""
        super().__init__()
        self.username = username
        self.password = password
        assert all(map(bool, [self.username, self.password])), "username and password must be set"
        self.header = "X-Simperium-Token"
        self.mark = "mark"
        self._token: str = ""

    @classmethod
    def authenticate(cls, username: str, password: str):
        """Method to get simplenote auth token

        Arguments:
            - username (string): simplenote email address
            - password (string): simplenote password

        Returns:
            Simplenote API token as string
        """
        headers = {"X-Simperium-API-Key": SIMPLENOTE_APP_KEY}
        request_data = {"username": username, "password": password}
        logger.debug(("request_data:", request_data, "headers:", headers))
        response = request(URL.auth(), method="POST", headers=headers, data=request_data, data_as_json=False)
        assert response.status == 200, SimplenoteLoginFailed("response.status is not 200: %s" % response.status)
        result = response.json()
        assert isinstance(result, dict), "result is not a dict: %s" % result
        if "access_token" not in result.keys():
            raise SimplenoteLoginFailed("access_token not in result: %s" % result)
        assert "access_token" in result, "access_token not in result: %s" % result
        token = result["access_token"]
        if isinstance(token, bytes):
            try:
                token = str(token, "utf-8")
            except TypeError as err:
                logger.exception(err)
                raise err
        assert isinstance(token, str), "token is not a string: %s" % token
        assert len(token) == 32, "token length is not 32: %s" % token
        with open(SIMPLENOTE_TOKEN_FILE, "wb") as fh:
            pickle.dump(token, fh)
        return token

    @functools.cached_property
    def token(self):
        """Method to retrieve an auth token.

        The cached global token is looked up and returned if it exists. If it
        is `None` a new one is requested and returned.

        Returns:
            Simplenote API token as string
        """
        if not self._token:
            try:
                with open(SIMPLENOTE_TOKEN_FILE, "rb") as fh:
                    token = pickle.load(fh, encoding="utf-8")
                    self._token = token
            except FileNotFoundError as err:
                self._token = self.authenticate(self.username, self.password)
            except EOFError as err:
                logger.exception(err)
                raise err
        return self._token

    def index(
        self,
        limit: int = 1000,
        data: bool = False,
    ):
        """Method to get the note list

        The method can be passed optional arguments to limit the
        the list to notes containing a certain tag. If omitted a list
        of all notes is returned.

        Arguments:
            - tags=[] list of tags as string: return notes that have
              at least one of these tags

        Returns:
            A tuple `(status, notes)`

            - status (int): 0 on success and -1 otherwise
            - notes (list): A list of note objects with all properties set except `content`.
            {
                'current': '666e8b00a5cc2b14e5c85722',
                'index': [
                {
                    'd':
                    {
                        'tags': [],
                        'deleted': False,
                        'shareURL': '',
                        'publishURL': '',
                        'content': '# 1',
                        'systemTags': [],
                        'modificationDate': 1718520576.085572,
                        'creationDate': 1718520569.25186
                    },
                    'id': 'd3aa2b8e6ade430bb0bd17e66b20d428',
                    'v': 2
                }],
                'mark': '666e8b00a5cc2b14e5c85722'
            }
        """
        params: Dict[str, Any] = {
            "limit": limit,
            # "data": data,
        }
        if data:
            params["data"] = "true"

        try:
            response = request(
                URL.index(**params),
                method="GET",
                params=params,
                headers={self.header: self.token},
            )
            return 0, response.data
        except IOError as err:
            logger.exception(err)
        return -1, {}

    def retrieve(self, note_id: str, version: Optional[int] = None):
        """Method to get a specific note

        Arguments:
            - note_id (string): ID of the note to get
            - version (int): optional version of the note to get

        Returns:
            A tuple `(status, note)`

            - status (int): 0 on success and -1 otherwise
            - note (dict): note object
        """
        try:
            response = request(
                URL.retrieve(note_id, version),
                method="GET",
                headers={self.header: self.token},
            )
            _version: str | None = response.headers.get("X-Simperium-Version")
            assert isinstance(_version, str)
            assert _version.isdigit()
            return 0, {"id": note_id, "v": int(_version), "d": response.data}
        except IOError as err:
            logger.exception(err)
        return -1, {}

    def modify(self, note: Dict[str, Any], note_id: Optional[str] = None, version: Optional[int] = None):
        """Method to modify or create a note

        Arguments:
            - note (dict): note object to modify
            - note_id (string): ID of the note to modify
            - version (int): optional version of the note to modify

        Returns:
            A tuple `(status, note)`

            - status (int): 0 on success and -1 otherwise
            - note (dict): note object
        """
        if not isinstance(note, dict):
            raise ValueError("note should be a string or a dict, but got %s" % note)
        if note_id is None:
            raise ValueError("note_id should be a string, but got %s" % note_id)
            note_id = uuid.uuid4().hex
        try:
            response = request(
                URL.modify(note_id, version),
                method="POST",
                headers={self.header: self.token},
                data=note,
            )
            logger.debug(("response", response))
            _version: str | None = response.headers.get("X-Simperium-Version")
            assert isinstance(_version, str), "Version should be a string, but got %s" % _version
            assert _version.isdigit(), "Version should be an integer, but got %s" % _version
            return 0, {"id": note_id, "v": int(_version), "d": response.data}
        except IOError as err:
            logger.exception(err)
        return -1, {}

    def delete(self, note_id: str, version: Optional[int] = None):
        """Method to permanently delete a note

        Arguments:
            - note_id (string): key of the note to trash

        Returns:
            A tuple `(status, note)`

            - status (int): 0 on success and -1 otherwise
            - note (dict): an empty dict or an error message
        """
        try:
            response = request(
                URL.delete(note_id, version),
                method="DELETE",
                headers={self.header: self.token},
            )
            _version: str | None = response.headers.get("X-Simperium-Version")
            assert isinstance(_version, str)
            assert _version.isdigit()
            return 0, {"id": note_id, "v": int(_version), "d": response.data}
        except IOError as err:
            logger.exception(err)
        return -1, {}

    def trash(self, note_id: str, version: Optional[int] = None):
        """Method to move a note to the trash

        Arguments:
            - note_id (string): key of the note to trash

        Returns:
            A tuple `(status, note)`

            - status (int): 0 on success and -1 otherwise
            - note (dict): the newly created note or an error message
        """
        status, note = self.retrieve(note_id, version)
        if status == -1:
            return status, note
        assert isinstance(note, dict), "note is not a dict: %s" % note
        assert "deleted" in note, "deleted not in note: %s" % note
        assert isinstance(note["deleted"], bool), "note['deleted'] is not a bool: %s" % note["deleted"]
        note["deleted"] = True
        note["modificationDate"] = time.time()
        return self.modify(note, note_id, version)


if __name__ == "__main__":
    from _config import CONFIG

    simplenote = Simplenote(username=CONFIG.SIMPLENOTE_USERNAME, password=CONFIG.SIMPLENOTE_PASSWORD)
    token = simplenote.token
    print("token: %s" % token)
