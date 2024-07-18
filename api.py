"""
:license: MIT, see LICENSE for more details.
:doc: https://simperium.com/docs/reference/http/#auth
"""

import base64
import functools
import logging
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from uuid import uuid4

from utils.patterns.singleton.base import Singleton
from utils.request import Response, request


logger = logging.getLogger()

__all__ = ["Simplenote"]

SIMPLENOTE_BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SIMPLENOTE_APP_ID: str = "chalk-bump-f49"
SIMPLENOTE_APP_KEY: str = base64.b64decode("YzhjMmI4NjMzNzE1NGNkYWJjOTg5YjIzZTMwYzZiZjQ=").decode("utf-8")
SIMPLENOTE_BUCKET: str = "note"
_SIMPLENOTE_TOKEN_FILE = "simplenote_token.pkl"
SIMPLENOTE_TOKEN_FILE = os.path.join(SIMPLENOTE_BASE_DIR, _SIMPLENOTE_TOKEN_FILE)


class URL:
    BASE: str = "simperium.com/1"
    AUTH = f"https://auth.{BASE}"
    DATA = f"https://api.{BASE}/{SIMPLENOTE_APP_ID}/{SIMPLENOTE_BUCKET}"
    __auth = f"{AUTH}/{SIMPLENOTE_APP_ID}/authorize/"
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
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


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
        response = request(URL.auth(), method="POST", headers=headers, data=request_data, data_as_json=False)
        if not response.status == 200:
            msg = "Simplenote login failed, Please check username and password: %s" % response.body
            raise SimplenoteLoginFailed(msg)
        result = response.data
        if not isinstance(result, dict):
            raise SimplenoteLoginFailed("access_token not in result: %s" % result)
        token = result.get("access_token")
        if not isinstance(token, str):
            raise SimplenoteLoginFailed("access_token is not a string: %s" % token)

        # assert len(token) == 32, "token length is not 32: %s" % token
        with open(SIMPLENOTE_TOKEN_FILE, "wb") as fh:
            fh.write(token.encode("utf-8"))
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
                    token = fh.read().decode("utf-8")
                    if not token:
                        raise ValueError("token is empty")
                    self._token = token
            except (FileNotFoundError, ValueError) as err:
                self._token = self.authenticate(self.username, self.password)
            except (EOFError, Exception) as err:
                logger.exception(err)
                raise err
        return self._token

    def _parse_response(self, note_id: str, response: Response):
        msg = "OK"
        try:
            assert isinstance(response, Response), "response is not a Response: %s" % response
            assert response.status == 200, "response.status is not 200: %s" % response
            _version: str | None = response.headers.get("X-Simperium-Version")
            logger.debug(("status:", response.status, "version:", _version))
            assert isinstance(_version, str), "version is not a string: %s" % _version
            assert _version.isdigit(), "version is not a number: %s" % _version
            return 0, msg, {"id": note_id, "v": int(_version), "d": response.data}
        except AssertionError as err:
            logger.exception(err)
            logger.error(response)
            msg = err
        except TypeError as err:
            logger.exception(err)
            logger.error(response)
            msg = err
        return -1, msg, {}

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
            - msg (string): "OK" or an error message
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
            return 0, "OK", response.data
        except IOError as err:
            logger.exception(err)
            return -1, err, []

    def retrieve(self, note_id: str, version: Optional[int] = None):
        """Method to get a specific note

        Arguments:
            - note_id (string): ID of the note to get
            - version (int): optional version of the note to get

        Returns:
            A tuple `(status, note)`

            - status (int): 0 on success and -1 otherwise
            - msg (string): "OK" or an error message
            - note (dict): note object
        """
        try:
            response = request(
                URL.retrieve(note_id, version),
                method="GET",
                headers={self.header: self.token},
            )
            return self._parse_response(note_id, response)
        except IOError as err:
            logger.exception(err)
            return -1, err, {}

    def modify(self, note: Dict[str, Any], note_id: Optional[str] = None, version: Optional[int] = None):
        """Method to modify or create a note

        Arguments:
            - note (dict): note object to modify
            - note_id (string): ID of the note to modify
            - version (int): optional version of the note to modify

        Returns:
            A tuple `(status, note)`

            - status (int): 0 on success and -1 otherwise
            - msg (string): "OK" or an error message
            - note (dict): note object
        """
        if not isinstance(note, dict):
            raise ValueError("note should be a string or a dict, but got %s" % note)
        if not note_id:
            note_id = str(uuid4())
            logger.info("note_id is None, using %s" % note_id)
            # raise ValueError("note_id should be a string, but got %s" % note_id)
        note["modificationDate"] = time.time()
        try:
            response = request(
                URL.modify(note_id, version),
                method="POST",
                headers={self.header: self.token},
                data=note,
            )
            return self._parse_response(note_id, response)
        except IOError as err:
            logger.exception(err)
            return -1, err, {}

    def delete(self, note_id: str, version: Optional[int] = None):
        """Method to permanently delete a note

        Arguments:
            - note_id (string): key of the note to trash

        Returns:
            A tuple `(status, note)`

            - status (int): 0 on success and -1 otherwise
            - msg (string): "OK" or an error message
            - note (dict): an empty dict or an error message
        """
        try:
            response = request(
                URL.delete(note_id, version),
                method="DELETE",
                headers={self.header: self.token},
            )
            return self._parse_response(note_id, response)
        except IOError as err:
            logger.exception(err)
            return -1, err, {}

    def trash(self, note_id: str, version: Optional[int] = None):
        """Method to move a note to the trash

        Arguments:
            - note_id (string): key of the note to trash

        Returns:
            A tuple `(status, note)`

            - status (int): 0 on success and -1 otherwise
            - msg (string): "OK" or an error message
            - note (dict): the newly created note or an error message
        """
        status, msg, note = self.retrieve(note_id, version)
        if status == -1:
            return status, msg, note
        assert isinstance(note, dict), "note is not a dict: %s" % note
        assert "deleted" in note, "deleted not in note: %s" % note
        assert isinstance(note["deleted"], bool), "note['deleted'] is not a bool: %s" % note["deleted"]
        note["deleted"] = True
        return self.modify(note, note_id, version)


if __name__ == "__main__":
    from settings import get_settings

    username = get_settings("username")
    password = get_settings("password")
    if not isinstance(username, str) or not isinstance(password, str):
        raise Exception("Missing username or password")
    simplenote = Simplenote(password, password)
    token = simplenote.token
    print("token: %s" % token)
