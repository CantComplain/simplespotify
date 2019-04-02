
from copy import deepcopy
from .BaseClasses import SpotifyItem, Searchable
from . import globalstate as gs


class Artist(Searchable, SpotifyItem):
    """ 
        the representation of an artist in a python object
        
        ***SHOULD NOT BE CALLED DIRECTLY***

        typically, you will construct an artist 1 of 2 ways

        BOTH methods will return None if they fail

        artist_object = artist.from_search('search string')

            -- gets artist from a string of the artists name ex "bomb the music industry" - string has to be fairly accurate

        artist_object = artist.from_id('id')

            -- gets artist from either the id, the URL of the artist or the URI
                - "7mmU5GuOoyxoBAgOZkSVj7" ----------------------------------- Example ID
                - "https://open.spotify.com/artist/7mmU5GuOoyxoBAgOZkSVj7" --- Example URL
                - "spotify:artist:7mmU5GuOoyxoBAgOZkSVj7" -------------------- Example URI
                Notice how they all contain the id - hence the potentially misleading name of the function

        Properties :

            ._apidict - the dictionary you would get from the spotify api, you should probably not need it (dict)
    
            .url - url to the artist (str)
            .id - artist ID (str)
            .uri - artist's URI (str)
            .name - artist's name e.g. "Bomb! The Music Industry" (str)

            .genres - genres spotify has labeled this artist as (list)
            .images - images with there height and widths icluded (list of dict)
            .popularity - popularity, I have no idea how this is calculated i think it's 1-100 scale (int)
            .followers - number of followers (int)
        Methods :
            .get_catalog() - returns a list of the artists albums AS OBJECTS and *INCLUDES FEATURES AND SINGLES* (list)


    """

    cache = deepcopy(SpotifyItem.cache)

    _full_attr_names = (  "followers",
                          "genres",
                          "images",
                          "popularity",)

    # ['external_urls', 'followers', 'genres', 'href', 'id', 'images', 'name', 'popularity', 'type', 'uri']
    def _add_simple_attrs(self):
        self._albums = None
        self._related_artists = None
        self._top_tracks = None

    def _determine_form(self):
        if "followers" in self._apidict:
            self._form = "full"
        else:
            self._form = "simplified"

    def _add_full_attrs(self):
        self._followers = self._apidict["followers"]["total"]
        self._genres = self._apidict["genres"]
        self._images = self._apidict["images"]
        self._popularity = self._apidict["popularity"]

    def get_catalog(self) -> list:  # TODO : add keyword args for removing singles, compilations, features etc.
        """ 
        --------------------------------------------
        No Args. Returns a list of albums as objects
        --INCLUDES FEATURES AND SINGLES-------------
        """
        if self._albums is None:
            self._albums = Album._dict_if_cached(self._api.get_artist_albums(self.id)['items'])
        return self._albums

    def top_tracks(self,market:str="US") -> list:
        if self._top_tracks is None:
            self._top_tracks = Track._dict_if_cached(self._api.artist_top_tracks(self.id,market=market)["tracks"])
        return self._top_tracks

    def related_artists(self) -> list:
        if self._related_artists is None:
            self._related_artists = Artist._dict_if_cached(self._api.artist_related_artists(self.id)['artists'])
        return self._related_artists


class Album(Searchable, SpotifyItem):
    cache = deepcopy(SpotifyItem.cache)
    _full_attr_names =  (   "total_tracks",
                            "external_ids",
                            "genres",
                            "label",
                            "copyright",
                            "popularity",
                            "tracks",)

        # ['album_type', 'artists', 'available_markets', 'copyrights', 'external_ids', 'external_urls', 'genres', 'href', 'id', 'images', 'label', 'name', 'popularity', 'release_date', 'release_date_precision', 'total_tracks', 'tracks', 'type', 'uri']
    def _add_simple_attrs(self):
        # TODO : somehow make album type/group make more sense
        self.album_type = self._apidict['album_type']
        # self.album_group --> only appears when looking up artists albums --> somehow make this a method or something

        #self.markets = self._apidict['available_markets']

        self.images = self._apidict["images"]

        self.artists = Artist._dict_if_cached(self._apidict['artists'])

        # TODO: Parse these somehow? datetime? would be nice to have .release_year
        self.release_date = self._apidict["release_date"]
        self.release_date_precision = self._apidict["release_date_precision"]

    def _determine_form(self):
        if 'copyrights' in self._apidict:
            self._form = "full"
        else:
            self._form = "simplified"

    def _add_full_attrs(self):
        self._external_ids = self._apidict['external_ids']  # I don't KNow what this is ???
                                                            # apparently we can get upc and other stuff ???
        self._genres = self._apidict['genres']  # for some reason this field always seems to be blank for me ? 
        # ---> I should stop being a hipster
        self._label = self._apidict['label']
        self._copyright = self._apidict['copyrights']
        self._popularity = self._apidict['popularity']
        self._total_tracks = self._apidict['total_tracks']
        self._tracks = Track._dict_if_cached(self._apidict['tracks']['items'])
        self._form = "full"

    @staticmethod
    def new_releases(country=None,limit=20,offset=0) :

        releases = gs.get_current_api().get_new_releases(country=country, limit=limit, offset=offset)
        return Album._dict_if_cached(releases['items'])

    def __len__(self):
        return self._total_tracks


class Track(Searchable,SpotifyItem):
    cache = deepcopy(SpotifyItem.cache)
    _full_attr_names =  (
        "album",
        "popularity",
        "markets",
    )


    def _add_simple_attrs(self):
        # list of artists on track!
        self.artists = Artist._dict_if_cached(self._apidict['artists'])

        # almost always gonna be one unless album has more than one disc
        self.disc_number = self._apidict['disc_number']

        # time in milleseconds
        self.duration_ms = self._apidict['duration_ms']

        # True if bad words, false if not or unknown
        self.is_explicit = self._apidict['explicit']

        # 30s preview link
        self.preview = self._apidict['preview_url']

        # number on album, if multiple discs its the number on disc
        self.track_number = self._apidict['track_number']

        # if it's a local file
        self.is_local = self._apidict['is_local']

    def _determine_form(self):
        if 'album' in self._apidict:
            self._form = "full"
        else:
            self._form = "simplified"

    def _add_full_attrs(self):
        self._album = Album._dict_if_cached([self._apidict['album']])[0]
        self._popularity = self._apidict['popularity']
        # self._markets = self._apidict['available_markets']

    def __len__(self) :
        return self.duration_ms


class Playlist(SpotifyItem, Searchable):

    _full_attr_names = (
        "collaborative"
        "description"
        "followers"
    )

    cache = deepcopy(SpotifyItem.cache)

    # TODO: ADD SUPPORT FOR FIELDS WHEN CONSTRUCTION FROM ID

    def _add_simple_attrs(self):
        self.isCollaborative = self._apidict["collaborative"]
        self.images = self._apidict["images"]
        self.owner = self._apidict["owner"]  # a USER object
        self.isPublic = self._apidict["public"]
        self.snapid = self._apidict["snapshot_id"]
        self.tracks = self._apidict["tracks"]
        self.length = self._apidict["tracks"]["total"]

    def _determine_form(self) :
        if getattr(self, "_description", -1) is -1 :  # if playlist description is actually "-1" is this fucked?
            self._form = "simplified"
        else:
            self._form = "full"

    def _add_full_attrs(self):
        self._description = self._apidict["description"]
        self._followers = self._apidict["followers"]["total"]  # is followers ever useful besides total?

    def __len__(self):
        return self.length

