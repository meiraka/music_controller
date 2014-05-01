"""
Lyrics reader and writer.

Supports read,  write,  search and download lyrics.

"""

import socket
import os
import sqlite3
import Queue
import threading

from base import Object
import rest
import environment

class CacheManager(Object, threading.Thread):
    def __init__(self, path):
        self.__path = path
        self.__download_queue = Queue.LifoQueue()
        self.__cache = {}
        
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.start()

    def __setitem__(self, key, value):
        self.__cache[hash(frozenset(key.items()))] = value

    def __getitem__(self, key):
        return self.__cache[hash(frozenset(key.items()))]

    def connection(self):
        """ Returns database instance.

        must generate instance at everytime cause
        sqlite3 is not thread-safe.
        """
        db = sqlite3.connect(self.__path)
        return db

    def run(self):
        while True:
            if not self.__download_queue.empty():
                song = self.__download_queue.get()
                if not hash(frozenset(song.items())) in self.__cache:
                    try:
                        self.download(song)
                    except Exception, err:
                        print type(err), err

    def add_download_queue(self, obj):
        self.__download_queue.put(obj)

class Lyrics(CacheManager):
    """
    Downloads and manages lyric.
    """
    UPDATING = 'updating'
    UPDATE = 'update'
    def __init__(self, client):
        """ init values and database."""
        CacheManager.__init__(self, environment.config_dir+u'/lyrics')
        self.client = client
        self.__downloading = []
        self.download_auto = False
        self.download_background = False
        self.downloaders = dict(
            geci_me = True
            )

        self.download_class = dict(
            geci_me = rest.GeciMe
            )
        """ init database.

        if not exists database,  create table.
        """
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
        Object.__init__(self)
        connection = self.connection()
        connection.execute(sql_init)

    def clear_empty(self):
        """ Clears no lyrics data raw(fail to download or no lyrics found raw).
        """
        sql_clear = 'delete from lyrics where lyric="None";'
        connection = self.connection()
        connection.execute(sql_clear)
        connection.commit()
        
       
    def __getitem__(self, song):
        """ Returns lyric.

        Arguments:
            song - client.Song object.

        Returns u'' if lyric is not found.
        if not found and self.download_auto,
        downloads and returns lyric.
        if download_background is True,
        run in another thread and raises UPDATING and UPDATE event.

        check self.downloading param to downloading lyric list.
        """
        sql_search = '''
        SELECT lyric FROM lyrics WHERE
            artist=? and
            title=? and
            album=?
        '''
        try:
            return CacheManager.__getitem__(self, song)
        except KeyError:
            pass
        connection = self.connection()
        cursor = connection.cursor()
        cursor.execute(sql_search,
                (
                song.format('%artist%'),
                song.format('%title%'),
                song.format('%album%')
                )
            )
        lyric = cursor.fetchone()
        if lyric is None:
            if self.download_auto:
                if self.download_background:
                    self.add_download_queue(song)
                else:
                    return self.download(song)
            return u''
        else:
            return lyric[0]

    def __setitem__(self, song, lyric):
        """ Saves lyric.

        Arguments:
            song - song object.
            lyric - string lyric.
        """
        CacheManager.__setitem__(self, song, lyric)
        lyric = unicode(lyric)
        sql_write = '''
        INSERT OR REPLACE INTO lyrics
        (artist, title, album, lyric)
        VALUES(?,  ?,  ?,  ?)
        '''
        connection = self.connection()
        cursor = connection.cursor()
        cursor.execute(sql_write,
                (
                song.format('%artist%'),
                song.format('%title%'),
                song.format('%album%'),
                lyric
                )
            )
        connection.commit()
        self.call(self.UPDATE, song, lyric)
        
    def download(self, song):
        # load client config and enable/disable api
        if self.client.config.lyrics_download:
            downloaders = {}
            for label, isd in self.downloaders.iteritems():
                attr = u'lyrics_api_'+label
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
        """ Returns candidate lyrics of given song.

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

    downloading = property(lambda self:self.__downloading)


#!/usr/bin/python

"""
Artwork reader and writer.

Supports read,  write,  search and download artwork.
"""

class Artwork(CacheManager):
    """
    Downloads and manages Artwork.
    """
    UPDATING = 'updating'
    UPDATE = 'update'
    def __init__(self, client):
        """ init values and database."""
        CacheManager.__init__(self, environment.config_dir+'/artworkdb')
        self.client = client
        self.__download_path = environment.config_dir+'/artwork'
        self.__downloading = []
        self.download_auto = False
        self.download_background = False
        self.downloaders = dict(
            lastfm = True
            )

        self.download_class = dict(
            lastfm = rest.ArtworkLastfm
            )
        """ init database.

        if not exists database,  create table.
        """
        sql_init = '''
        CREATE TABLE IF NOT EXISTS artwork
        (
            artist TEXT,
            album TEXT,
            artwork TEXT,
            UNIQUE(artist, album)
        );
        '''
        Object.__init__(self)
        connection = self.connection()
        connection.execute(sql_init)

    def __getitem__(self, song):
        """ Returns artwork path.

        Arguments:
            song - client.Song object.

        Returns u'' if artwork is not found.
        if not found and self.download_auto,
        downloads and returns artwork path.
        if download_background is True,
        run in another thread and raises UPDATING and UPDATE event.

        check self.downloading param to downloading artwork list.
        """
        try:
            return CacheManager.__getitem__(self, song)
        except KeyError:
            pass
        sql_search = '''
        SELECT artwork FROM artwork WHERE
            artist=? and
            album=?
        '''
        connection = self.connection()
        cursor = connection.cursor()
        cursor.execute(sql_search,
                (
                song.format('%albumartist%'),
                song.format('%album%')
                )
            )
        artwork = cursor.fetchone()
        if artwork is None:
            if self.download_auto:
                if self.download_background:
                    self.add_download_queue(song)
                else:
                    return self.download(song)
            return u''
        elif artwork[0]:
            return self.__download_path + '/' + artwork[0]
        else:
            # download is blocked
            # or already downloaded but not found any data.
            return u''

    def __setitem__(self, song, artwork_binary):
        """ Saves artwork binary.

        Arguments:
            song - song object.
            artwork - string artwork binary,  not filepath.
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
        CacheManager.__setitem__(self, song, fullpath)

        # save filepath to database.
        sql_write = '''
        INSERT OR REPLACE INTO artwork
        (artist, album, artwork)
        VALUES(?,  ?,  ?)
        '''
        connection = self.connection()
        cursor = connection.cursor()
        cursor.execute(sql_write,
                (
                song.format('%albumartist%'),
                song.format('%album%'),
                filename
                )
            )
        connection.commit()
        if fullpath:
            self.call(self.UPDATE, song, fullpath)

    def clear_empty(self):
        sql_clear = 'delete from artwork where artwork="";'
        connection = self.connection()
        cursor = connection.cursor()
        cursor.execute(sql_clear)
        connection.commit()
        
        
    def download(self, song):
        if not song in self.__downloading:
            # load client config and enable/disable api
            if self.client.config.artwork_download:
                downloaders = {}
                for label, isd in self.downloaders.iteritems():
                    attr = u'artwork_api_'+label
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
        """ Returns candidate artworks of given song.

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

    downloading = property(lambda self:self.__downloading)



