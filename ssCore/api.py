from .tokenbearers import TokenBearer
from typing import *
import requests
import abc
from .ssexceptions import *

attributes = ("acousticness", "danceability", "duration_ms",
                          "energy", "instrumentalness", "key", "liveness", "loudness", "mode", "popularity", "speechiness", "tempo", "time_signature", "valence")
def _get_session(self) :
    if self._passed_session is not None :
        return self._passed_session
    if not hasattr(self,"_session") :
        self._session = requests.session()
    return self._session


class APIbase(abc.ABC):
    ''' Base Class for all API classes '''

    def __init__(self, tokenbearer : TokenBearer, session: Optional[requests.Session] = None):
        self.tokenbearer = tokenbearer
        self._passed_session = session

    @property
    def session(self):
        if self._passed_session is not None:
            return self._passed_session
        if not hasattr(self, "_session"):
            self._session = requests.session()
        return self._session

    # These are all the "ENDPOINTS" you need to implement if you want to create a compatible API class (in a way this
    # this is the API for API's) All of them should return the JSON response just as it came from the spotify API
    @abc.abstractmethod
    def get_new_releases(self, country: Optional[str] = None, limit: int = 20, offset : int = 0) :
        pass

    @abc.abstractmethod
    def list_categories(self, limit: int= 20, offset: int = 0, country: str = None, locale: Optional[str] = None):
        pass

    @abc.abstractmethod
    def get_category(self, category_id: str, country: Optional[str]=None, locale: Optional[str] = None):
        pass

    @abc.abstractmethod
    def category_playlists(self, category_id: str, limit: int = 20, offset: int = 0, country: Optional[str] = None):
        pass

    @abc.abstractmethod
    def single_album(self, id: str):
        pass

    @abc.abstractmethod
    def multiple_albums(self, ids: list, market: Optional[str] = None):
        pass

    @abc.abstractmethod
    def get_album_tracks(self, id: str, limit: int = 50, offset: int = 0, market:Optional[str] = None):
        pass

    @abc.abstractmethod
    def single_artist(self, id: str):
        pass

    @abc.abstractmethod
    def multiple_artists(self, ids: list):
        pass

    @abc.abstractmethod
    def artist_top_tracks(self, id: str, market: str="US"):
        pass

    @abc.abstractmethod
    def artist_related_artists(self, id: str):
        pass

    @abc.abstractmethod
    def get_artist_albums(self, id: str, include_groups: str = None, market: str = None,limit: int = 20, offset: int = 0):
        pass

    @abc.abstractmethod
    def single_track(self, id: str, market: str = None):
        pass

    @abc.abstractmethod
    def multiple_tracks(self, ids: list, market: str = None):
        pass

    @abc.abstractmethod
    def single_track_audio_features(self, id: str):
        pass

    @abc.abstractmethod
    def multiple_track_audio_features(self,ids: list):
        pass

    @abc.abstractmethod
    def track_audio_analysis(self,id: str):
        pass
    @abc.abstractmethod
    def search(self,q:str, type:str, market: Optional[str] = None, limit:int = 20, offset: int = 0, include_external:bool = False):
        pass

    @abc.abstractmethod
    def featured_playlists(self, locale:Optional[str] = None, country:Optional[str] = None,timestamp: Optional[str] = None,
                           limit:int=20, offset:int=0):
        pass

    @abc.abstractmethod
    def get_seeded_recommendations(self, limit: int = 20, offset: int = 0, seed_artists: list = None,
                                   seed_genres: list = None,
                                   seed_tracks: list = None, market: str = None, **kwargs):
        pass


class SimpleSpotifyApi(APIbase) :

    # --INTERNALS --
    def auth_headers(self):
        return {"Authorization": f"Bearer { self.tokenbearer._get_token() }"}

    def _get(self, *args, **kwargs):
        kwargs.update({"headers": self.auth_headers()})

        r = self.session.get(*args, **kwargs)

        if r.status_code == 200:  # ok
            return r
        elif r.status_code == 400:  # bad request
            #print(r.content)
            #r.raise_for_status()
            raise SSExcept(f"Error 400 Bad Request: {r.json()['error']['message']}")
        elif r.status_code == 401 :
            print(r.json())
            raise ClientExcept(f"Error 401 Unauthorized: {r.json()['error']['message']}")
        else:  # other
            try :
                print(f"error {r.json()}")
            finally:
                r.raise_for_status()

    # --BROWSE ENDPOINTS-- COMPLETE

    def get_seeded_recommendations(self, limit: int = 20, offset: int = 0, seed_artists:list = None, seed_genres: list = None,
                                   seed_tracks: list = None, market: str = None, **kwargs):
        params = {"limit" : limit, "offset" : offset, "market": market}

        if seed_artists is not None :
            seed_artists = ",".join(seed_artists)
            params.update({"seed_artists": seed_artists})
        if seed_genres is not None:
            seed_genres = ",".join(seed_genres)
            params.update({"seed_genres": seed_genres})
        if seed_tracks is not None :
            seed_tracks = ",".join(seed_tracks)
            params.update({"seed_tracks": seed_tracks})

        for kwarg in kwargs :
            if not kwarg.startswith(("min_","max_","target_")) or not kwarg.endswith(attributes) :
                raise TypeError(f"Unexpected Keyword Argument {kwarg}")
            params.update({kwarg: kwargs[kwarg]})

        r = self._get(url ="https://api.spotify.com/v1/recommendations",
                      params = params)

        return r.json()

    def get_new_releases(self, country: Optional[str] = None, limit: int = 20, offset : int = 0):

        # request
        resp = self._get(
            url = "https://api.spotify.com/v1/browse/new-releases",
            params = {"country": country,
                      "limit": limit,
                      "offset": offset, }
        )
        # Return paged item. ['items'] is the list of album objects
        # paged item contains ['href', 'items', 'limit', 'next', 'offset', 'previous', 'total']
        return resp.json()['albums']

    def featured_playlists(self, locale: Optional[str] = None, country: Optional[str] = None,
                           timestamp: Optional[str] = None,
                           limit: int = 20, offset: int = 0):
        r = self._get("https://api.spotify.com/v1/browse/featured-playlists",
                      params= {"locale": locale, "country": country, "timestamp": timestamp,
                               "limit": limit, "offset": offset})
        return r.json()

    def list_categories(self, limit: int= 20, offset: int = 0, country: Optional[str] = None, locale: Optional[str] = None):
        r = self._get("https://api.spotify.com/v1/browse/categories",
                      params = {"limit": limit, "offset": offset,
                                "country": country, "locale": locale})
        return r.json()

    def get_category(self, category_id: str, country:Optional[str]=None, locale:Optional[str]=None):
        r = self._get(f"https://api.spotify.com/v1/browse/categories/{category_id}",
                      params={"country": country, "locale": locale})
        return r.json()

    def category_playlists(self, category_id: str, limit: int = 20, offset: int = 0, country: Optional[str]=None):

        r = self._get(url = f"https://api.spotify.com/v1/browse/categories/{category_id}/playlists",
                      params = {
                          "limit": limit,
                          "offset": offset,
                          "country": country})
        return r.json()

    def search(self, q: str, types: str, market: Optional[str] = None, limit: int = 20, offset: int = 0, include_external: bool = False):
        params = {"q": q,
                  "type"   : types,
                  "market" : market,
                  "limit"  : limit,
                  "offset" : offset
                                 }
        if include_external :
            params.update({"include_external": "audio"})

        r = self._get( url = "https://api.spotify.com/v1/search",
                       params = params)

        return r.json()

    # --ALBUM ENDPOINTS-- COMPLETE
    def single_album(self, id: str):
        # TODO add id parsing tools -> id is base 62 encoded
        resp = self._get(f"https://api.spotify.com/v1/albums/{id}")

        return resp.json()

    def multiple_albums(self, ids: list, market: Optional[str] = None):
        r = self._get(url = "https://api.spotify.com/v1/albums",
                      params = {
                          "ids": ",".join(ids),
                          "market": market
                      })
        return r.json()

    def get_album_tracks(self, id: str, limit: int = 50, offset: int = 0, market:Optional[str]= None):

        r = self._get(url = f"https://api.spotify.com/v1/albums/{id}/tracks",
                      params = {
                          "limit": limit,
                          "offset": offset,
                          "market": market}
                      )

        return r.json()

    # --ARTIST ENDPOINTS-- COMPLETE
    def single_artist(self, id: str):
        resp = self._get(f"https://api.spotify.com/v1/artists/{id}")
        return resp.json()

    def multiple_artists(self, ids: list):
        r = self._get(url="https://api.spotify.com/v1/artists",
                      params={"ids"   : ','.join(ids)})
        return r.json()

    def artist_top_tracks(self, id: str, market: str="US"):
        r = self._get(url=f"https://api.spotify.com/v1/artists/{id}/top-tracks",
                      params={"market":market})
        return r.json()

    def artist_related_artists(self, id: str):
        r = self._get(f"https://api.spotify.com/v1/artists/{id}/related-artists")
        return r.json()

    def get_artist_albums(self, id: str, include_groups: Optional[str] = None, market: Optional[str] = None,limit: int = 20, offset: int = 0):
        r = self._get(f"https://api.spotify.com/v1/artists/{id}/albums",
                      params = {"include_groups": include_groups,
                                "market": market,
                                "limit": limit,
                                "offset": offset})
        return r.json()

    # --TRACK ENDPOINTS-- COMPLETE
    def single_track(self, id: str, market: Optional[str] = None):
        resp = self._get(f"https://api.spotify.com/v1/tracks/{id}",
                         params={"market": market})
        return resp.json()

    def multiple_tracks(self, ids: list, market: Optional[str] = None):
        r = self._get(url = "https://api.spotify.com/v1/tracks",
                      params = {"ids": ','.join(ids),
                                "market": market})
        return r.json()

    def single_track_audio_features(self, id: str):
        r = self._get(f"https://api.spotify.com/v1/audio-features/{id}")
        return r.json()

    def multiple_track_audio_features(self, ids: list):
        r = self._get("https://api.spotify.com/v1/audio-features",
                      params={"ids": ",".join(ids)})
        return r.json()

    def track_audio_analysis(self, id: str):
        r = self._get(f"https://api.spotify.com/v1/audio-analysis/{id}")
        return r.json()

    # -- PLAYLIST ENDPOINTS --

    def single_playlist(self, id, fields=None, market = None) :
        r = self._get(f"https://api.spotify.com/v1/playlists/{id}",
                      params = {
                          "fields": fields,
                          "market": market
                                })
        return r.json()

    def playlist_cover_image(self, playlist_id ):  # why is this endpoint even needed? the normal playllist endpoint returns it aswell
        # OAUTH REQUIRED IT RETURNS BAD REQUEST CAUSE API RESPONSE IS STUPID
        r = self._get("https://api.spotify.com/v1/playlists/{}/images".format(playlist_id))
        return r.json()

