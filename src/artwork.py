#!/usr/bin/python

import os
import thread
import wx
import environment

class Artwork(object):
	def __init__(self):
		self.__check_dir = environment.config_dir + u'/artwork'
		self.__files = []
		self.__images = {}
		self.cache()
		self.resize = True
		self.__callbacks = []
		self.size = (120,120)

	def attach(self,func):
		self.__callbacks.append(func)

	def detach(self,func):
		del self.__callbacks[self.__callbacks.index(func)]

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
				path = self.__check_dir + u'/' + file
				if self.__images.has_key((path,self.size)):
					return self.__images[(path,self.size)]
				else:
					thread.start_new_thread(self.__load_image,(path,))
					return None
				break
		else:
			return None

	def __load_image(self,path):
		image = wx.Image(path)
		w,h = image.GetSize()
		if self.resize:
			if w > h:
				new_size = (self.size[0],int(1.0*h/w*self.size[1]))
			else:
				new_size = (int(1.0*w/h*self.size[0]),self.size[1])
			if all([i > 0 for i in new_size]):
				image.Rescale(*new_size,quality=wx.IMAGE_QUALITY_HIGH)
			wx.CallAfter(self.__cache_image,path,image)

	def __cache_image(self,path,image):
		bmp = wx.BitmapFromImage(image)
		self.__images[(path,self.size)] = bmp
		for func in self.__callbacks:
			func()
			
