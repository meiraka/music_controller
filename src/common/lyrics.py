#!/usr/bin/python

"""
Draw lyric 
"""

import sqlite3
import time
import urllib
import urllib2
import json
import thread
import re

import client
import environment

class Downloader(object):
	def list(self,**kwargs):
		""" Returns list for format() or get() arg.

		Normally returns lyric url.
		"""
		pass

	def format(self,list_returns_line):
		""" Convert given arg to readable string.
		"""
		return unicode(list_returns_line)

	def get(self,list_returns_line):
		""" Returns lyric from url in given arg data.
		"""
		pass

	def download(self,song):
		""" Returns lyric by given song data.
		"""
		items = self.list(title=song.format('%title%'),
				artist=song.format('%artist%'),
				album = song.format('%album%'))
		if items:
			time.sleep(1)
			return self.get(items[0])


class DownloaderGeciMe(Downloader):
	def list(self,**kwargs):
		if not 'title' in kwargs:
			return []
		query_text = kwargs['title'].replace(u'/',u'*').encode('utf8')
		if 'artist' in kwargs:
			artist = kwargs['artist'].replace(u'/',u'*').encode('utf8')
			query_text = query_text + '/' + artist
		query = urllib.quote(query_text)
		try:
			json_text = urllib2.urlopen('http://geci.me/api/lyric/'+query).read()
		except urllib2.URLError,err:
			print 'can not access:','http://geci.me/api/lyric/'+query,err
			return []
		json_parsed = json.loads(json_text.decode('utf8'))
		if u'result' in json_parsed:
			return json_parsed[u'result']
		else:
			return []

	def get(self,list_returns_line):
		try:
			lyric_page = urllib2.urlopen(list_returns_line[u'lrc'])
		except urllib2.URLError,err:
			print 'can not access:',list_returns_line[u'lrc'],err
			return u''
		lyric_encode = lyric_page.info()
		lyric = lyric_page.read().decode('utf8')
		return lyric



class Database(client.Object):
	"""
	Downloads and manages lyric.
	"""
	UPDATING = 'updating'
	UPDATE = 'update'
	def __init__(self):
		""" init values and database."""
		self.__downloading = []
		self.download_auto = False
		self.download_background = False
		self.downloaders = dict(
			geci_me = True
			)

		""" init database.

		if not exists database, create table.
		"""
		sql_init = '''
		CREATE TABLE IF NOT EXISTS lyrics
		(
			artist TEXT,
			title TEXT,
			album TEXT,
			lyric TEXT,
			UNIQUE(artist,title,album)
		);
		'''
		client.Object.__init__(self)
		connection = self.__get_connection()
		connection.execute(sql_init)

	def clear_empty_lyrics(self):
		""" Clears no lyrics data raw(fail to download or no lyrics found raw).
		"""
		sql_clear = 'delete from lyrics where lyric="None";'
		connection = self.__get_connection()
		connection.execute(sql_clear)
		connection.commit()
		
	def __get_connection(self):
		""" Returns database instance.

		must generate instance at everytime cause
		sqlite3 is not thread-safe.
		"""
		db = sqlite3.connect(environment.config_dir+'/lyrics')
		return db
		
	def __getitem__(self,song):
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
		connection = self.__get_connection()
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
					thread.start_new_thread(self.download,(song,))
				else:
					return self.download(song)
			return u''
		else:
			return lyric[0]

	def __setitem__(self,song,lyric):
		""" Saves lyric.

		Arguments:
			song - song object.
			lyric - string lyric.
		"""
		lyric = unicode(lyric)
		sql_write = '''
		INSERT OR REPLACE INTO lyrics
		(artist,title,album,lyric)
		VALUES(?, ?, ?, ?)
		'''
		connection = self.__get_connection()
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
		self.call(self.UPDATE,song,lyric)
		
	def download(self,song):
		self.__downloading.append(song)
		self.call(self.UPDATING)
		lyric = u''
		for label,is_download in self.downloaders.iteritems():
			if is_download:
				downloader = getattr(self,'download_from_'+label)
				lyric = downloader(song)
				if lyric:
					break
			else:
				pass
		del self.__downloading[self.__downloading.index(song)]
		self.__setitem__(song,lyric)
		return lyric

	def download_from_geci_me(self,song):
		downloader = DownloaderGeciMe()
		return downloader.download(song)

	downloading = property(lambda self:self.__downloading)


