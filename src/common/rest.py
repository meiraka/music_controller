#!/usr/bin/python

"""
Rest API wrapper.
"""

import time
import urllib
import urllib2
import json

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


class GeciMe(Downloader):
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



