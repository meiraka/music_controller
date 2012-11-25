#!/usr/bin/python

import os
import environment

class Artwork(object):
	def __init__(self):
		self.__check_dir = environment.config_dir + u'/artwork'
		self.__files = []
		self.cache()

	def cache(self):
		""" check art work dir and caching."""
		if not os.path.exists(self.__check_dir):
			os.makedirs(self.__check_dir)
		self.__files = os.listdir(self.__check_dir)

	def has_song(self,song):
		""" returns True if given song's artwork was found."""
		pass

	def __getitem__(self,song):
		for file in self.__files:
			if file.count(song[u'album']):
				return self.__check_dir + u'/' + file
		return u''
			
