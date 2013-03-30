#!/usr/bin/python

"""
Artwork reader and writer.

Supports read, write, search and download artwork.
"""

import os
import sqlite3
import thread

from base import Object
import rest
import environment

class Database(Object):
	"""
	Downloads and manages Artwork.
	"""
	UPDATING = 'updating'
	UPDATE = 'update'
	def __init__(self,client):
		""" init values and database."""
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

		if not exists database, create table.
		"""
		sql_init = '''
		CREATE TABLE IF NOT EXISTS artwork
		(
			artist TEXT,
			album TEXT,
			artwork TEXT,
			UNIQUE(artist,album)
		);
		'''
		Object.__init__(self)
		connection = self.__get_connection()
		connection.execute(sql_init)

	def __get_connection(self):
		""" Returns database instance.

		must generate instance at everytime cause
		sqlite3 is not thread-safe.
		"""
		db = sqlite3.connect(environment.config_dir+'/artworkdb')
		return db

	def __getitem__(self,song):
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
		sql_search = '''
		SELECT artwork FROM artwork WHERE
			artist=? and
			album=?
		'''
		connection = self.__get_connection()
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
					thread.start_new_thread(self.download,(song,))
				else:
					return self.download(song)
			return u''
		elif artwork[0]:
			return self.__download_path + '/' + artwork[0]
		else:
			# download is blocked
			# or already downloaded but not found any data.
			return u''

	def __setitem__(self,song,artwork_binary):
		""" Saves artwork binary.

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
			f = open(fullpath,'w')
			f.write(artwork_binary)
			f.close()
		else:
			fullpath = u''
			filename = u''

		# save filepath to database.
		sql_write = '''
		INSERT OR REPLACE INTO artwork
		(artist,album,artwork)
		VALUES(?, ?, ?)
		'''
		connection = self.__get_connection()
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
			self.call(self.UPDATE,song,fullpath)

	def clear_empty(self):
		sql_clear = 'delete from artwork where artwork="";'
		connection = self.__get_connection()
		cursor = connection.cursor()
		cursor.execute(sql_clear)
		connection.commit()
		
		
	def download(self,song):
		if not song in self.__downloading:
			self.__downloading.append(song)
			self.__setitem__(song,u'')  # flush for terrible lock.
			self.call(self.UPDATING)
			artwork_binary = u''
			for label,is_download in self.downloaders.iteritems():
				if is_download:
					downloader = self.download_class[label]()
					artwork_binary = downloader.download(song)
					if artwork_binary:
						break
				else:
					pass
			del self.__downloading[self.__downloading.index(song)]
			self.__setitem__(song,artwork_binary)
			return self.__getitem__(song)
		else:
			return ''

	def list(self,keywords,callback=None):
		""" Returns candidate artworks of given song.

		Arguments:
			keywords -- keyword dict like dict(artist=foo,title=bar)
			callback -- if not None, callback(*each_list_item)

		Returns list like:
			[
				( downloadfunc,urlinfo formatter func, urlinfo list),
				...,
			]

		to get artwork list[0][0]:
			returnslist = db.list(keywords)
			func,formatter,urlinfo_list = returnslist[0]
			artwork_binary = func(urlinfo_list[0])
			db[song] = artwork_binary
			

		to show readable candidate artworks:
			returnslist = db.list(keywords)
			for func,formatter,urlinfo_list in returnslist:
				for urlinfo in urlinfo_list:
					print formatter(urlinfo)
		"""

		lists = []
		for label,is_download in self.downloaders.iteritems():
			if is_download:
				downloader = self.download_class[label]()
				urls = downloader.list(**keywords)
				appends = (downloader.get,downloader.format,urls)
				lists.append(appends)
				if callback:
					callback(*appends)
			else:
				pass
		return lists

	downloading = property(lambda self:self.__downloading)



