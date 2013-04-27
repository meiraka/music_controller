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
from common import Object

import dialog

class Loader(Object):
	"""
	Artwork image loader.

	to get image and mirror:

	::

		img = db[song.artwork]
		mirror_img  = db.mirror[song.artwork]

	Events:
		UPDATE -- database is updated. raises with no arguments.
	"""
	UPDATE = 'update'
	class Mirror(Object):
		def __init__(self,parent,enable=False):
			Object.__init__(self)
			self.parent = parent
			self.__images = {}
			self.__empty_image = None
			self.__enable = enable
			if not enable:
				self.__empty_image = self.parent.empty
			self.size = (120,120)
			self.length = 0.3

		def __getitem__(self,path):
			""" Returns mirrored artwork image.
			"""
			if not self.__enable:
				return self.__get_empty_image()
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
			
	def __init__(self,client,mirror=False):
		""" Inits database interface.

		Arguments:
			client -- mpd client object.
			mirror -- if True, generates mirrored image.

		"""
		Object.__init__(self)
		self.__files = []
		self.__images = {}
		self.__empty = None
		self.__callbacks = []
		self.__size = (120,120)
		self.mirror = Loader.Mirror(self,mirror)
		self.artwork = client.artwork
		self.artwork.bind(self.artwork.UPDATE,self.__load_image)


	def __getitem__(self,path):
		if not path:
			return self.__get_empty_image()
		if self.__images.has_key((path,self.size)) and self.__images[(path,self.size)]:
			return self.__images[(path,self.size)]
		elif self.__images.has_key((path,self.size)):
			return self.__get_empty_image()
		else:
			thread.start_new_thread(self.__load_image,('',path))
			return None

	def __load_image(self,song,path):
		""" Generates given path of image object.
		
		
		"""
		self.__images[(path,self.size)] = None
		image = wx.Image(path)
		if not image.IsOk():
			return
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

class Downloader(dialog.Frame):
	"""
	Artwork Download dialog.
	"""
	def __init__(self,parent,client,song):
		self.parent = parent
		self.client = client
		self.database = self.client.artwork
		self.song = song
		self.items = []
		dialog.Frame.__init__(self,parent,style=dialog.MIN_STYLE|wx.RESIZE_BORDER)
		self.SetTitle(_('Download Artwork: %s') % song.format('%albumartist% - %album%'))
		sizer = wx.GridBagSizer()
		sizer_flag = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL,border=3)
		sizer_flag_right = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT,border=3)
		expand_sizer_flag = dict(flag=wx.ALL|wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL,border=3)
		labels = ['albumartist','album']
		self.values = {}
		index = 0
		base = self
		if environment.userinterface.fill_window_background:
			base = wx.Panel(self,-1)
		for index,label in enumerate(labels):
			sizer.Add(wx.StaticText(base,-1,_(label)+u':'),(index,0),**sizer_flag_right)
			value = wx.TextCtrl(base,-1,getattr(self.song,label))
			self.values[label] = value
			sizer.Add(value,(index,1),(1,2),**expand_sizer_flag)
		self.listview = wx.ListBox(base,-1)
		index = index + 1
		sizer.Add(self.listview,(index,0),(1,3),flag=wx.EXPAND)
		sizer.AddGrowableRow(index)
		sizer.AddGrowableCol(1)
		index = index + 1
		self.status_label = wx.StaticText(base,-1)
		self.search_button = wx.Button(base,-1,_('Search'))
		sizer.Add(self.status_label,(index,0),**sizer_flag)
		sizer.Add(self.search_button,(index,2),**sizer_flag)
		base.SetSizer(sizer)

		self.search_button.Bind(wx.EVT_BUTTON,self.on_search_button)
		self.listview.Bind(wx.EVT_LISTBOX_DCLICK,self.on_activate_item)
		if environment.userinterface.fill_window_background:
			sizer = wx.BoxSizer()
			sizer.Add(base,1,wx.EXPAND)
			self.SetSizer(sizer)

	def on_search_button(self,event):
		self.listview.Clear()
		keywords = dict((label,value.GetValue()) for label,value in self.values.iteritems())
		def download():
			wx.CallAfter(self.status_label.SetLabel,_('Searching'))
			def download_callback(get,format,list):
				for i in list:
					wx.CallAfter(self.listview.Append,format(i))
					self.items.append((get,i))
				wx.CallAfter(self.Layout)
			self.database.list(keywords,callback=download_callback)
			if self.items:
				wx.CallAfter(self.status_label.SetLabel,_('%i Items Found' % len(self.items)))
			else:
				wx.CallAfter(self.status_label.SetLabel,_('No Items Found'))
		thread.start_new_thread(download,())

	def on_activate_item(self,event):
		index = event.GetSelection()
		get,urlinfo = self.items[index]
		def download():
			wx.CallAfter(self.status_label.SetLabel,_('Downloading'))
			artwork_binary = get(urlinfo)
			self.database[self.song] = artwork_binary
			wx.CallAfter(self.status_label.SetLabel,_(''))
		thread.start_new_thread(download,())
