#!/usr/bin/python

import thread

import wx

import artwork
import environment

class Info(wx.Panel):
	def __init__(self,parent,client,debug=False):
		wx.Panel.__init__(self,parent,-1)
		self.client = client
		self.__currentsong = 0
		self.__lock = False
		self.__image = None
		self.artwork = wx.StaticBitmap(self,-1)
		self.artwork_mirror = wx.StaticBitmap(self,-1)
		self.title = wx.StaticText(self,-1)
		self.artist = wx.StaticText(self,-1)
		self.album = wx.StaticText(self,-1,style=wx.ALIGN_LEFT)
		self.genre = wx.StaticText(self,-1,style=wx.ALIGN_LEFT)
		self.artwork_loader = artwork.Artwork()
		h = environment.ui.text_height
		self.artwork_loader.size = (h*12,h*12)
		self.SetMinSize((h*16,h*16))
		self.artwork_loader.attach(self.update)
		sizer = wx.GridBagSizer()
		params = dict(flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTRE|wx.ALL,border=3)
		params_image = dict(flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTRE)
		params_r = dict(flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALIGN_LEFT|wx.ALL,border=3)
		params_l = dict(flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALIGN_RIGHT|wx.ALL,border=3)

		sizer.Add(self.artwork,(0,0),(1,2),**params_image)
		sizer.Add(self.artwork_mirror,(1,0),(1,2),**params_image)
		sizer.Add(self.title,(2,0),(1,2),**params)
		sizer.Add(self.artist,(3,0),(1,2),**params)
		sizer.Add(wx.StaticText(self,-1,u'album:',style=wx.ALIGN_RIGHT),(5,0),**params_l)
		sizer.Add(self.album,(5,1),**params_r)
		sizer.Add(wx.StaticText(self,-1,u'genre:',style=wx.ALIGN_RIGHT),(6,0),**params_l)
		sizer.Add(self.genre,(6,1),**params_r)
		#sizer.AddGrowableCol(0)
		#sizer.AddGrowableCol(1)
		outer = wx.BoxSizer(wx.VERTICAL)
		outer.Add(sizer,0,wx.ALL,border=h*2-3)
		self.SetSizer(outer)
		self.client.playback.bind(self.client.playback.UPDATE,self.update)

	def update(self,*args,**kwargs):
		wx.CallAfter(self.__update,self.client.playback.status)

	def resize_image(self,*args,**kwargs):
		self.__resize_image()

	def __update(self,status):
		if not status or not status.has_key(u'song'):
			return
		song = self.client.playlist[int(status[u'song'])]
		if not self.__currentsong == status[u'song']:
			self.__currentsong = status[u'song']
			self.title.SetLabel(song[u'title'])
			self.artist.SetLabel(song[u'artist'])
			self.album.SetLabel(song[u'album'])
			self.Layout()
		image = self.artwork_loader[song]
		if not self.__image == image:
			self.__image = image
			if self.__image:
				self.artwork.SetBitmap(self.__image)
				self.artwork_mirror.SetBitmap(self.artwork_loader.mirror[song])
				self.artwork.Show()
				self.artwork_mirror.Show()
			else:
				self.artwork.Hide()
				self.artwork_mirror.Hide()
			self.Layout()
		
