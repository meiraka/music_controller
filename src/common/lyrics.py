#!/usr/bin/python

"""
Lyrics reader and writer.

Supports read, write, search and download lyrics.
"""

import sqlite3
import time
import urllib
import urllib2
import json
import thread
import re

import client
import rest
import environment


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

		self.download_class = dict(
			geci_me = rest.GeciMe
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
				downloader = self.download_class[label]()
				lyric = downloader.download(song)
				if lyric:
					break
			else:
				pass
		del self.__downloading[self.__downloading.index(song)]
		self.__setitem__(song,lyric)
		return lyric

	def list(self,keywords,callback=None):
		""" Returns candidate lyrics of given song.

		Arguments:
			keywords -- keyword dict like dict(artist=foo,title=bar)
			callback -- if not None, callback(*each_list_item)

		Returns list like:
			[
				( downloadfunc,urlinfo formatter func, urlinfo list),
				...,
			]

		to get lyric list[0][0]:
			returnslist = db.list(keywords)
			func,formatter,urlinfo_list = returnslist[0]
			lyric = func(urlinfo_list[0])
			db[song] = lyric
			

		to show readable candidate lyric:
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


