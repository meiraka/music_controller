"""
event driven mpd client module.
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

class Object(object):
	def __init__(self):
		self.__binds = {}
	def bind(self,event,function):
		"""Binds a function to the event.
		"""
		if not self.__binds.has_key(event):
			self.__binds[event] = []
		if self.__binds[event].count(function) == 0:
			self.__binds[event].append(function)

	def unbind(self,event,function):
		"""Unbinds a function from the event.
		"""
		while not self.__binds[event].count(function) == 0:
			self.__binds[event].remove(function)
			
	def call(self,event,*args,**kwargs):
		"""raise event with given args.
		"""
		if self.__binds.has_key(event):
		 	for function in self.__binds[event]:
				function(*args,**kwargs)
class Data(dict):
	__getattr__ = dict.__getitem__

class Song(Data):
	splitter = re.compile(u'\\%\\%')
	__param = re.compile(u'\\%([^\\%]+\\%)')
	def __init__(self,data):
		data[u'length'] = u'%i:%s' % (int(data[u'time'])/60,str(int(data[u'time'])%60).zfill(2))
		if data.has_key(u'track'):
			data[u'track_index'] = data[u'track'].zfill(2)
		if not data.has_key(u'albumartist') and data.has_key(u'artist'):
			data[u'albumartist'] = data[u'artist']
		Data.__init__(self,data)
	def format(self,format_string):
		v = self.splitter.split(format_string)
		f = [u''.join([ self[ii[:-1]] if ii.endswith(u'%') and len(ii) > 0 and self.has_key(ii[:-1]) else u'[no %s]' % ii[:-1] if ii.endswith(u'%') else ii  for ii in self.__param.split(i)]) for i in v]
		return u'%%'.join(f)
		
class Error(Exception):
	pass



class Client(Object):
	'''
	MPD client. This object can connect, control and manage mpd.

	Attributes:
		config -- connection settings for this client.
		playback -- control(play, pause and etc.) mpd status.
	'''
	def __init__(self,config_path='./'):
		Object.__init__(self)
		self.__config     = Config(config_path)
		self.__connection = Connection(self.config)
		self.__playback   = Playback(self.__connection,self.__config)
		self.__library    = Library(self.__connection,self.__playback,self.__config)
		self.__playlist   = Playlist(self.__connection,self.__playback,self.__config)

	def connect(self,profile=None):
		return self.__connection.connect(profile)

	def start(self):
		self.__playback.start()

	config = property(lambda self:self.__config)
	playback = property(lambda self:self.__playback)
	library = property(lambda self:self.__library)
	playlist = property(lambda self:self.__playlist)
	

class Connection(Object):
	'''
	A connection object manages mpd connection and execute commands.
	To connect to mpd, call the Connection.connect().
	'''

	CONNECT = 'connect'
	CLOSE = 'close'

	def __init__(self,config):
		Object.__init__(self)
		self.__config = config
		self.__current = None
		self.__connection = None
		self.__lock = thread.allocate_lock()
		self.__status = ''
		self.connected = False

	def connect(self,profile=None):
		'''connect to mpd daemon.

		Arguments:
		profile -- string profile name. if none, uses default value.
		'''
		connection = mpd.MPDClient()
		if not profile:
			if not self.__current:
				profile = self.__config.default_profile
			else:
				profile = self.__current	
		try:
	
			mpd.socket.setdefaulttimeout(2)
			connection.connect(profile[1].encode('utf8'),int(profile[2]))
			self.__connection = connection
			self.current = copy.copy(profile)
			self.connected = True
			self.call(self.CONNECT)
		except mpd.MPDError,err:
			self.__status = err
			return False
		except socket.error,err:
			self.__status = err
			return False
		#if connection was established
		return True

	def execute(self,func_name,skip=False,*args,**kwargs):
		'''execute mpd commands.
		
		execute given mpd command. while executing command, can not execute
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
			try:
				if type(func_name) == str or type(func_name) == unicode:
					func_name = str(func_name)
					value = self.__decode(getattr(self.__connection,func_name)(*args,**kwargs))
				elif type(func_name) == list:
					self.__connection.command_list_ok_begin()
					try:
						for index,func_name_part in enumerate(func_name):
							func = self.__decode(getattr(self.__connection,func_name_part))
							func_args = [args_part[index] for args_part in args]
							func_kwargs = dict([(key,values[index]) for key,values in kwargs.iteritems()])
							func(*func_args,**func_kwargs)
					except Exception:
						print traceback.format_exc()
						pass
					self.__connection.command_list_end()
			except mpd.MPDError,err:
				print traceback.format_exc()
			except socket.timeout,err:
				pass
			except socket.error:
				self.connected = False
				self.call(self.CLOSE)
			except AttributeError,err:
				pass
			except Exception,err:
				print traceback.format_exc()
			finally:
				self.__lock.release()
		else:
			return False
		return value

	def __decode(self,item):
		if type(item) == str:
			return item.decode('utf8')
		elif type(item) == dict:
			returns = {}
			for key,value in item.iteritems():
				key = key.decode('utf8')
				if type(value) == str:
					returns[key] = value.decode('utf8')
				elif type(value) == list:
					returns[key] = ';'.join(value).decode('utf8')
				else:
					returns[key] = value
			return Data(returns)
		elif type(item) == list:
			return [self.__decode(info) for info in item]
		else:
			return item
	
class Playback(Object,threading.Thread):
	'''
	Controlls playback interface.

	Event signals:
		UPDATE -- when status has been changed.
		UPDATE_DATABASE -- when database updating job was finished.
		UPDATE_PLAYLIST -- when playlist has been changed.
		UPDATE_PLAYING -- when current playing song was changed.
	'''
	UPDATE = 'updated'
	UPDATE_DATABASE = 'updated_database'
	UPDATE_PLAYLIST = 'updated_playlist'
	UPDATE_PLAYING = 'update_playing'
	def __init__(self,connection,config):
		Object.__init__(self)
		threading.Thread.__init__(self)
		self.daemon = True
		self.connection = connection
		self.config = config
		self.__status = {}
		self.__check_playlist = False
		self.__check_library = False
		self.__playing = None
		self.__running = False

	def run(self):
		""" crawling mpd to check update.
		"""
		while True:
			self.__running = True
			try:
				self.update()
				time.sleep(1)
			except:
				print traceback.format_exc()

	def update(self):
		status = self.connection.execute('status')
		if status and not self.__status == status:
			self.__status = status
			self.call(self.UPDATE,self.__status)
			if not self.__check_playlist == self.__status[u'playlist']:
				self.__check_playlist = self.__status[u'playlist']
				self.call(self.UPDATE_PLAYLIST)
			if not self.__check_library == False and \
				not self.__status.has_key('updating_db'):
				self.call(self.UPDATE_DATABASE)
			elif self.__status.has_key('updating_db'):
				self.__check_library = self.__status['updating_db']
			if self.__status.has_key(u'song') and not self.__playing == self.__status[u'song']:
				self.__playing = self.__status[u'song']
				self.call(self.UPDATE_PLAYING)

	def play(self,song=None):
		if song:
			self.connection.execute('play',True,song[u'pos'])
		else:
			self.connection.execute('play',skip=True)

	def stop(self):
		self.connection.execute('stop',skip=True)

	def pause(self):
		self.connection.execute('pause',skip=True)

	def next(self):
		self.connection.execute('next',skip=True)
	
	def previous(self):
		self.connection.execute('previous',skip=True)

	def __get_status(self):
		if self.__running:
			return self.__status
		else:
			self.update()
			return self.__status
	status = property(lambda self:self.__get_status())

		
class Playlist(Object):
	UPDATE = 'update'
	FOCUS = 'focus'
	SELECT = 'select'

	class Song(Song):
		def __init__(self,song,connection):
			Song.__init__(self,song)
			self.__connection = connection

		def play(self):
			self.__connection.execute(u'play',True,self[u'pos'])
			
	def __init__(self,connection,playback,config):
		Object.__init__(self)
		self.__connection = connection
		self.__playback = playback
		self.__config = config
		self.__data = []
		self.__selected = []
		self.__focused = None
		self.__current = None
		self.__connection.bind(self.__connection.CONNECT,self.__update_cache)
		self.__playback.bind(self.__playback.UPDATE_PLAYLIST,self.__update_cache)
		self.__playback.bind(self.__playback.UPDATE,self.__focus_playling)

	def __iter__(self):
		return list.__iter__(self.__data)

	def __getitem__(self,index):
		return self.__data[index]

	def __delitem__(self,index):
		pos = self.__data[index][u'pos']
		self.__connection.execute('delete',False,pos)
		self.__playback.update()

	def __delslice__(self,start,end):
		pos = [song[u'pos'] for song in self.__data[start:end]]
		delete = ['delete' for song in self.__data[start:end]]
		self.__connection.execute(delete,False,pos)
		self.__playback.update()

	def __getslice__(self,start,end):
		return self.__data[start:end]

	def __len__(self):
		return len(self.__data)

	def __update_cache(self):
		""" update playlist songs cache.
		"""
		data = self.__connection.execute('playlistinfo')
		self.__data = [Playlist.Song(song,self.__connection) for song in data]
		self.focus_playling()
		self.call(self.UPDATE,self.__data)

	def focus_playling(self):
		""" set focus and select value to current playing song.
		"""
		if self.__playback.status and self.__playback.status.has_key(u'song'):
			status = self.__playback.status
			if not status or not status.has_key(u'song'):
				return False
			if not len(self.__data) > int(status[u'song']):
				return False
			song = self.__data[int(status[u'song'])]
			if not song == self.__current:
				self.__current = song
				self.__set_select([song])
				self.__set_focus(song)

	def __focus_playling(self,*args,**kwargs):
		self.focus_playling()

	def __set_select(self,songs):
		self.__selected = [int(song[u'pos']) for song in songs]
		self.call(self.SELECT)

	def __set_focus(self,song):
		self.__focused = int(song[u'pos'])
		self.call(self.FOCUS)




	def append(self,song):
		"""apennd song to end of playlist.
		"""
		add = 'add'
		filepath = song[u'file'].encode('utf8')
		self.__connection.execute(add,True,filepath)
		self.__playback.update()

	def extend(self,songs):
		"""marge the playlist and given songs into the playlist.
		"""
		add = 'add'
		add = [add for song in songs if song.has_key(u'file')]
		filepath = [song[u'file'].encode('utf8') for song in songs if song.has_key(u'file')]
		self.__connection.execute(add,True,filepath)
		self.__playback.update()

	def clear(self):
		"""Clear current playlist.
		"""
		self.__connection.execute('clear',True)
		self.__playback.update()

	current = property(lambda self:copy.copy(self.__data[self.current_index]))
	current_index = property(lambda self:int(self.__playback.status.song))
	selected = property(lambda self:[self.__data[pos] for pos in self.__selected if len(self.__data) > pos],__set_select)
	focused = property(lambda self:self.__data[self.__focused] if not self.__focused == None and len(self.__data) > self.__focused else None,__set_focus)
		



class Library(Object):
	UPDATE = 'update'
	def __init__(self,connection,playback,config):
		Object.__init__(self)
		self.__connection = connection
		self.__playback = playback
		self.__config = config
		self.__data = []
		self.__connection.bind(self.__connection.CONNECT,self.__update_cache)
		self.__playback.bind(self.__playback.UPDATE_DATABASE,self.__update_cache)

	def __iter__(self):
		return list.__iter__(self.__data)

	def __getitem__(self,index):
		return self.__data[index]

	def __getslice__(self,start,end):
		return self.__data[start:end]

	def __len__(self):
		return len(self.__data)

	def update(self):
		self.__connection.execute('update')

	def __update_cache(self):
		""" update library songs cache.
		"""
		self.__data = self.__connection.execute('listallinfo')
		# remove invalid songs.
		self.__data = [Song(data) for data in self.__data if data.has_key(u'file')]
		self.call(self.UPDATE,self.__data)


class Songs(list):
	def __init__(self,song_list):
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
	def __init__(self,path='./'):
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
				f = codecs.open(self.path+'config.json','r','utf8')
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
			f = codecs.open(self.path + 'config.json','w','utf8')
			f.write(dumps)
			f.close()
		except ValueError:
			pass

	def __get_profiles(self):
		if not self.__config.has_key(u'profiles'):
			self.__config[u'profiles'] = [[u'default',u'localhost',u'6600',False,u'']]
		return copy.copy(self.__config[u'profiles'])

	def __set_profiles(self,profiles):
		if not type(profiles) == list:
			cause ='given:'+unicode(type(profiles))+' require:'+unicode(list)
			raise TypeError(cause)
		else:
			for profile in profiles:
				if not [type(item) for item in profile] == [unicode,unicode,unicode,bool,unicode]:
					cause = 'given:'+unicode([type(item) for item in profile])+' require:'+unicode([unicode,unicode,unicode,bool,unicode])
					raise TypeError(cause)
			if len(profiles) == 0:
				raise IndexError(0)
		self.__config[u'profiles'] = profiles
		self.save()
		self.call(self.CONFIG_CHANGED)

	profiles = property(__get_profiles,__set_profiles)

	def __get_default_profile(self):
		if not self.__config.has_key(u'default_profile'):
			for name,_,_,_,_ in self.__get_profiles():
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

