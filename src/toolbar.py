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
		icons = dict(
			previous = 'gtk-media-next-rtl' if gtk else wx.ART_GOTO_FIRST,
			play =     'gtk-media-play-ltr' if gtk else wx.ART_GO_FORWARD,
			next =     'gtk-media-next-ltr' if gtk else wx.ART_GOTO_LAST,
			playlist = wx.ART_NORMAL_FILE,
			library =  wx.ART_HARDDISK,
			lyric =    wx.ART_PASTE
			)
		labels = [
			(u'previous',),
                        (u'play',    ),
                        (u'next',    ),
                        (u'playlist',),
                        (u'library', ),
                        (u'lyric',   )
			]
		self.__buttons = [
			(label,wx.ArtProvider.GetBitmap(icons[label]),wx.NewId()) for (label,) in labels
			]
		if environment.userinterface.toolbar_icon_centre:
			self.__tool.AddStretchableSpace()
		for label,icon,id in self.__buttons:
			self.__tool.AddLabelTool(id,label,icon)
		if environment.userinterface.toolbar_icon_centre:
			self.__tool.AddStretchableSpace()
		self.__tool.Bind(wx.EVT_TOOL,self.OnTool)
		self.__tool.Realize()
		self.playback.bind(self.playback.UPDATE,self.update)

	def update(self):
		def __update():
			obj = None
			for label,icon,id in self.__buttons:
				if label == u'play':
					obj = self.__tool.FindById(id)
					break
			else:
				return
			if u'state' in self.playback.status and self.playback.status[u'state'] == u'play':
				if obj.GetLabel() == u'play':
					obj.SetLabel(u'pause')
			else:
				if not obj.GetLabel() == u'play':
					obj.SetLabel(u'play')
		wx.CallAfter(__update)

	def OnTool(self,event):
		event_id = event.GetId()
		for func_name,icon,id in self.__buttons:
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


