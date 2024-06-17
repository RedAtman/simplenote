"""
:license: MIT, see LICENSE for more details.
:doc: https://simperium.com/docs/reference/http/#auth
"""

import functools
import logging
import os
import pickle
import time
from typing import Dict
import uuid

from config import CONFIG
from utils.patterns.singleton.base import Singleton
from utils.request import request


logger = logging.getLogger()


class SimplenoteLoginFailed(Exception):
    pass


class Simplenote(Singleton):
    """Class for interacting with the simplenote web service"""

    # TODO: This should be a relative path, not an absolute one
    TOKEN_FILE = "/Users/nut/Library/Application Support/Sublime Text/Packages/Simplenote/pkl/simplenote.pkl"

    if not os.path.exists("pkl"):
        os.makedirs("pkl")
    assert os.path.exists("pkl"), "pkl directory does not exist!"
    assert os.path.isdir("pkl"), "pkl is not a directory!"
    assert os.access("pkl", os.W_OK), "pkl directory is not writable!"
    assert os.access("pkl", os.R_OK), "pkl directory is not readable!"
    assert os.path.exists(TOKEN_FILE), "pkl/simplenote.pkl does not exist!"

    def __init__(self, username: str, password: str):
        """object constructor"""
        if not any([username, password]):
            raise SimplenoteLoginFailed(
                "username should not be None or password should not be None! but got username: %s, password: %s"
                % (username, password)
            )
        self.username = username
        self.password = password
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
        headers = {"X-Simperium-API-Key": CONFIG.SIMPLENOTE_APP_KEY}
        request_data = {"username": username, "password": password}
        logger.info(("request_data:", request_data, "headers:", headers))
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
        with open(cls.TOKEN_FILE, "wb") as fh:
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
                with open(self.TOKEN_FILE, "rb") as fh:
                    token = pickle.load(fh, encoding="utf-8")
                    self._token = token
            except FileNotFoundError as err:
                self._token = self.authenticate(self.username, self.password)
            except EOFError as err:
                logger.exception(err)
                raise err
        return self._token

    def get_note(self, note_id, version=None):
        """Method to get a specific note

        Arguments:
            - note_id (string): ID of the note to get
            - version (int): optional version of the note to get

        Returns:
            A tuple `(note, status)`

            - note (dict): note object
            - status (int): 0 on sucesss and -1 otherwise
        """
        # url: "https://api.simperium.com/1/chalk-bump-f49/note/i/ba4f2735aab811e89fd89d5f0cfefda5"
        params_version = ""
        if version is not None:
            params_version = "/v/" + str(version)
        params = "/i/%s%s" % (str(note_id), params_version)
        response = request(url=CONFIG.SIMPLENOTE_DATA_URL + params, method="GET", headers={self.header: self.token})
        version = response.headers.get("X-Simperium-Version")
        assert version is not None, "version is None: %s" % version
        assert isinstance(version, str), "version is not a string: %s" % version
        assert version.isdigit(), "version is not a digit: %s" % version
        version = int(version)
        note = response.data

        note = self.__add_simplenote_api_fields(note, note_id, version)
        logger.debug(("Got note:", note))

        return note, 0

    def update_note(self, note: Dict[str, str]):
        """Method to update a specific note object, if the note object does not
        have a "key" field, a new note is created

        Arguments
            - note (dict): note object to update

        Returns:
            A tuple `(note, status)`
            - note (dict): note object
            - status (int): 0 on sucesss and -1 otherwise

        """
        # determine whether to create a new note or update an existing one
        # Also need to add/remove key field to keep simplenote.py consistency
        if "key" in note:
            # Then already have a noteid we need to remove before passing to Simperium API
            note_id = note.pop("key", None)
            # set modification timestamp if not set by client
            if "modificationDate" not in note:
                note["modificationDate"] = time.time()
        else:
            # Adding a new note
            note_id = uuid.uuid4().hex

        # TODO: Set a ccid?
        # ccid = uuid.uuid4().hex
        if "version" in note:
            version = note.pop("version", None)
            url = "%s/i/%s/v/%s?response=1" % (CONFIG.SIMPLENOTE_DATA_URL, note_id, version)
        else:
            url = "%s/i/%s?response=1" % (CONFIG.SIMPLENOTE_DATA_URL, note_id)
        logger.info(("url:", url))

        # TODO: Could do with being consistent here. Everywhere else is Request(CONFIG.SIMPLENOTE_DATA_URL+params)
        note = self.__remove_simplenote_api_fields(note)
        headers = {
            self.header: self.token,
            "Content-Type": "application/json",
        }
        try:
            response = request(url, method="POST", headers=headers, data=note)
            logger.info(("response:", response.status, response, response.data, response.headers.__dict__))
        except IOError as err:
            logger.exception(err)
            return err, -1
        assert response.status == 200, f"response.status is not 200: {response.status}"
        note = response.data
        version = response.headers.get("X-Simperium-Version")
        assert version is not None, "version is None: %s" % version
        assert isinstance(version, str), "version is not a string: %s" % version
        assert version.isdigit(), "version is not a digit: %s" % version
        version = int(version)
        note = self.__add_simplenote_api_fields(note, note_id, version)
        return note, 0

    def add_note(self, note):
        """Wrapper method to add a note

        The method can be passed the note as a dict with the `content`
        property set, which is then directly send to the web service for
        creation. Alternatively, only the body as string can also be passed. In
        this case the parameter is used as `content` for the new note.

        Arguments:
            - note (dict or string): the note to add

        Returns:
            A tuple `(note, status)`

            - note (dict): the newly created note
            - status (int): 0 on sucesss and -1 otherwise

        """
        if isinstance(note, str):
            note = {"content": note}
        if not isinstance(note, dict):
            raise ValueError("note should be a string or a dict, but got %s" % note)
        if "content" not in note:
            raise ValueError("note should have a 'content' key, but got %s" % note)
        return self.update_note(note)

    def get_note_list(self, tags=[]):
        """Method to get the note list

        The method can be passed optional arguments to limit the
        the list to notes containing a certain tag. If omitted a list
        of all notes is returned.

        Arguments:
            - tags=[] list of tags as string: return notes that have
              at least one of these tags

        Returns:
            A tuple `(notes, status)`

            - notes (list): A list of note objects with all properties set except
            `content`.
            - status (int): 0 on sucesss and -1 otherwise

        """
        # initialize data
        status = 0
        ret = []
        response_notes = {}
        notes = {"index": []}

        # get the note index
        # TODO: Using data=false is actually fine with simplenote.vim - sadly no faster though
        # params = "/index?limit=%s&data=true" % CONFIG.NOTE_FETCH_LENGTH
        params = "/index?limit=%s&data=true" % 10
        try:
            response = request(CONFIG.SIMPLENOTE_DATA_URL + params, headers={self.header: self.token})
            response_notes = response.data
            # re-write for v1 consistency
            note_objects = []
            for note in response_notes["index"]:
                note_object = self.__add_simplenote_api_fields(note["d"], note["id"], note["v"])
                logger.info((note, note_object))
                """
                {
                    'd':
                    {
                        'tags': [],
                        'deleted': False,
                        'shareURL': '',
                        'systemTags': ['markdown'],
                        'content': '# 2024 / 05 / 26\n\n## edit from web\n\n- 1. \n- 2. \n- 3.\n\n__bold__\n\n# hello\n\nthis is a note.\n\n* 1\n* 2\n',
                        'publishURL': '',
                        'modificationDate': 1718379332.496,
                        'creationDate': 1716440782.110128,
                        'key': '24d9daab381f4170864301cc1cc220f2',
                        'version': 52,
                        'modifydate': 1718379332.496,
                        'createdate': 1716440782.110128,
                        'systemtags': ['markdown']
                    },
                    'id': '24d9daab381f4170864301cc1cc220f2',
                    'v': 52
                },
                {
                    'tags': [],
                    'deleted': False,
                    'shareURL': '',
                    'systemTags': ['markdown'],
                    'content': '# 2024 / 05 / 26\n\n## edit from web\n\n- 1. \n- 2. \n- 3.\n\n__bold__\n\n# hello\n\nthis is a note.\n\n* 1\n* 2\n',
                    'publishURL': '',
                    'modificationDate': 1718379332.496,
                    'creationDate': 1716440782.110128,
                    'key': '24d9daab381f4170864301cc1cc220f2',
                    'version': 52,
                    'modifydate': 1718379332.496,
                    'createdate': 1716440782.110128,
                    'systemtags': ['markdown']
                }
                """
                note_objects.append(note_object)
            notes["index"].extend(note_objects)
        except IOError as err:
            logger.exception(err)
            status = -1

        # get additional notes if bookmark was set in response
        while "mark" in response_notes:
            params += "&mark=%s" % response_notes["mark"]

            try:
                response = request(CONFIG.SIMPLENOTE_DATA_URL + params, headers={self.header: self.token})
                response_notes = response.data
                # re-write for v1 consistency
                note_objects = []
                for n in response_notes["index"]:
                    note_object = n["d"]
                    note_object["version"] = n["v"]
                    note_object["key"] = n["id"]
                    note_objects.append(note_object)
                notes["index"].extend(note_objects)
            except IOError as err:
                logger.exception(err)
                status = -1
        note_list = notes["index"]
        # Can only filter for tags at end, once all notes have been retrieved.
        if len(tags) > 0:
            note_list = [n for n in note_list if (len(set(n["tags"]).intersection(tags)) > 0)]
        return note_list, status

    def trash_note(self, note_id):
        """Method to move a note to the trash

        Arguments:
            - note_id (string): key of the note to trash

        Returns:
            A tuple `(note, status)`

            - note (dict): the newly created note or an error message
            - status (int): 0 on sucesss and -1 otherwise

        """
        # get note
        note, status = self.get_note(note_id)
        if status == -1:
            return note, status
        # set deleted property, but only if not already trashed
        # TODO: A 412 is ok, that's unmodified. Should handle this in update_note and
        # then not worry about checking here
        if not note["deleted"]:
            note["deleted"] = True
            note["modificationDate"] = time.time()
            # update note
            return self.update_note(note)
        else:
            return 0, note

    def delete_note(self, note_id):
        """Method to permanently delete a note

        Arguments:
            - note_id (string): key of the note to trash

        Returns:
            A tuple `(note, status)`

            - note (dict): an empty dict or an error message
            - status (int): 0 on sucesss and -1 otherwise

        """
        # notes have to be trashed before deletion
        note, status = self.trash_note(note_id)
        if status == -1:
            return note, status

        params = "/i/%s" % (str(note_id))
        response = request(url=CONFIG.SIMPLENOTE_DATA_URL + params, method="DELETE", headers={self.header: self.token})
        if response.status == 200:
            return {}, 0
        return response.data, 1

    def __add_simplenote_api_fields(self, note, noteid, version: int):
        # Compatibility with original Simplenote API v2.1.5
        # key_mapper = {
        #     "key": "key",
        #     "version": "version",
        #     "modifydate": "modificationDate",
        #     "createdate": "creationDate",
        #     "systemtags": "systemTags",
        # }
        note["key"] = noteid
        note["version"] = version
        note["modifydate"] = note["modificationDate"]
        note["createdate"] = note["creationDate"]
        note["systemtags"] = note["systemTags"]
        return note

    def __remove_simplenote_api_fields(self, note):
        # These two should have already removed by this point since they are needed for updating, etc, but _just_ incase...
        note.pop("key", None)
        note.pop("version", None)
        # Let's only set these ones if they exist. We don't want None so we can
        # still set defaults afterwards
        mappings = {"modifydate": "modificationDate", "createdate": "creationDate", "systemtags": "systemTags"}
        for k, v in mappings.items():
            if k in note:
                note[v] = note.pop(k)
        # Need to add missing dict stuff if missing, might as well do by
        # default, not just for note objects only containing content
        createDate = time.time()
        note_dict = {
            "tags": [],
            "systemTags": [],
            "creationDate": createDate,
            "modificationDate": createDate,
            "deleted": False,
            "shareURL": "",
            "publishURL": "",
        }
        for k, v in note_dict.items():
            note.setdefault(k, v)
        return note


if __name__ == "__main__":
    simplenote = Simplenote(CONFIG.SIMPLENOTE_USERNAME, CONFIG.SIMPLENOTE_PASSWORD)
    token = simplenote.token
    print("token: %s" % token)
