#!/usr/bin/python

import os
import thread
import wx
import environment
import math
import lastfm

class ArtworkFinder(object):
	def __init__(self):
		self.__check_dir = environment.config_dir + u'/artwork'
		self.lastfm = lastfm.Album()
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

	def get_image_from_lastfm(self,song):
		return self.lastfm[song]



class Artwork(ArtworkFinder):
	class Mirror(ArtworkFinder):
		def __init__(self,parent,enable=False):
			self.parent = parent
			ArtworkFinder.__init__(self)
			self.__images = {}
			self.__empty_image = None
			self.__enable = enable
			if not enable:
				self.__empty_image = self.parent.empty
			self.size = (120,120)
			self.length = 0.3
		def __getitem__(self,song):
			if not self.__enable:
				return self.__empty()
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
				image = wx.ImageFromBitmap(self.parent.empty)
				image = image.Mirror()
				image = image.Rotate90()
				image = image.Rotate90()
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
			
	def __init__(self,mirror=False):
		ArtworkFinder.__init__(self)
		self.__files = []
		self.__images = {}
		self.resize = True
		self.__empty = None
		self.__callbacks = []
		self.__size = (120,120)
		self.mirror = Artwork.Mirror(self,mirror)
		self.__lastfm = mirror
		self.lastfm.bind(self.lastfm.DOWNLOADED,self.__load_image)


	def attach(self,func):
		""" attach function to listen artwork loader event.
		if image was loaded, call function.
		"""
		self.__callbacks.append(func)

	def detach(self,func):
		del self.__callbacks[self.__callbacks.index(func)]

	def __getitem__(self,song):
		path = self.get_image_from_lastfm(song)
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
			if w is 0 or h is 0:
				return
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
			self.__empty = wx.EmptyBitmap(*self.__size)
			writer = wx.MemoryDC(self.__empty)
			bg,fg = environment.userinterface.colors
			writer.SetBrush(wx.Brush(bg))
			writer.SetPen(wx.Pen(bg))
			writer.DrawRectangle(0,0,*self.__size)
			writer.SetBrush(wx.Brush(fg))
			width = environment.userinterface.text_height/2
			space = int(math.sqrt(width*width*2))
			writer.SetPen(wx.Pen(fg,width=width))
			for x in xrange(self.__size[0]/space+1):
				if x%2:
					writer.DrawLine(x*space,0,x*space+self.__size[0],self.__size[1])
					writer.DrawLine(0,x*space,self.__size[0],x*space+self.__size[1])
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
			self.__empty = None
			self.__get_empty_image()
		else:
			return self.__size
	size = property(__change_size,__change_size)
	empty = property(__get_empty_image)

