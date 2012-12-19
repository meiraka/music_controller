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
		self.single_text = dict(
			title   = wx.StaticText(self,-1)
			,artist = wx.StaticText(self,-1)
			)
		self.slider = wx.Slider(self,-1)
		self.slider.Bind(wx.EVT_SCROLL_THUMBTRACK,self.OnSlider)
		self.double_text = dict(
			album  = wx.StaticText(self,-1)
			,genre = wx.StaticText(self,-1)
			)
		self.artwork_loader = artwork.Artwork()
		h = environment.ui.text_height
		self.artwork_loader.size = (h*12,h*12)
		self.SetMinSize((h*16,h*16))
		self.artwork_loader.attach(self.update)

		imgsizer = wx.BoxSizer(wx.VERTICAL)
		imgsizer.Add(self.artwork,0)
		imgsizer.Add(self.artwork_mirror,0)
		singlesizer = wx.BoxSizer(wx.VERTICAL)
		for label in self.single_text.values():
			singlesizer.Add(label,0,wx.ALIGN_CENTRE|wx.ALL,border=3)
		doublesizer = wx.GridBagSizer()
		for index,(key,label) in enumerate(self.double_text.iteritems()):
			doublesizer.Add(wx.StaticText(self,-1,key+':'),(index,0),flag=wx.ALIGN_RIGHT|wx.ALL,border=3)
			doublesizer.Add(label,(index,1),flag=wx.ALIGN_LEFT|wx.ALL,border=3)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(imgsizer,0,wx.ALIGN_CENTRE|wx.TOP,border=h*2)
		sizer.Add(singlesizer,0,wx.ALIGN_CENTRE)
		sizer.Add(self.slider,0,wx.ALIGN_CENTRE)
		sizer.Add(doublesizer,0,wx.ALIGN_CENTRE|wx.BOTTOM,border=h*2)
		self.SetSizer(sizer)
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
			for key,label in self.single_text.iteritems():
				label.SetLabel(song.format(u'%'+key+u'%'))
				label.Wrap(environment.ui.text_height*16)
			for key,label in self.double_text.iteritems():
				label.SetLabel(song.format(u'%'+key+u'%'))
				label.Wrap(environment.ui.text_height*8)
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
				self.artwork.Show()
				self.artwork_mirror.Show()
			else:
				self.artwork.Hide()
				self.artwork_mirror.Hide()
			self.Layout()

	def OnSlider(self,event):
		pos = self.slider.GetValue()
		self.client.playback.seek(pos)
