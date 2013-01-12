#!/usr/bin/python
import wx
import environment

class MacToolbar(object):
	def __init__(self,parent,playback):
		self.parent = parent
		self.__tool = parent.CreateToolBar(wx.TB_TEXT)
		self.playback = playback
		#size = (19,19)
		size = None
		#self.__tool.SetToolBitmapSize(size)
		icons = [
			(u'previous', wx.ArtProvider.GetBitmap(wx.ART_GOTO_FIRST,size=size)),
			(u'play',     wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD,size=size)),
			(u'next',     wx.ArtProvider.GetBitmap(wx.ART_GOTO_LAST,size=size)),
			(u'playlist', wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE,size=size)),
			(u'library',  wx.ArtProvider.GetBitmap(wx.ART_HARDDISK,size=size)),
			(u'lyric',    wx.ArtProvider.GetBitmap(wx.ART_PASTE,size=size))
			]
		self.icons = [(k, (v, wx.NewId() ) ) for k,v in icons]
		self.__tool.AddStretchableSpace()
		for k,(icon,id) in self.icons:
			self.__tool.AddLabelTool(id,k,icon)
		self.__tool.AddStretchableSpace()
		self.__tool.Realize()
		self.__tool.Bind(wx.EVT_TOOL,self.OnTool)

	def OnTool(self,event):
		event_id = event.GetId()
		for func_name,(icon,id) in self.icons:
			if event_id == id:
				obj = self.__tool.FindById(id)
				if obj.GetLabel() == u'play':
					self.playback.play()
					obj.SetLabel(u'pause')
				elif obj.GetLabel() == u'pause':
					self.playback.pause()
					obj.SetLabel(u'play')
				elif func_name == 'playlist':
					self.parent.show_playlist()
				elif func_name == 'library':
					self.parent.show_library()
				elif func_name == 'lyric':
					self.parent.show_lyric()
				elif hasattr(self.playback,func_name):
					getattr(self.playback,func_name)()


class GTKToolbar(object):
	def __init__(self,parent,playback):
		self.__tool = parent.CreateToolBar()
		self.parent = parent
		self.playback = playback
		self.play = wx.Button(self.__tool,-1,u'play')
		self.previous = wx.Button(self.__tool,-1,u'previous')
		self.next = wx.Button(self.__tool,-1,u'next')
		self.playlist = wx.Button(self.__tool,-1,u'playlist')
		self.library = wx.Button(self.__tool,-1,u'library')
		self.state = ''
		self.__tool.Bind(wx.EVT_BUTTON,self.OnButton)
		self.__tool.AddControl(self.previous)
		self.__tool.AddControl(self.play)
		self.__tool.AddControl(self.next)
		self.__tool.AddControl(self.playlist)
		self.__tool.AddControl(self.library)
		self.__tool.Realize()
		self.playback.bind(self.playback.UPDATE,self.update_label)

	def update_label(self,*args,**kwargs):
		wx.CallAfter(self.__update_label,self.playback.status)

	def __update_label(self,status):
		if not self.state == status[u'state']:
			self.state = status[u'state']
			if self.state == u'play':
				self.play.SetLabel(u'pause')
			else:
				self.play.SetLabel(u'play')

	def OnButton(self,event):
		obj = event.GetEventObject()
		if obj == self.play:
			if self.state == u'play':
				self.playback.pause()
			else:
				self.playback.play()
		elif obj == self.next:
			self.playback.next()
		elif obj == self.previous:
			self.playback.previous()
		elif obj == self.playlist:
			self.parent.show_playlist()
		elif obj == self.library:
			self.parent.show_library()
		

if environment.userinterface.style == 'mac':
	Toolbar = MacToolbar
else:
	Toolbar = GTKToolbar
