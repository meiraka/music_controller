#!/usr/bin/python

import thread

import wx

import artwork

class Info(wx.Panel):
	def __init__(self,parent,client,debug=False):
		wx.Panel.__init__(self,parent,-1)
		self.client = client
		self.__currentsong = 0
		self.__lock = False
		self.__image_path = u''
		self.artwork = wx.StaticBitmap(self,-1)
		self.title = wx.StaticText(self,-1)
		self.artist = wx.StaticText(self,-1)
		self.album = wx.StaticText(self,-1)
		self.artwork_loader = artwork.Artwork()
		self.sizer = wx.GridBagSizer()
		self.sizer.Add(self.artwork,(0,0),(3,1),border=6)
		self.sizer.Add(self.title,(0,2),flag=wx.ALL,border=6)
		self.sizer.Add(self.artist,(1,2),flag=wx.ALL,border=6)
		self.sizer.Add(self.album,(2,2),flag=wx.ALL,border=6)
		self.SetSizer(self.sizer)
		self.client.playback.bind(self.client.playback.UPDATED,self.update)
		self.Bind(wx.EVT_SIZE,self.resize_image)

	def update(self,*args,**kwargs):
		wx.CallAfter(self.__update,self.client.playback.status)

	def resize_image(self,*args,**kwargs):
		self.__resize_image()

	def __update(self,status):
		if not self.__currentsong == status[u'song']:
			self.__currentsong = status[u'song']
			song = self.client.playlist[int(self.__currentsong)]
			self.title.SetLabel(song[u'title'])
			self.artist.SetLabel(song[u'artist'])
			self.album.SetLabel(song[u'album'])
			self.__image_path = self.artwork_loader[song]
			self.__update_image()
			self.Layout()
	
	def __update_image(self):
		if self.__image_path and not self.__lock:
			self.__lock = True
			w,h = self.GetSize()
			image = wx.Image(self.__image_path)
			iw,ih = image.GetSize()
			image.Rescale(iw/ih*h,h,quality=wx.IMAGE_QUALITY_HIGH)
			self.artwork.SetBitmap(image.ConvertToBitmap())
			self.__lock = False
			self.Layout()
			

	def __resize_image(self):
		thread.start_new_thread(wx.CallAfter,(self.__update_image,))
		
