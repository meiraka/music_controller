#!/usr/bin/python

"""
Rest API wrapper.
"""

import time
import urllib
import urllib2
import json

class Downloader(object):
	"""
	Base class for rest api.
	"""
	def list(self,**kwargs):
		""" Returns list for format() or get() arg.

		Normally returns data url.
		"""
		pass

	def format(self,list_returns_line):
		""" Convert given arg to readable string.
		"""
		return unicode(list_returns_line)

	def get(self,list_returns_line):
		""" Returns data from url in given arg data.
		"""
		pass

	def download(self,song):
		""" Returns data by given song data.
		"""
		items = self.list(title=song.format('%title%'),
				artist=song.format('%artist%'),
				albumartist=song.format('%albumartist%'),
				album = song.format('%album%'))
		if items:
			time.sleep(1)
			return self.get(items[0])

	def download_errmsg(self,url,err):
		print 'cam not access: ',msg,err


class GeciMe(Downloader):
	"""
	Download lyrics from geci.me
	"""
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



class ArtworkLastfm(Downloader):
	"""
	Download artwork from lastfm.
	"""
	KEY = u'1f898a6986e69cd5a456d18e56051e0c'
	SECRET = u'4c77ec44c856dc04bbc5b69a6068a8d9'
	def list(self,**kwargs):
		artist = kwargs['albumartist']
		album = kwargs['album']
		req = 'http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=%(key)s&artist=%(artist)s&album=%(album)s&format=json'
		req = req % dict(key=self.KEY,
				artist=urllib.quote(artist.encode('utf8')),
				album=urllib.quote(album.encode('utf8')))
		try:
			json_text = urllib.urlopen(req).read().decode('utf8')
		except urllib2.URLError,err:
			self.download_errmsg(req,err)
		json_parsed = json.loads(json_text)
		if 'album' in json_parsed and 'image' in json_parsed['album']:
			url_list = [i for i in json_parsed['album']['image'] if '#text' in i]
			url_list.reverse()
			return url_list
		else:
			return []

	def get(self,list_returns_line):
		""" Returns image binary text. not image path.
		"""
		url = list_returns_line['#text']
		if url:
			try:
				image_bin = urllib2.urlopen(url).read()
				return image_bin
			except urllib2.URLError,err:
				self.download_errmsg(url,err)
		return ''
