#!/usr/bin/python
import wx
import environment

class Toolbar(object):
	def __init__(self,parent,playback):
		self.parent = parent
		toolbar_style = wx.TB_TEXT
		if environment.userinterface.toolbar_icon_horizontal:
			toolbar_style = wx.TB_HORZ_TEXT
		self.__tool = parent.CreateToolBar(toolbar_style)
		self.playback = playback
		size = None
		gtk = True if environment.userinterface.style == 'gtk' else False
		icons = [
			(u'previous', 'gtk-media-next-rtl' if gtk else wx.ART_GOTO_FIRST),
			(u'play',     'gtk-media-play-ltr' if gtk else wx.ART_GO_FORWARD),
			(u'next',     'gtk-media-next-ltr' if gtk else wx.ART_GOTO_LAST),
			(u'playlist', wx.ART_NORMAL_FILE),
			(u'library',  wx.ART_HARDDISK),
			(u'lyric',    wx.ART_PASTE)
			]
		self.icons = [(k, (wx.ArtProvider.GetBitmap(v,size=size), wx.NewId() ) ) for k,v in icons]
		if environment.userinterface.toolbar_icon_centre:
			self.__tool.AddStretchableSpace()
		for k,(icon,id) in self.icons:
			self.__tool.AddLabelTool(id,k,icon)
		if environment.userinterface.toolbar_icon_centre:
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


