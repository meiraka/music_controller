#!/usr/bin/python

import urllib
import sqlite3
import thread
import json
import socket

import client
import environment

KEY = u'1f898a6986e69cd5a456d18e56051e0c'
SECRET = u'4c77ec44c856dc04bbc5b69a6068a8d9'

class Artwork(client.Object):
	"""
	Download and cache image from Last.fm

	"""
	DOWNLOADED = 'downloaded'
	def __init__(self):
		client.Object.__init__(self)
		self.__cache = {} # song.format('%albumartist% %album%') = fullpath
		self.download_auto = False
		self.download_background = False
		sql_init = '''
		CREATE TABLE IF NOT EXISTS
		albums
		(
			artist TEXT ,
			album TEXT ,
			artwork TEXT
		);
		'''
		connection = self.__get_connection()
		connection.execute(sql_init)
		
	def __get_connection(self):
		db = sqlite3.connect(environment.config_dir+'/lastfm')
		return db
		
	def __getitem__(self,song):
		sql_search = '''
		SELECT artwork FROM albums WHERE
			artist=? and
			album=?
		'''

		# check cache.
		if not song:
			return None
		key = song.format('%albumartist% %album%')
		if key in self.__cache:
			return self.__cache[key]


		# if not cached.
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
			# not in db, download
			# write cache empty value
			self.__cache[key] = ''
			if self.download_auto:
				if self.download_background:
					thread.start_new_thread(self.download,(song,))
				else:
					self.download(song)
			return self.__cache[key]
		elif artwork[0]:
			# found image in db
			# write cache path
			self.__cache[key] = environment.config_dir+'/artwork/'+artwork[0]
			return self.__cache[key]
		else:
			# not found, but downloaded
			return None

	def download(self,song):
		""" download image and write db andcache path.

		if timeout, delete from db and cache.
		"""

		try:
			self.__download(song)
		except socket.error:
			sql_delete = '''
			DELETE FROM albums WHERE
			artist=? and
			album=?
			'''
			artist = song.format('%albumartist%')
			album = song.format('%album%')
			connection = self.__get_connection()
			cursor = connection.cursor()
			cursor.execute(sql_delete,(artist,album))
			connection.commit()
			key = song.format('%albumartist% %album%')
			del self.__cache[key]
			return ''


	def __download(self,song):
		""" part of download()

		Donwload and write db, cache path.
		Returns:
			fullpath of image if downloaded else None
		"""
		sql_write = '''
		INSERT OR REPLACE INTO albums
		(artist,album,artwork)
		VALUES(?,?,?)
		'''
		sql_update = '''
		UPDATE albums SET
		artwork=?
		WHERE
		artist=? and
		album=?
		'''
		artist = song.format('%albumartist%')
		album = song.format('%album%')
		key = song.format('%albumartist% %album%')
		# fill with '' to block another instance start download.
		connection = self.__get_connection()
		cursor = connection.cursor()
		cursor.execute(sql_write,(artist,album,''))
		connection.commit()

		# download from lastfm.
		reqest = 'http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=%(key)s&artist=%(artist)s&album=%(album)s&format=json'
		reqest = reqest % dict(key=KEY,
			artist=urllib.quote(artist.encode('utf8')),
			album=urllib.quote(album.encode('utf8')))
		json_text = urllib.urlopen(reqest).read().decode('utf8')
		json_parsed = json.loads(json_text)
		path = ''
		filename = ''
		if 'album' in json_parsed and 'image' in json_parsed['album']:
			for image in json_parsed['album']['image']:
				if '#text' in image:
					path = image['#text']
		if path:
			image_bin = urllib.urlopen(path).read()
			filename = key.replace('/','_')
			fullpath = environment.config_dir+'/artwork/'+filename
			f = open(fullpath,'w')
			f.write(image_bin)
			f.close()
			cursor.execute(sql_update,(filename,artist,album))
			connection.commit()
			self.__cache[key] = fullpath
			self.call(self.DOWNLOADED,fullpath,song)
			return fullpath
		return None
