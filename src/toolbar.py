#!/usr/bin/python
import wx
import environment

class Toolbar(object):
	TYPE_TOGGLE = 'toggle'
	TYPE_NORMAL = 'normal'
	def __init__(self,parent,client):
		self.parent = parent
		toolbar_style = wx.TB_TEXT
		if environment.userinterface.toolbar_icon_horizontal:
			toolbar_style = wx.TB_HORZ_TEXT
		self.__tool = parent.CreateToolBar(toolbar_style)
		self.playback = client.playback
		self.connection = client.connection
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
			(u'previous',self.TYPE_NORMAL),
                        (u'play',    self.TYPE_TOGGLE),
                        (u'next',    self.TYPE_NORMAL),
                        (u'playlist',self.TYPE_TOGGLE),
                        (u'library', self.TYPE_TOGGLE),
                        (u'lyric',   self.TYPE_TOGGLE)
			]
		self.__buttons = [
			(label,wx.ArtProvider.GetBitmap(icons[label]),wx.NewId(),button_type) for (label,button_type) in labels
			]
		self.__ids = dict([(label,id) for label,bmp,id,button_type in self.__buttons])
		self.__labels = dict([(id,label) for label,bmp,id,button_type in self.__buttons])
		if environment.userinterface.toolbar_icon_centre:
			self.__tool.AddStretchableSpace()
		for label,icon,id,button_type in self.__buttons:
			if environment.userinterface.toolbar_toggle:
				if button_type == self.TYPE_TOGGLE:
					self.__tool.AddCheckLabelTool(id,label,icon)
				else:
					self.__tool.AddLabelTool(id,label,icon)
			else:
				self.__tool.AddLabelTool(id,label,icon)
		if environment.userinterface.toolbar_icon_centre:
			self.__tool.AddStretchableSpace()
		self.__tool.Bind(wx.EVT_TOOL,self.OnTool)
		self.__tool.Realize()
		self.playback.bind(self.playback.UPDATE,self.update_playback)
		self.connection.bind(self.connection.CONNECT,self.update_connection)
		self.connection.bind(self.connection.CLOSE,self.update_connection)
		self.connection.bind(self.connection.CLOSE_UNEXPECT,self.update_connection)
		self.parent.bind(self.parent.VIEW,self.update_selector)
		self.update_playback()
		self.update_connection()

	def update_playback(self):
		def __update():
			obj = None
			id = None
			for label,icon,id,button_type in self.__buttons:
				if label == u'play':
					obj = self.__tool.FindById(id)
					break
			else:
				return
			if u'state' in self.playback.status and self.playback.status[u'state'] == u'play':
				if obj.GetLabel() == u'play':
					obj.SetLabel(u'pause')
					if environment.userinterface.toolbar_toggle:
						self.__tool.ToggleTool(id,True)
			else:
				if not obj.GetLabel() == u'play':
					obj.SetLabel(u'play')
					if environment.userinterface.toolbar_toggle:
						self.__tool.ToggleTool(id,False)
		wx.CallAfter(__update)

	def update_connection(self):
		updates = [u'playlist',u'library',u'lyric']
		enable = self.connection.connected
		def __update():
			for label,icon,id,button_type in self.__buttons:
				if updates.count(label):
					self.__tool.EnableTool(id,enable)
		wx.CallAfter(__update)

	def update_selector(self):
		if not environment.userinterface.toolbar_toggle:
			return
		updates = [u'playlist',u'library',u'lyric']
		for view in updates:
			self.__tool.ToggleTool(self.__ids[view],view==self.parent.current_view)

	def OnTool(self,event):
		event_id = event.GetId()
		obj = self.__tool.FindById(event_id)
		func_name = self.__labels[event_id]
		radio = ['playlist','library','lyric']
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


