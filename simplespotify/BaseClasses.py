import abc
from . import globalstate as gs
from simpleSpotifyCore.IDtools import get_id,is_id


class SpotifyItem (abc.ABC):
    """ Base class for all types of object we should have (track, album, and artist).
        user should never use or see this its just for inheritance"""

    cache = {
        'names': {},
        'ids': {},
        'searches': {}
    }

    _api = property(fget=gs.get_current_api)

    def __init__(self, apidict: dict):

        # track, artist and album all have these so far
        self._apidict: dict = apidict

        self.url:   str = self._apidict['external_urls']['spotify']
        self.id:    str = self._apidict['id']
        self.uri:   str = self._apidict['uri']
        self.name:  str = self._apidict['name']
        self.type:  str = self._apidict['type']
        self.href:  str = self._apidict['href']

        # store the item in cache
        self._cache()
        self._determine_form()
        self._add_simple_attrs()
        if self._form == 'full' :
            self._add_full_attrs()


    def _cache(self):
        self.__class__.cache["ids"][self.id] = self
        self.__class__.cache["names"][self.name.strip().lower()] = self

    def __getattr__(self,attr):
        if attr in self.__class__._full_attr_names :
            return self._get_full_attribute("_"+attr)
        if hasattr(super(), "__getattr__"):
            return super().__getattr__(attr)
        raise AttributeError(f'No Attribute "{attr}" for {self.__class__.__name__} "{self}"')

    @abc.abstractmethod
    def _determine_form(self): pass
    @abc.abstractmethod
    def _add_simple_attrs(self): pass
    @abc.abstractmethod
    def _add_full_attrs(self): pass

    # noinspection PyProtectedMember,PyProtectedMember,PyShadowingBuiltins,PyShadowingBuiltins
    @classmethod
    def from_id(cls, id):
        """
        constructor for creating from spotify id,
        IE Artist.from_id('sdfsadfsa')
        can actually take ID, URI or URL since all have id in them

        """

        if type(id) == str:
            id = get_id(id)
            if not is_id(id) :
                return None
            return cls._if_id_cached( id, returnbool=False)

        if type(id) == list:
            if len(id) < 1:
                return []

            not_cached_items = []
            cached_items = []

            for individual_id in id:
                individual_id = get_id(individual_id)
                cached = cls._if_id_cached(individual_id, returnbool=True)
                if cached is False:
                    not_cached_items.append(individual_id)
                else:
                    cached_items.append(cached)

            if len(not_cached_items) < 1 :
                return cached_items
            return cls._api_multiple(not_cached_items) + cached_items

        raise Exception('From_id input must be either a string ID or a list of IDs')

    def _get_full_attribute(self, attribute: str):
        cls = self.__class__
        if self._form == "simplified":
            self._apidict = getattr(self._api,"single_"+cls.__name__.lower())(self.id)
            self._add_full_attrs()
            self._form = "full"
        return getattr(self, attribute)

    @classmethod
    def _dict_if_cached(cls, dictlist:list) -> list :
        existing = []
        new = []
        for dictionary in dictlist :
            if dictionary['id'] in cls.cache['ids'] :
                existing.append(cls.cache['ids'][dictionary['id']])
            else : new.append(cls(dictionary))
        return new + existing

    @classmethod
    def _if_id_cached(cls, id: str, returnbool: bool = False):
        """
        cachetype: "ids" or "names"
        key = a valid id or name

        """

        if id in cls.cache['ids'] :
            return cls.cache['ids'][id]
        if returnbool :
            return False
        return cls(getattr(cls._api.fget(),"single_"+cls.__name__.lower())(id))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__class__.__name__ + f".from_id('{self.id}') # {self.__class__.__name__} '{self.name}' "


class Searchable(abc.ABC) :

    @classmethod
    def from_search(cls: SpotifyItem, searchstring: str):
        """
        construct an artist, playlist, track, or album from a search. returns the closest match, or none if no artist is found

        """
        stripped = searchstring.lower().strip()
        if stripped in cls.cache['names']:
            return cls.cache['names'][stripped]
        if stripped in cls.cache['searches']:
            return cls.cache['searches'][stripped]

        results = cls._api.fget().search(q=cls.__name__.lower() + ':' + searchstring, types=cls.__name__.lower(), limit=1)
        results = results[cls.__name__.lower() + "s"]["items"]

        if len(results) > 0:
            result = results[0]
            if result['id'] in cls.cache['ids']:
                existed = cls.cache['ids'][result['id']]
                print(f"returning original object, already existed but we couldn't find in cache >{repr(existed)}<")
                return existed
            newitem = cls(result)
            cls.cache['searches'][searchstring] = newitem
            return newitem

        else:
            return None
