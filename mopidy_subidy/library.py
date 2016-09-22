from mopidy import backend, models
from mopidy.models import Ref, SearchResult
from mopidy_subidy import uri

import logging
logger = logging.getLogger(__name__)

class SubidyLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri=uri.ROOT_URI, name='Subsonic')

    def __init__(self, *args, **kwargs):
        super(SubidyLibraryProvider, self).__init__(*args, **kwargs)
        self.subsonic_api = self.backend.subsonic_api

    def browse_songs(self,album_id):
        return self.subsonic_api.get_songs_as_refs(album_id)

    def browse_albums(self, artist_id):
        return self.subsonic_api.get_albums_as_refs(artist_id)

    def browse_artists(self):
        return self.subsonic_api.get_artists_as_refs()

    def lookup_song(self, song_id):
        return self.subsonic_api.get_song_by_id(song_id)

    def lookup_album(self, album_id):
        return self.subsonic_api.get_album_by_id(album_id)

    def lookup_artist(self, artist_id):
        return self.subsonic_api.get_artist_by_id(artist_id)

    def browse(self, browse_uri):
        type = uri.get_type(browse_uri)
        if browse_uri == uri.ROOT_URI:
            return self.browse_artists()
        if type == uri.ARTIST:
            return self.browse_albums(uri.get_artist_id(browse_uri))
        if type == uri.ALBUM:
            return self.browse_songs(uri.get_album_id(browse_uri))

    def lookup_one(self, lookup_uri):
        type = uri.get_type(lookup_uri)
        if type == uri.ARTIST:
            return self.lookup_artist(uri.get_artist_id(lookup_uri))
        if type == uri.ALBUM:
            return self.lookup_album(uri.get_album_id(lookup_uri))
        if type == uri.SONG:
            return self.lookup_song(uri.get_song_id(lookup_uri))

    def lookup(self, uri=None, uris=None):
        if uris is not None:
            return [self.lookup_one(uri) for uri in uris]
        if uri is not None:
            return [self.lookup_one(uri)]
        return None

    def refresh(self, uri):
        pass

    def search_uri(self, query):
        type = uri.get_type(lookup_uri)
        if type == uri.ARTIST:
            artist = self.lookup_artist(uri.get_artist_id(lookup_uri))
            if artist is not None:
                return SearchResult(artists=[artist])
        elif type == uri.ALBUM:
            album = self.lookup_album(uri.get_album_id(lookup_uri))
            if album is not None:
                return SearchResult(albums=[album])
        elif type == uri.SONG:
            song = self.lookup_song(uri.get_song_id(lookup_uri))
            if song is not None:
                return SearchResult(tracks=[song])
        return None

    def search_by_artist_album_and_track(self, artist_name, album_name, track_name):
        tracks = self.search_by_artist_and_album(artist_name, album_name)
        track = next(item for item in tracks.tracks if track_name in item.name)
        return SearchResult(tracks=[track])

    def search_by_artist_and_album(self, artist_name, album_name):
        artists = self.subsonic_api.get_raw_artists()
        artist = next(item for item in artists if artist_name in item.get('name'))
        albums = self.subsonic_api.get_raw_albums(artist.get('id'))
        album = next(item for item in albums if album_name in item.get('title'))
        return SearchResult(tracks=self.subsonic_api.get_songs_as_tracks(album.get('id')))

    def get_distinct(self, field, query):
        search_result = self.search(query)
        if not search_result:
            return []
        if field == 'track' or field == 'title':
            return [track.name for track in (search_result.tracks or [])]
        if field == 'album':
            return [album.name for album in (search_result.albums or [])]
        if field == 'artist':
            if not search_result.artists:
                return [artist.name for artist in self.browse_artists()]
            return [artist.name for artist in search_result.artists]

    def search(self, query=None, uris=None, exact=False):
        if 'artist' in query and 'album' in query and 'track_name' in query:
            return self.search_by_artist_album_and_track(query.get('artist')[0], query.get('album')[0], query.get('track_name')[0])
        if 'artist' in query and 'album' in query:
            return self.search_by_artist_and_album(query.get('artist')[0], query.get('album')[0])
        if 'artist' in query:
            return self.subsonic_api.find_as_search_result(query.get('artist')[0])
        if 'any' in query:
            return self.subsonic_api.find_as_search_result(query.get('any')[0])
        return SearchResult(artists=self.subsonic_api.get_artists_as_artists())

