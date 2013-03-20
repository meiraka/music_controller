#!/usr/bin/python

import thread

import wx

from common import artwork
from common import environment
from common.client import Song

class Info(wx.BoxSizer):
	def __init__(self,parent,client,debug=False):
		wx.BoxSizer.__init__(self)
		self.parent = parent
		self.client = client
		self.__currentsong = 0
		self.__lock = False
		self.__image = None
		h = environment.userinterface.text_height
		self.artwork = wx.StaticBitmap(parent,-1)
		self.artwork_mirror = wx.StaticBitmap(parent,-1)
		self.single_text = dict(
			title   = wx.StaticText(parent,-1)
			,artist = wx.StaticText(parent,-1)
			)
		self.slider = wx.Slider(parent,-1,50,0,100,size=(h*12,-1))
		self.slider.Bind(wx.EVT_SCROLL_THUMBTRACK,self.OnSlider)
		self.double_text = dict(
			album  = wx.StaticText(parent,-1)
			,genre = wx.StaticText(parent,-1)
			)
		self.artwork_loader = artwork.Database(mirror=True)
		self.artwork_loader.size = (h*12,h*12)
		self.SetMinSize((h*16,h*16))
		self.artwork_loader.bind(self.artwork_loader.UPDATE,self.update)

		imgsizer = wx.BoxSizer(wx.VERTICAL)
		imgsizer.Add(self.artwork,0)
		imgsizer.Add(self.artwork_mirror,0)
		singlesizer = wx.BoxSizer(wx.VERTICAL)
		for label in self.single_text.values():
			singlesizer.Add(label,0,wx.ALIGN_CENTRE|wx.ALL,border=3)
		doublesizer = wx.GridBagSizer()
		for index,(key,label) in enumerate(self.double_text.iteritems()):
			doublesizer.Add(wx.StaticText(parent,-1,key+':'),(index,0),flag=wx.ALIGN_RIGHT|wx.ALL,border=3)
			doublesizer.Add(label,(index,1),flag=wx.ALIGN_LEFT|wx.ALL,border=3)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(imgsizer,0,wx.ALIGN_CENTRE|wx.ALIGN_CENTRE_VERTICAL|wx.TOP,border=h*2)
		self.sizer.Add(singlesizer,0,wx.ALIGN_CENTRE)
		self.sizer.Add(self.slider,0,wx.ALIGN_CENTRE)
		self.sizer.Add(doublesizer,0,wx.ALIGN_CENTRE|wx.BOTTOM,border=h*2)
		self.Add(self.sizer,1,wx.EXPAND)
		self.__update({},Song({}))
		self.client.playback.bind(self.client.playback.UPDATE,self.update)

	def Hide(self):
		self.ShowItems(False)
		self.parent.Layout()

	def Show(self):
		self.ShowItems(True)
		self.parent.Layout()

	def update(self,*args,**kwargs):
		wx.CallAfter(self.__update,self.client.playback.status)

	def resize_image(self,*args,**kwargs):
		self.__resize_image()

	def __update(self,status,song=None):
		if song is None and (not status or not status.has_key(u'song')):
			return
		if song is None and len(self.client.playlist)> int(status[u'song']):
			song = self.client.playlist[int(status[u'song'])]
			if not self.__currentsong == status[u'song']:
				self.__currentsong = status[u'song']
		if song and self.__currentsong is not None:
			for key,label in self.single_text.iteritems():
				label.SetLabel(song.format(u'%'+key+u'%'))
				label.Wrap(environment.userinterface.text_height*16)
			for key,label in self.double_text.iteritems():
				label.SetLabel(song.format(u'%'+key+u'%'))
				label.Wrap(environment.userinterface.text_height*8)
			self.Layout()
		if u'time' in status:
			current,max = [int(i) for i in status[u'time'].split(u':')]
			if not self.slider.GetMax() == max:
				self.slider.SetMax(max)
			self.slider.SetValue(current)
		image = self.artwork_loader[song]
		if not self.__image == image:
			self.__image = image
			if self.__image:
				self.artwork.SetBitmap(self.__image)
				self.artwork_mirror.SetBitmap(self.artwork_loader.mirror[song])
			else:
				self.artwork.SetBitmap(self.artwork_loader.empty)
				self.artwork_mirror.SetBitmap(self.artwork_loader.mirror.empty)

			self.Layout()

	def OnSlider(self,event):
		pos = self.slider.GetValue()
		self.client.playback.seek(pos)
