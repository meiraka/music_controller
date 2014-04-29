"""
Event driven mpd client module.

"""

import os
import codecs
import copy
import json
import re
import time
import thread
import threading
import mpd
import socket
import traceback

from base import Object

import database

class Data(dict):
    __getattr__ = dict.__getitem__

class Song(Data):
    splitter = re.compile(u'\\%\\%')
    __param = re.compile(u'\\%([^\\%]+\\%)')
    def __init__(self, data, artwork=None, lyrics=None):
        if u'time' in data:
            t = int(data[u'time'].split(u':')[0])
            data[u'length'] = u'%i:%s' % (t/60, str(t%60).zfill(2))
        if data.has_key(u'track'):
            data[u'track_index'] = data[u'track'].zfill(2)
        if not data.has_key(u'albumartist') and data.has_key(u'artist'):
            data[u'albumartist'] = data[u'artist']
        self.__artwork = artwork
        self.__lyrics = lyrics
        Data.__init__(self, data)

    def format(self, format_string):
        v = self.splitter.split(format_string)
        f = [u''.join([ self[ii[:-1]] if ii.endswith(u'%') and len(ii) > 0 and self.has_key(ii[:-1]) else u' [no %s] ' % ii[:-1] if ii.endswith(u'%') else ii  for ii in self.__param.split(i)]) for i in v]
        return u'%%'.join(f)

    def __get_artwork(self):
        return self.__artwork[self] if self.__artwork else ''

    def __get_lyric(self):
        return self.__lyrics[self] if self.__lyrics else ''

    artwork = property(__get_artwork)
    lyric   = property(__get_lyric)
        
class Error(Exception):
    pass


class Client(Object):
    '''
    MPD client. This object can connect,  control and manage mpd.

    Attributes:
        config -- connection settings for this client.
        playback -- control(play,  pause and etc.) mpd status.
    '''
    def __init__(self, config_path='./'):
        Object.__init__(self)
        self.__config     = Config(config_path)
        self.__artwork    = database.Artwork(self)
        self.__lyrics     = database.Lyrics(self)
        self.__connection = Connection(self.config)
        self.__playback   = Playback(self.__connection, self.__config)
        args = [self.__connection, self.__playback, self.__config, self.__artwork, self.__lyrics]
        self.__library    = Library(*args)
        self.__playlist   = Playlist(*args)

    def connect(self, profile=None):
        return self.__connection.connect(profile)

    def start(self):
        self.__connection.start()

    config = property(lambda self:self.__config)
    playback = property(lambda self:self.__playback)
    library = property(lambda self:self.__library)
    playlist = property(lambda self:self.__playlist)
    connection = property(lambda self:self.__connection)
    artwork = property(lambda self:self.__artwork)
    lyrics = property(lambda self:self.__lyrics)
    

class Connection(Object, threading.Thread):
    '''
    A connection object manages mpd connection and execute commands.
    To connect to mpd,  call the Connection.connect().

    Event signals:
        UPDATE -- when status has been changed.
        UPDATE_DATABASE -- when database updating job was finished.
        UPDATE_PLAYLIST -- when playlist has been changed.
        UPDATE_PLAYING -- when current playing song was changed.

    '''

    CONNECT = 'connect'
    CLOSE = 'close'
    CLOSE_UNEXPECT = 'close_unexpect'
    UPDATE = 'updated'
    UPDATE_DATABASE = 'updated_database'
    UPDATE_PLAYLIST = 'updated_playlist'
    UPDATE_PLAYING = 'update_playing'
    SERVER_ERROR = 'server_error'
    CLOCK = 'clock'
    def __init__(self, config):
        Object.__init__(self)
        threading.Thread.__init__(self)
        self.__running = False
        self.daemon = True
        self.__config = config
        self.__current = None
        self.__connection = None
        self.__lock = thread.allocate_lock()
        self.__status = ''
        # server status checker.
        self.__server_status = {}
        self.__check_playlist = None
        self.__check_library = None
        self.__server_status_song = None
        self.connected = False

    def run(self):
        """ crawling mpd to check update.
        """
        while True:
            self.__running = True
            try:
                self.update()
                time.sleep(1)
            except:
                print 'daemon err:',  traceback.format_exc()

    def check_library(self):
        """ Check library updates.
        """
        self.__check_library = True

    def update(self):
        status = self.execute('status')
        if status and not self.__server_status == status:
            self.__server_status = status
            self.call(self.UPDATE)
            # check playlist
            if not self.__check_playlist == self.__server_status[u'playlist']:
                self.__check_playlist = self.__server_status[u'playlist']
                self.call(self.UPDATE_PLAYLIST)
            # check playing song
            if u'song' in self.__server_status and self.__server_status[u'song'] is not None and not self.__server_status_song == self.__server_status[u'song']:
                self.__server_status_song = self.__server_status[u'song']
                self.call(self.UPDATE_PLAYING)
        if not self.__check_library == False and \
            not self.__server_status.has_key('updating_db'):
            self.__check_library = False
            self.call(self.UPDATE_DATABASE)
        elif self.__server_status.has_key('updating_db'):
            self.__check_library = self.__server_status['updating_db']
        if u'error' in self.__server_status and self.__server_status[u'error']:
            self.call(self.SERVER_ERROR, self.__server_status[u'error'])
            self.execute('clearerror')
        self.call(self.CLOCK)

    def connect(self, profile=None):
        '''connect to mpd daemon.

        Arguments:
        profile -- string profile name. if none,  uses default value.
        '''
        connection = mpd.MPDClient()
        if not profile:
            if not self.__current:
                profile = self.__config.default_profile
            else:
                profile = self.__current    
        try:
    
            mpd.socket.setdefaulttimeout(2)
            connection.connect(profile[1].encode('utf8'), int(profile[2]))
            if profile[3]:
                connection.password(profile[4])
            self.__connection = connection
            self.__current = copy.copy(profile)
            self.connected = True
            self.update()
            self.call(self.CONNECT)
        except mpd.MPDError, err:
            self.__status = err
            return False
        except socket.error, err:
            self.__status = err
            return False
        #if connection was established
        return True

    def close(self):
        self.connected = False
        self.__current = None
        try:
            self.__connection.disconnect()
        except:
            pass
        self.call(self.CLOSE)

    def __enter__(self):
        self.execute('command_list_ok_begin')

    def __exit__(self, exc_type,  exc_value,  traceback):
        self.execute('command_list_end')
        return True

    def execute(self, func_name, skip=False, *args, **kwargs):
        '''execute mpd commands.
        
        execute given mpd command. while executing command,  can not execute
        another commands.
        
        Arguments:
        func_name - string or list mpd command names.
        Returns:
        structure of mpd returns.
        ''' 
        value = None
        if not self.connected:
            return value
        if self.__lock.acquire(not(skip)):
            re_execute = False
            if kwargs.has_key(u're_execute'):
                del kwargs[u're_execute']
                re_execute = True
            try:
                if type(func_name) == str or type(func_name) == unicode:
                    func_name = str(func_name)
                    value = self.__decode(getattr(self.__connection, func_name)(*args, **kwargs))
            except mpd.ProtocolError:
                self.connected = False
                self.__current = None
                self.call(self.CLOSE_UNEXPECT)
            except mpd.MPDError, err:
                print 'err at', func_name, args, kwargs
                print 'mpderr', traceback.format_exc()
                    
            except socket.timeout, err:
                pass
            except socket.error:
                self.connected = False
                self.__current = None
                self.call(self.CLOSE_UNEXPECT)
            except AttributeError, err:
                pass
            except Exception, err:
                print traceback.format_exc()
            finally:
                self.__lock.release()
        else:
            return False
        return value

    def __decode(self, item):
        """ Decodes given utf-8 object to unicode object.

        decodes str and str in non-nested dict and list to
        unicode each object.
        """
        if type(item) == str:
            return item.decode('utf8')
        elif type(item) == dict:
            returns = {}
            for key, value in item.iteritems():
                key = self.__decode(key)
                if type(value) == str:
                    returns[key] = self.__decode(value)
                elif type(value) == list:
                    returns[key] = self.__decode(';'.join(value))
                else:
                    returns[key] = value
            return Data(returns)
        elif type(item) == list:
            return [self.__decode(info) for info in item]
        else:
            return item

    def __get_server_status(key=None, cast=None):
        def get(self):
            if not self.__running:
                self.update()
            if key is None:
                return self.__server_status
            else:
                if type is None:
                    return self.__server_status[key]
                else:
                    return cast(self.__server_status[key])
        return get

    def __get_server_stats():
        def get(self):
            return self.execute('stats')
        return get

    def __get_server_version():
        def get(self):
            return self.__connection.mpd_version if self.connected else ''
        return get

    def __get_server_decoders():
        def get(self):
            return self.execute('decoders')
        return get


    
    current = property(lambda self:self.__current)
    server_status = property(__get_server_status())
    server_stats = property(__get_server_stats())
    server_version = property(__get_server_version())
    server_decoders = property(__get_server_decoders())
    
    
class Playback(Object):
    '''
    Controlls playback interface.

    '''
    class Device(object):
        def __init__(self, connection, kwargs):
            self.connection = connection
            self.__id = kwargs[u'outputid']
            self.name = kwargs[u'outputname']
            self.__enable = True if kwargs[u'outputenabled'] == u'1' else False

        def enable(self):
            self.connection.execute('enableoutput', True, self.__id)
            self.__enable = True

        def disable(self):
            self.connection.execute('disableoutput', True, self.__id)
            self.__enable = False

        def is_enable(self):
            return self.__enable


    def __init__(self, connection, config):
        Object.__init__(self)
        self.connection = connection
        self.config = config

    def __check_status(self, key, value):
        status = self.connection.server_status
        if key in status and status[key] == value:
            return True
        else:
            return False
        

    def play(self, song=None, block=False):
        if song:
            self.connection.execute('play', not(block), song[u'pos'])
        else:
            self.connection.execute('play', not(block))

    def is_play(self):
        return self.__check_status(u'state', u'play')

    def stop(self, block=False):
        self.connection.execute('stop', not(block))

    def is_stop(self):
        return self.__check_status(u'state', u'stop')

    def pause(self, block=False):
        self.connection.execute('pause', not(block))

    def is_pause(self):
        return self.__check_status(u'state', u'pause')

    def next(self, block=False):
        self.connection.execute('next', not(block))
    
    def previous(self, block=False):
        self.connection.execute('previous', not(block))

    def random(self, activate, block=False):
        arg = '1' if activate else '0'
        self.connection.execute('random', not(block), arg)

    def is_random(self):
        return self.__check_status(u'random', u'1')

    def repeat(self, activate, block=False):
        arg = '1' if activate else '0'
        self.connection.execute('repeat', not(block), arg)

    def is_repeat(self):
        return self.__check_status(u'repeat', u'1')

    def single(self, activate, block=False):
        arg = '1' if activate else '0'
        self.connection.execute('single', not(block), arg)

    def is_single(self):
        return self.__check_status(u'single', u'1')

    def seek(self, second):
        song_id = self.song
        if song_id is not None:
            self.connection.execute('seek', True, song_id, second)

    def __get(key, value_type, default):
        def get(self):
            status = self.connection.server_status
            if status and key in status:
                return value_type(status[key])
            else:
                return default
        return get

    def __set(command, default=0):
        def set(self, value):
            if value is None:
                value = default
            self.connection.execute(command, True, value)
        return set

    def __get_devices():
        def get(self):
            def generate_device(connection, kwargs):
                try:
                    return Playback.Device(connection, kwargs)
                except KeyError:
                    return None
            return [dev for dev in [generate_device(self.connection, i) for i in self.connection.execute(u'outputs')] if dev]

        return get
    time = property(__get(u'time', int, 0))
    volume = property(__get(u'volume', int, 100), __set(u'setvol'))
    crossfade = property(__get(u'xfade', int, 0), __set(u'crossfade'))
    devices = property(__get_devices())
    
        
class Playlist(Object):
    """ This class provides current MPD play queue.
    """
    UPDATE = 'update'
    UPDATE_CURRENT = 'update_current'
    FOCUS = 'focus'
    SELECT = 'select'

    class Song(Song):
        """ A playable song object.
        """
        def __init__(self, song, connection, artwork, lyrics):
            Song.__init__(self, song, artwork, lyrics)
            self.__connection = connection

        def play(self):
            """ Plays this song.
            """
            self.__connection.execute(u'play', True, self[u'pos'])

        def remove(self):
            """ Removes from playlist.
            """
            self.__connection.execute(u'deleteid', False, self[u'id'])
            
    def __init__(self, connection, playback, config, artwork, lyrics):
        Object.__init__(self)
        self.__connection = connection
        self.__playback = playback
        self.__config = config
        self.__artwork = artwork
        self.__lyrics = lyrics
        self.__data = []
        self.__selected = []
        self.__focused = None
        self.__current = None
        self.__connection.bind(self.__connection.CONNECT, self.__update_cache)
        self.__connection.bind(self.__connection.UPDATE_PLAYLIST, self.__update_cache)
        self.__connection.bind(self.__connection.UPDATE, self.__focus_playing)

    def __iter__(self):
        return list.__iter__(self.__data)

    def __getitem__(self, index):
        return self.__data[index]

    def __delitem__(self, index):
        pos = self.__data[index][u'pos']
        self.__connection.execute('delete', False, pos)
        self.__connection.update()

    def __delslice__(self, start, end):
        self.__connection.execute('delete', False, '%i:%i' % (start, end))
        self.__connection.update()

    def __getslice__(self, start, end):
        return self.__data[start:end]

    def __len__(self):
        return len(self.__data)

    def __update_cache(self):
        """ update playlist songs cache.
        """
        data = self.__connection.execute('playlistinfo')
        self.__data = [Playlist.Song(song, self.__connection, self.__artwork, self.__lyrics) for song in data]
        if self.__config.playlist_focus:
            self.focus_playing()
        self.call(self.UPDATE)

    def focus_playing(self):
        """ set focus and select value to current playing song.
        """
        if not u'song' in self.__connection.server_status:
            return False
        song_id = int(self.__connection.server_status[u'song'])
        if song_id is None:
            return False
        if not len(self.__data) > song_id:
            return False
        song = self.__data[song_id]
        if not self.__current == song:
            self.__current = song
            self.__set_select([song])
            self.__set_focus(song)
            self.call(self.UPDATE_CURRENT, song)

    def __focus_playing(self, *args, **kwargs):
        self.focus_playing()

    def __set_select(self, songs):
        self.__selected = [int(song[u'pos']) for song in songs]
        self.call(self.SELECT)

    def __set_focus(self, song):
        self.__focused = int(song[u'pos'])
        self.call(self.FOCUS)

    def append(self, song):
        """apennd song to end of playlist.
        """
        add = 'add'
        filepath = song[u'file'].encode('utf8')
        self.__connection.execute(add, False, filepath)
        self.__connection.update()

    def extend(self, songs):
        """marge the playlist and given songs into the playlist.
        """
        add = 'add'
        filepath = [song[u'file'].encode('utf8') for song in songs if song.has_key(u'file')]
        with self.__connection:
            for i in filepath:
                self.__connection.execute('add', False, i)
        self.__connection.update()

    def clear(self):
        """Clear current playlist.
        """
        self.__connection.execute('clear', False)
        self.__connection.update()

    def replace(self, songs):
        """ Replaces playlist by given songs.

        if mpd plays song,  search that in given songs and
        plays after playlist was updated.

        Arguments:
            songs - list of Song object.
        """
        status = self.__connection.server_status
        # set seek pos
        seek = False
        id = 0
        song_id = None
        if u'song' in status:
            song_id = int(status[u'song'])
        if song_id is not None:
            if len(self.__data) > song_id:
                play_song = self.__data[song_id]
                check_keys = [u'file']
                time = status[u'time'].split(':')[0] if u'time' in status else '0'
                for index, song in enumerate(songs):
                    for i in check_keys:
                        if not i in song and i in play_song:
                            break
                        if not song[i] == play_song[i]:
                            break
                    else:
                        id = index
                        seek = True
                        break
        filepath = [song[u'file'].encode('utf8') for song in songs if song.has_key(u'file')]
        with self.__connection:
            self.__connection.execute('clear')
            for i in filepath:
                self.__connection.execute('add', False, i)
            if seek:
                self.__connection.execute('seek', False, str(id), time)
                if u'state' in status and status[u'state'] == u'play':
                    self.__connection.execute('play')
                else:
                    self.__connection.execute('pause')
        self.__connection.update()

    

    current = property(lambda self:copy.copy(self.__data[self.current_index]))
    current_index = property(lambda self:int(self.__connection.server_status[u'song']))
    selected = property(lambda self:[self.__data[pos] for pos in self.__selected if len(self.__data) > pos], __set_select)
    focused = property(lambda self:self.__data[self.__focused] if not self.__focused == None and len(self.__data) > self.__focused else None, __set_focus)
        



class Library(Object):
    UPDATE = 'update'
    def __init__(self, connection, playback, config, artwork, lyrics):
        Object.__init__(self)
        self.__connection = connection
        self.__playback = playback
        self.__config = config
        self.__artwork = artwork
        self.__lyrics = lyrics
        self.__data = []
        self.__connection.bind(self.__connection.CONNECT, self.__update_cache)
        self.__connection.bind(self.__connection.UPDATE_DATABASE, self.__update_cache)

    def __iter__(self):
        return list.__iter__(self.__data)

    def __getitem__(self, index):
        return self.__data[index]

    def __getslice__(self, start, end):
        return self.__data[start:end]

    def __len__(self):
        return len(self.__data)

    def update(self):
        """ Update library database in background.

        to catch updated event,  bind Library.UPDATE.
        """
        self.__connection.check_library()
        self.__connection.execute('update')

    def __update_cache(self):
        """ update library songs cache.
        """
        data = self.__connection.execute('listallinfo')
        # remove invalid songs.
        if data:
            self.__data = [Song(songinfo, self.__artwork, self.__lyrics) for songinfo in data if songinfo.has_key(u'file')]
        else:
            self.__data = []
        self.call(self.UPDATE)


class Songs(list):
    def __init__(self, song_list):
        list.__init__(song_list)

    

class Config(Object):
    """
    Settings for Client.

    Attributes:
        profiles -- list of mpd connection settings.
        default_profile -- default mpd connection settings.
    """
    class ConfigError(Error):
        pass
    CONFIG_CHANGED = 'config_changed'
    PLAYLIST_STYLE_SONGS = 1
    PLAYLIST_STYLE_ALBUMS = 1 << 1
    def __init__(self, path='./'):
        """ initializes config by given path.
        
        Arguments:
            path -- string json config filepath.
        """
        self.path = path
        if not self.path[-1] == '/':
            self.path = self.path + '/'
        self.__config = {}
        Object.__init__(self)
        self.load()

    def load(self):
        """ reload config.
        """
        if os.path.exists(self.path+'config.json'):
            try:
                f = codecs.open(self.path+'config.json', 'r', 'utf8')
                dumps = f.read()
                f.close()
                self.__config = json.loads(dumps)
            except TypeError:
                pass

    def save(self):
        """ save current config.
        """
        dumps = json.dumps(self.__config)
        try:
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            f = codecs.open(self.path + 'config.json', 'w', 'utf8')
            f.write(dumps)
            f.close()
        except ValueError:
            pass

    def __get_profiles(self):
        if not self.__config.has_key(u'profiles'):
            self.__config[u'profiles'] = [[u'default', u'localhost', u'6600', False, u'']]
        return copy.deepcopy(self.__config[u'profiles'])

    def __set_profiles(self, profiles):
        if not type(profiles) == list:
            cause ='given:'+unicode(type(profiles))+' require:'+unicode(list)
            raise TypeError(cause)
        else:
            for profile in profiles:
                if not [type(item) for item in profile] == [unicode, unicode, unicode, bool, unicode]:
                    cause = 'given:'+unicode([type(item) for item in profile])+' require:'+unicode([unicode, unicode, unicode, bool, unicode])
                    raise TypeError(cause)
            if len(profiles) == 0:
                raise IndexError(0)
        self.__config[u'profiles'] = profiles
        self.save()
        self.call(self.CONFIG_CHANGED)

    profiles = property(__get_profiles, __set_profiles)

    def __get_default_profile(self):
        if not self.__config.has_key(u'default_profile'):
            for name, _, _, _, _ in self.__get_profiles():
                if name == u'default':
                    self.__config[u'default_profile'] = name
                    break
            else:
                self.__config[u'default_profile'] = self.__get_profiles()[0][0]
        for profile in self.__get_profiles():
            if profile[0] == self.__config[u'default_profile']:
                return profile
        self.__config[u'default_profile'] = self.__get_profiles()[0][0]
        return self.__get_profiles()[0]

    default_profile = property(__get_default_profile)

    def __get_bool(key, default):
        def _get(self):
            if not key in self.__config:
                self.__config[key] = True if default else False
            return self.__config[key]
        def _set(self, value):
            self.__config[key] = True if value else False
            self.save()
            self.call(self.CONFIG_CHANGED)

        return (_get, _set)

    def __get_unicode(key, default):
        def _get(self):
            if not key in self.__config:
                self.__config[key] = unicode(default)
            return self.__config[key]
        def _set(self, value):
            self.__config[key] = value
            self.save()
            self.call(self.CONFIG_CHANGED)

        return (_get, _set)

    def __get_tuple(key, default):
        def _get(self):
            if not key in self.__config:
                self.__config[key] = list(default)
            return tuple(self.__config[key])
        def _set(self, value):
            if len(value) == len(self.window_size):
                self.__config[key] = list(value)
                self.save()
                self.call(self.CONFIG_CHANGED)
        return (_get, _set)

    def __get(key, keytype, default):
        def _get(self):
            if not key in self.__config:
                self.__config[key] = keytype(default)
            return self.__config[key]
        def _set(self, value):
            self.__config[key] = value
            self.save()
            self.call(self.CONFIG_CHANGED)
        return (_get, _set)

    playlist_focus =     property(*__get_bool(u'playlist_focus', True))
    view =           property(*__get(u'view', unicode,  u''))
    info =           property(*__get_bool(u'info', True))
    lyrics_download =    property(*__get_bool(u'lyrics_download', False))
    lyrics_api_geci_me = property(*__get_bool(u'lyrics_api_geci_me', False))
    artwork_download =   property(*__get_bool(u'artwork_download', True))
    artwork_api_lastfm = property(*__get_bool(u'artwork_api_lastfm', True))
    window_size =    property(*__get_tuple(u'window_size', (-1, -1)))
    notify_growl =       property(*__get_bool(u'notify_growl', True))
    notify_growl_host =  property(*__get_unicode(u'notify_growl_host', u'localhost'))
    notify_growl_pass =  property(*__get_unicode(u'notify_growl_pass', u''))
    notify_osd =     property(*__get_bool(u'notify_osd', True))
    
