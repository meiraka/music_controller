#!/usr/bin/python

import os
import thread
import wx
import environment

class ArtworkFinder(object):
	def __init__(self):
		self.__check_dir = environment.config_dir + u'/artwork'
		self.cache()

	def cache(self):
		""" check art work dir and caching."""
		if not os.path.exists(self.__check_dir):
			os.makedirs(self.__check_dir)
		self.__files = os.listdir(self.__check_dir)

	def get_image_path(self,song):
		if not(song and song.has_key(u'album')):
			return None
		for file in self.__files:
			if file.count(song[u'album']):
				return self.__check_dir + u'/' + file
		else:
			return None



class Artwork(ArtworkFinder):
	class Mirror(ArtworkFinder):
		def __init__(self):
			ArtworkFinder.__init__(self)
			self.__images = {}
			self.__empty_image = None
			self.size = (120,120)
			self.length = 0.3
		def __getitem__(self,song):
			path = self.get_image_path(song)
			if not path:
				return self.__empty()
			if self.__images.has_key((path,self.size)):
				return self.__images[(path,self.size)]
			else:
				return self.__empty()

		def load(self,path,image):
			mirror = image.Mirror()
			h = int(mirror.GetHeight()*self.length)
			mirror = mirror.Rotate90()
			mirror = mirror.Rotate90()
			mirror = mirror.Size((mirror.GetWidth(),h),(0,0))
			if not mirror.HasAlpha():
				mirror.InitAlpha()
			w,h = mirror.GetSize()
			for x in xrange(w):
				for y in xrange(h):
					if y:
						p = int(y*1.0/h * 200)
						mirror.SetAlpha(x,y,200-p if 200-p>0 else 0)
			wx.CallAfter(self.__cache_image,path,mirror)

		def __cache_image(self,path,image):
			bmp = wx.BitmapFromImage(image)
			self.__images[(path,self.size)] = bmp



		def __empty(self):
			if not self.__empty_image:
				image = wx.EmptyImage(*self.size)
				h = int(image.GetHeight()*self.length)
				image = image.Size((image.GetWidth(),h),(0,0))
				w,h = image.GetSize()
				if not image.HasAlpha():
					image.InitAlpha()
				for x in xrange(w):
					for y in xrange(h):
						if y:
							p = int(y*1.0/h * 200)
							image.SetAlpha(x,y,200-p if 200-p>0 else 0)
				self.__empty_image = wx.BitmapFromImage(image)
			return self.__empty_image
			
	def __init__(self):
		ArtworkFinder.__init__(self)
		self.__files = []
		self.__images = {}
		self.resize = True
		self.__callbacks = []
		self.__size = (120,120)
		self.mirror = Artwork.Mirror()

	def attach(self,func):
		""" attach function to listen artwork loader event.
		if image was loaded, call function.
		"""
		self.__callbacks.append(func)

	def detach(self,func):
		del self.__callbacks[self.__callbacks.index(func)]

	def __getitem__(self,song):
		path = self.get_image_path(song)
		if not path:
			return self.__get_empty_image()
		if self.__images.has_key((path,self.size)) and self.__images[(path,self.size)]:
			return self.__images[(path,self.size)]
		elif self.__images.has_key((path,self.size)):
			return self.__get_empty_image()
		else:
			thread.start_new_thread(self.__load_image,(path,song))
			return None

	def __load_image(self,path,song):
		self.__images[(path,self.size)] = None
		if self.resize:
			image = wx.Image(path)
			w,h = image.GetSize()
			if w > h:
				new_size = (self.size[0],int(1.0*h/w*self.size[1]))
			else:
				new_size = (int(1.0*w/h*self.size[0]),self.size[1])
			if all([i > 0 for i in new_size]):
				image.Rescale(*new_size,quality=wx.IMAGE_QUALITY_HIGH)
			self.mirror.load(path,image)
			wx.CallAfter(self.__cache_image,path,image)

	def __get_empty_image(self):
		if not self.__empty:
			self.__empty = wx.EmptyBitmap(*size)
		return self.__empty

	def __cache_image(self,path,image):
		bmp = wx.BitmapFromImage(image)
		self.__images[(path,self.size)] = bmp
		for func in self.__callbacks:
			func()

	
	
	def __change_size(self,size=None):
		if size:
			self.__size = size
			self.mirror.size = size
			self.__empty = wx.EmptyBitmap(*size)
		else:
			return self.__size
	size = property(__change_size,__change_size)


