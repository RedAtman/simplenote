"""
:license: MIT, see LICENSE for more details.
:doc: https://simperium.com/docs/reference/http/#auth
"""

import functools
import json
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from uuid import uuid4

from .._config import CONFIG
from ..utils.patterns.singleton.base import Singleton
from ..utils.request import Response, request


logger = logging.getLogger()

__all__ = ["Simplenote"]


class URL:
    BASE: str = "simperium.com/1"
    AUTH = f"https://auth.{BASE}"
    DATA = f"https://api.{BASE}/{CONFIG.SIMPLENOTE_APP_ID}/{CONFIG.SIMPLENOTE_BUCKET}"
    __auth = f"{AUTH}/{CONFIG.SIMPLENOTE_APP_ID}/authorize/"
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

    @staticmethod
    @functools.lru_cache(maxsize=2)
    def authenticate(username: str, password: str):
        """Method to get simplenote auth token

        Arguments:
            - username (string): simplenote email address
            - password (string): simplenote password

        Returns:
            Simplenote API token as string
        """
        response = request(
            URL.auth(),
            method="POST",
            headers={"X-Simperium-API-Key": CONFIG.SIMPLENOTE_APP_KEY},
            data={"username": username, "password": password},
            data_as_json=False,
        )
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
        return token

    @property
    def token(self):
        """Method to retrieve an auth token.

        The cached global token is looked up and returned if it exists. If it
        is `None` a new one is requested and returned.

        Returns:
            Simplenote API token as string
        """
        if not self._token:
            try:
                with open(CONFIG.SIMPLENOTE_TOKEN_FILE_PATH, "r") as fh:
                    _token = json.load(fh)
                    token = _token.get(self.username)
                    if not token:
                        raise ValueError("token is empty")
                    return token
            except Exception as err:
                logger.info("Do not have token cache for %s, requesting new one. Error: %s" % (self.username, err))
                self._token = self.authenticate(self.username, self.password)
                with open(CONFIG.SIMPLENOTE_TOKEN_FILE_PATH, "w+") as fh:
                    try:
                        _token = json.load(fh)
                    except Exception as err:
                        _token = {}
                    _token[self.username] = self._token
                    json.dump(_token, fh)
        return self._token

    def _parse_response(self, note_id: str, response: Response):
        assert isinstance(response, Response), "response is not a Response: %s" % response
        assert response.status == 200, "response.status is not 200: %s" % response
        _version: str | None = response.headers.get("X-Simperium-Version")
        logger.debug(("status:", response.status, "version:", _version))
        assert isinstance(_version, str), "version is not a string: %s" % _version
        assert _version.isdigit(), "version is not a number: %s" % _version
        return {"id": note_id, "v": int(_version), "d": response.data}

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
            - limit (int): number of notes to return
            - data (bool): whether to return the note data or not
            - tags=[] list of tags as string: return notes that have
              at least one of these tags

        Returns:
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

        response = request(
            URL.index(**params),
            method="GET",
            params=params,
            headers={self.header: self.token},
        )
        return response.data

    def retrieve(self, note_id: str, version: Optional[int] = None):
        """Method to get a specific note

        Arguments:
            - note_id (string): ID of the note
            - version (int): optional version of the note

        Returns:
            - note (dict): note object
        """

        response = request(
            URL.retrieve(note_id, version),
            method="GET",
            headers={self.header: self.token},
        )
        return self._parse_response(note_id, response)

    def modify(self, note: Dict[str, Any], note_id: Optional[str] = None, version: Optional[int] = None):
        """Method to modify or create a note

        Arguments:
            - note (dict): note object
            - note_id (string): optional ID of the note
            - version (int): optional version of the note

        Returns:
            - note (dict): note object
        """
        if not isinstance(note, dict):
            raise ValueError("note should be a string or a dict, but got %s" % note)
        if not note_id:
            note_id = str(uuid4())
            logger.info("note_id is None, using %s" % note_id)
            # raise ValueError("note_id should be a string, but got %s" % note_id)
        note["modificationDate"] = time.time()

        response = request(
            URL.modify(note_id, version),
            method="POST",
            headers={self.header: self.token},
            data=note,
        )
        return self._parse_response(note_id, response)

    def delete(self, note_id: str, version: Optional[int] = None):
        """Method to permanently delete a note

        Arguments:
            - note_id (string): key of the note
            - version (int): optional version of the note

        Returns:
            - note (dict): an empty dict or an error message
        """
        response = request(
            URL.delete(note_id, version),
            method="DELETE",
            headers={self.header: self.token},
        )
        return self._parse_response(note_id, response)

    def trash(self, note_id: str, version: Optional[int] = None):
        """Method to move a note to the trash

        Arguments:
            - note_id (string): key of the note
            - version (int): optional version of the note

        Returns:
            - note (dict): the newly created note or an error message
        """
        note = self.retrieve(note_id, version)
        note["deleted"] = True
        return self.modify(note, note_id, version)
