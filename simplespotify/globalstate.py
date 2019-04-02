from simpleSpotifyCore.ssexceptions import *
from simpleSpotifyCore.api import APIbase


current_bearer = None


def use_globally(bear) :
    global current_bearer
    current_bearer = bear


def get_current_api(*_args) -> APIbase :
    if current_bearer is None :
        raise InsufficientCredentials("No Global API currently used")
    return current_bearer.api

