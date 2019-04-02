import requests
import os
import base64
import time
import abc
import urllib.parse
from.ssexceptions import *



def token_expired(tokeninfo):
    return tokeninfo['expires_at'] < int(time.time()) + 60

def add_token_expiration_date(tokeninfo):
    tokeninfo['expires_at'] = int(time.time()) + tokeninfo['expires_in']


class TokenBearer(abc.ABC) :
    @abc.abstractmethod
    def _get_token(self):
        pass

    @classmethod
    def __subclasshook__(cls,subcls) :
        if "_get_token" in subcls.__dict__ and callable(subcls.__dict__["_get_token"]):
            return True
        return NotImplemented



from simpleSpotifyCore import api


class DirectTokenBearer(TokenBearer):
    def __init__(self, token, makesession=True):
        self.token = token
        if makesession:
            self._session = requests.session()

    def _get_token(self):
        return self.token


class Oauth2(TokenBearer):

    @property
    def _session(self):
        if self._passed_session is not None:
            return self._passed_session
        if not hasattr(self, "_session_"):
            self._session_ = requests.session()
        return self._session_

    def __init__(self,client_id, client_secret, request_session=None,
                 redirecturl="http://localhost:8080", scopes = None,
                 show_dialog = False, state = None):

        self._passed_session = request_session
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirecturl = redirecturl
        self.scopes = scopes
        self.show_dialog = show_dialog
        self.state = state
        self.tokeninfo = None

    def get_redirect_uri(self) :

        params = {"client_id": self.client_id,
                  "response_type": "code" ,
                  "redirect_uri": self.redirecturl ,
                  "showdialog": self.show_dialog
                }
        if self.state :
            params.update({"state": self.state})
        if self.scopes :
            params.update({"scope": self.scopes})

        params = urllib.parse.urlencode(params)

        return f"https://accounts.spotify.com/authorize?{params}"

    def exchange_code_for_token(self,code) :
        authb = base64.b64encode((self.client_id + ":" + self.client_secret).encode()).decode()

        resp = self._session.post(
            url = "https://accounts.spotify.com/api/token",
            data = {
                'grant_type': 'authorization_code',
                'code' : code,
                'redirect_uri': self.redirecturl
            },
            headers = {'Authorization': f'Basic {authb}'}
        )

        if resp.status_code == 200 :
            self.tokeninfo = resp.json()
            add_token_expiration_date(self.tokeninfo)
            return self.tokeninfo # TOKEN INFO
        elif resp.status_code == 400 :
            raise Exception(f"Error 400 Bad Request : {resp.json()['error_description']}")
        resp.raise_for_status()

    def _get_token(self):
        if self.tokeninfo is None :
            #TODO clear up this exception
            raise Exception("No token info available!")
        elif token_expired(self.tokeninfo):
            pass #refresh token
        return self.tokeninfo['access_token']


class Client(TokenBearer):

    @property
    def session(self):
        if self._passed_session is not None:
            return self._passed_session
        if not hasattr(self, "_session") :
            self._session = requests.session()
        return self._session

    def __init__(self, client_id=None, client_secret=None, requests_session=None, scope=None, redirecturl="http://localhost:8080"):
        pass
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirecturl = redirecturl
        self._passed_session = requests_session
        self._tokeninfo = None
        self.scopes = scope

    def create_oauth2(self,scopes=None) -> Oauth2 :
        return Oauth2(client_id = self.client_id,client_secret = self.client_secret,
                      redirecturl=self.redirecturl, request_session = self.session,
                      scopes=scopes or self.scopes )

    def _get_token(self):
        #TODO : add token caching
        if self._tokeninfo is None:
            self._tokeninfo = self._request_client_token()
        elif token_expired(self._tokeninfo):
            self._tokeninfo = self._request_client_token()
        return self._tokeninfo['access_token']

    def _request_client_token(self):

        # I literally don't know what this black magic is
        authb = base64.b64encode((self.client_id + ":" + self.client_secret).encode()).decode()

        resp = self.session.post(
            url = "https://accounts.spotify.com/api/token",
            data = {'grant_type': 'client_credentials'},
            headers = {'Authorization': f'Basic {authb}'}
        )

        if resp.status_code == 400:
            error_message = resp.json()
            raise InvalidCredentials(f"Error Retrieving Client Token : {error_message['error_description']}")

        tokeninfo = resp.json()
        add_token_expiration_date(tokeninfo)
        return tokeninfo

        # 'access_token', 'token_type', 'expires_in', 'scope'
