#!/usr/bin/python

"""
load Artwork and generates wx.Bitmap objects.
"""

import sqlite3
import os
import thread
import wx
import math
from common import environment
from common import artwork
from common import Object

class ArtworkFinder(Object):
	""" Wrapper for common.artwork.Database.

	This class will be removed.
	"""
	DOWNLOADED = 'downloaded'
	def __init__(self):
		Object.__init__(self)
		self.__db = artwork.Database()
		self.__db.download_auto = True
		self.__db.download_background = True
		self.__db.bind(self.__db.UPDATE,self.__downloaded)

	def __getitem__(self,song):
		return self.__db[song]

	def __downloaded(self,song,path):
		""" event function for lastfm.Album.DOWNLOADED. """
		self.call(self.DOWNLOADED,path,song)



class Database(ArtworkFinder):
	"""
	Artwork database.

	to get song artwork and artwork mirror:

	::

		img = db[song]
		mirror_img  = db.mirror[song]

	Events:
		UPDATE -- database is updated. raises with no arguments.
	"""
	UPDATE = 'update'
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
			""" Returns mirrored artwork image.
			"""
			if not self.__enable:
				return self.__get_empty_image()
			path = ArtworkFinder.__getitem__(self,song)
			if not path:
				return self.__get_empty_image()
			if self.__images.has_key((path,self.size)):
				return self.__images[(path,self.size)]
			else:
				return self.__get_empty_image()

		def load(self,path,image):
			""" converts image to mirror image and 
			stores image as given path of image.
			"""
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

			def __cache_image(path,image):
				bmp = wx.BitmapFromImage(image)
				self.__images[(path,self.size)] = bmp
			wx.CallAfter(__cache_image,path,mirror)


		def __get_empty_image(self):
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

		empty = property(__get_empty_image)
			
	def __init__(self,mirror=False):
		""" Inits database interface.

		Arguments:
			mirror -- if True, generates mirrored image.

		"""
		ArtworkFinder.__init__(self)
		self.__files = []
		self.__images = {}
		self.__empty = None
		self.__callbacks = []
		self.__size = (120,120)
		self.mirror = Database.Mirror(self,mirror)
		self.bind(self.DOWNLOADED,self.__load_image)


	def __getitem__(self,song):
		path = ArtworkFinder.__getitem__(self,song)
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
		""" Generates given path of image object.
		
		
		"""
		self.__images[(path,self.size)] = None
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
		""" Returns image for "Not found".

		if empty image was not generated, generates and
		returns image.
		"""
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
		""" converts image to bitmap and stores __cache

		Raises UPDATE event.
		"""
		bmp = wx.BitmapFromImage(image)
		self.__images[(path,self.size)] = bmp
		self.call(self.UPDATE)

	
	
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

