"""Lyric and Artwork reader/writer/downloader
"""

import socket
import os
import sqlite3
import Queue
import time
import threading

from base import Object
import rest
import environment


class SqliteDict(Object):
    """Sqlite as a Dict."""
    def __init__(self, path, init, search, search_parser, write, write_parser):
        """Initializes sqlite database.

        :path: sqlite db path
        """
        self.__path = path
        self.__search = search
        self.__search_parser = search_parser
        self.__write = write
        self.__write_parser = write_parser
        self.__connection().execute(init)

    def __connection(self):
        """Returns database instance.

        must generate instance at everytime cause
        sqlite3 is not thread-safe.
        """
        db = sqlite3.connect(self.__path)
        return db

    def __contains__(self, key):
        """D.__contains__(k) -> True if D has a key k, else False"""
        cursor = self.__connection().cursor()
        cursor.execute(self.__search, self.__search_parser(key))
        ret = cursor.fetchone()
        return False if ret == None or ret[0] == '' else True

    def __getitem__(self, key):
        """x.__getitem__(k) <==> x[k]"""
        cursor = self.__connection().cursor()
        cursor.execute(self.__search, self.__search_parser(key))
        ret = cursor.fetchone()
        if ret == None or ret[0] == '':
            raise KeyError(key)
        return ret[0]

    def __setitem__(self, key, value):
        """x.__setitem__(k, v) <==> x[k]=v"""
        connection = self.__connection()
        cursor = connection.cursor()
        cursor.execute(self.__write, self.__write_parser(key) + (value,))
        connection.commit()


class CacheDict(Object, threading.Thread):
    """Cache dict with background setitem."""
    def __init__(self):
        """Initializes cache."""
        self.__first_sleep_time = 10
        self.__queue = Queue.LifoQueue()
        self.__cache = {}
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def __contains__(self, key):
        """D.__contains__(k) -> True if D has a key k, else False"""
        return hash(frozenset(key.items())) in self.__cache

    def __getitem__(self, key):
        """x.__getitem__(k) <==> x[k]"""
        return self.__cache[hash(frozenset(key.items()))]

    def __setitem__(self, key, value):
        """x.__setitem__(k, v) <==> x[k]=v"""
        self.__cache[hash(frozenset(key.items()))] = value

    def run(self):
        """Executes setdefault_later() queue."""
        time.sleep(self.__first_sleep_time)
        while True:
            if not self.__queue.empty():
                key, func, args, kwargs = self.__queue.get()
                if not key in self:
                    try:
                        self[key] = func(*args, **kwargs)
                    except Exception, err:
                        print type(err), err
            time.sleep(0.5)

    def setdefault_later(self, key, func, *args, **kwargs):
        """Sets D[key]=func(*args,**kwargs) in background if key not in D"""
        if not self.is_alive():
            self.start()
        self.__queue.put((key, func, args, kwargs))


class Lyrics(Object):
    """Downloads and manages lyric.
    """
    UPDATING = 'updating'
    UPDATE = 'update'

    def __init__(self, client):
        """init values and database."""
        self.__cache = CacheDict()
        sql_init = '''
        CREATE TABLE IF NOT EXISTS lyrics
        (
            artist TEXT,
            title TEXT,
            album TEXT,
            lyric TEXT,
            UNIQUE(artist, title, album)
        );
        '''
        sql_search = '''
        SELECT lyric FROM lyrics WHERE
            artist=? and
            title=? and
            album=?
        '''
        sql_write = '''
        INSERT OR REPLACE INTO lyrics
        (artist, title, album, lyric)
        VALUES(?,  ?,  ?,  ?)
        '''

        def sql_arg_parser(song):
            return (song.format('%artist%'),
                    song.format('%title%'),
                    song.format('%album%'))

        self.__data = SqliteDict(environment.config_dir + u'/lyrics',
                                 sql_init,
                                 sql_search,
                                 sql_arg_parser,
                                 sql_write,
                                 sql_arg_parser)
        self.client = client
        self.__downloading = []
        self.download_auto = False
        self.download_background = False
        self.downloaders = {'geci_me': True}
        self.download_class = {'geci_me': rest.GeciMe}
        Object.__init__(self)

    def __getitem__(self, song):
        """Returns lyric.

        Arguments:
            song - client.Song object.

        Returns u'' if lyric is not found.
        if not found and self.download_auto,
        downloads and returns lyric.
        if download_background is True,
        run in another thread and raises UPDATING and UPDATE event.

        check self.downloading param to downloading lyric list.
        """
        if song in self.__cache:
            return self.__cache[song]
        if song in self.__data:
            self.__cache[song] = self.__data[song]
            return self.__cache[song]
        else:
            self.__cache[song] = u''
            if self.download_auto:
                if self.download_background:
                    self.__cache.setdefault_later(song, self.download, song)
                else:
                    return self.download(song)
            return self.__cache[song]

    def __setitem__(self, song, lyric):
        """Saves lyric.

        Arguments:
            song - song object.
            lyric - string lyric.
        """
        lyric = unicode(lyric)
        self.__cache[song] = lyric
        if lyric:
            self.__data[song] = lyric
            self.call(self.UPDATE, song, lyric)

    def download(self, song):
        # load client config and enable/disable api
        if self.client.config.lyrics_download:
            downloaders = {}
            for label, isd in self.downloaders.iteritems():
                attr = u'lyrics_api_' + label
                downloaders[label] = getattr(self.client.config, attr)
            self.downloaders = downloaders
        else:
            return ''
        self.__downloading.append(song)
        self.call(self.UPDATING)
        lyric = u''
        for label, is_download in self.downloaders.iteritems():
            if is_download:
                downloader = self.download_class[label]()
                lyric = downloader.download(song)
                if lyric:
                    break
            else:
                pass
        del self.__downloading[self.__downloading.index(song)]
        self.__setitem__(song, lyric)
        return lyric

    def list(self, keywords, callback=None):
        """Returns candidate lyrics of given song.

        Arguments:
            keywords -- keyword dict like dict(artist=foo, title=bar)
            callback -- if not None,  callback(*each_list_item)

        Returns list like:
            [
                ( downloadfunc, urlinfo formatter func,  urlinfo list),
                ...,
            ]

        to get lyric list[0][0]:
            returnslist = db.list(keywords)
            func, formatter, urlinfo_list = returnslist[0]
            lyric = func(urlinfo_list[0])
            db[song] = lyric

        to show readable candidate lyric:
            returnslist = db.list(keywords)
            for func, formatter, urlinfo_list in returnslist:
                for urlinfo in urlinfo_list:
                    print formatter(urlinfo)
        """

        lists = []
        for label, is_download in self.downloaders.iteritems():
            if is_download:
                downloader = self.download_class[label]()
                urls = downloader.list(**keywords)
                appends = (downloader.get, downloader.format, urls)
                lists.append(appends)
                if callback:
                    callback(*appends)
            else:
                pass
        return lists

    downloading = property(lambda self: self.__downloading)


class Artwork(Object):
    """Downloads and manages Artwork.
    """
    UPDATING = 'updating'
    UPDATE = 'update'

    def __init__(self, client):
        """init values and database."""
        self.client = client
        self.__download_path = environment.config_dir + '/artwork'
        self.__downloading = []
        self.download_auto = False
        self.download_background = False
        self.downloaders = {'lastfm': True}
        self.download_class = {'lastfm': rest.ArtworkLastfm}

        sql_init = '''
        CREATE TABLE IF NOT EXISTS artwork
        (   artist TEXT,
            album TEXT,
            artwork TEXT,
            UNIQUE(artist, album)
        );
        '''
        sql_search = '''
        SELECT artwork FROM artwork WHERE
            artist=? and
            album=?
        '''
        sql_write = '''
        INSERT OR REPLACE INTO artwork
        (artist, album, artwork)
        VALUES(?,  ?,  ?)
        '''

        def sql_arg_parser(song):
            return (song.format('%albumartist%'),
                    song.format('%album%'))

        self.__data = SqliteDict(environment.config_dir + '/artworkdb',
                                 sql_init,
                                 sql_search,
                                 sql_arg_parser,
                                 sql_write,
                                 sql_arg_parser)
        self.__cache = CacheDict()
        Object.__init__(self)

    def __getitem__(self, song):
        """Returns artwork path.

        Arguments:
            song - client.Song object.

        Returns u'' if artwork is not found.
        if not found and self.download_auto,
        downloads and returns artwork path.
        if download_background is True,
        run in another thread and raises UPDATING and UPDATE event.

        check self.downloading param to downloading artwork list.
        """
        if song in self.__cache:
            return self.__cache[song]
        if song in self.__data:
            self.__cache[song] = self.__download_path + '/' + self.__data[song]
            return self.__cache[song]
        else:
            self.__cache[song] = u''
            if self.download_auto:
                if self.download_background:
                    self.__cache.setdefault_later(song, self.download, song)
                else:
                    return self.download(song)
            return u''

    def __setitem__(self, song, artwork_binary):
        """Saves artwork binary.

        Arguments:
            song - song object.
            artwork - string artwork binary, not filepath.
        """
        # save binary to local dir.
        if artwork_binary:
            filename = song.format('%albumartist% %album%')
            fullpath = self.__download_path + '/' + filename
            if not os.path.exists(os.path.dirname(fullpath)):
                os.makedirs(os.path.dirname(fullpath))
            f = open(fullpath, 'wb')
            f.write(artwork_binary)
            f.close()
        else:
            fullpath = u''
            filename = u''
        self.__cache[song] = fullpath

        # save filepath to database.
        if fullpath:
            self.__data[song] = filename
            self.call(self.UPDATE, song, fullpath)

    def download(self, song):
        if not song in self.__downloading:
            # load client config and enable/disable api
            if self.client.config.artwork_download:
                downloaders = {}
                for label, isd in self.downloaders.iteritems():
                    attr = u'artwork_api_' + label
                    downloaders[label] = getattr(self.client.config, attr)
                self.downloaders = downloaders
            else:
                return ''
            self.__downloading.append(song)
            self.__setitem__(song, u'')  # flush for terrible lock.
            self.call(self.UPDATING)
            artwork_binary = u''
            for label, is_download in self.downloaders.iteritems():
                if is_download:
                    downloader = self.download_class[label]()
                    artwork_binary = downloader.download(song)
                    if artwork_binary:
                        break
                else:
                    pass
            self.__setitem__(song, artwork_binary)
            return self.__getitem__(song)
        else:
            return ''

    def list(self, keywords, callback=None):
        """Returns candidate artworks of given song.

        Arguments:
            keywords -- keyword dict like dict(artist=foo, title=bar)
            callback -- if not None,  callback(*each_list_item)

        Returns list like:
            [
                ( downloadfunc, urlinfo formatter func,  urlinfo list),
                ...,
            ]

        to get artwork list[0][0]:
            returnslist = db.list(keywords)
            func, formatter, urlinfo_list = returnslist[0]
            artwork_binary = func(urlinfo_list[0])
            db[song] = artwork_binary

        to show readable candidate artworks:
            returnslist = db.list(keywords)
            for func, formatter, urlinfo_list in returnslist:
                for urlinfo in urlinfo_list:
                    print formatter(urlinfo)
        """

        lists = []
        for label, is_download in self.downloaders.iteritems():
            if is_download:
                downloader = self.download_class[label]()
                urls = downloader.list(**keywords)
                appends = (downloader.get, downloader.format, urls)
                lists.append(appends)
                if callback:
                    callback(*appends)
            else:
                pass
        return lists

    downloading = property(lambda self: self.__downloading)
