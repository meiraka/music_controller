#!/usr/bin/python
import wx
from common import environment

def get_nonnull_bitmap(stock_labels):
	for label in stock_labels:
		bmp = wx.ArtProvider.GetBitmap(label)
		if bmp.IsOk() and not bmp.GetSize() == (-1,-1):
			return bmp
	return None

class Toolbar(object):
	TYPE_TOGGLE = 'toggle'
	TYPE_NORMAL = 'normal'
	TYPE_RADIO = 'radio'
	TYPE_STRETCH = 'stretch'
	def __init__(self,parent,client):
		self.parent = parent
		toolbar_style = wx.TB_TEXT
		if environment.userinterface.toolbar_icon_horizontal:
			toolbar_style = wx.TB_HORZ_TEXT
		self.__tool = parent.CreateToolBar(toolbar_style)
		self.client = client
		self.playback = client.playback
		self.connection = client.connection
		size = None
		icons = dict(
			View =     ['gtk-media-play-ltr',wx.ART_GO_DOWN],
			Previous = ['gtk-media-next-rtl',wx.ART_GO_BACK],
			Play =     ['gtk-media-play-ltr',wx.ART_GO_FORWARD],
			Stop =     ['gtk-media-stop',wx.ART_GO_UP],
			Next =     ['gtk-media-next-ltr',wx.ART_GO_FORWARD],
			Playlist = ['media-tape',wx.ART_NORMAL_FILE],
			Library =  ['folder-music',wx.ART_HARDDISK],
			Lyric =    ['applications-office',wx.ART_PASTE],
			Info =     [wx.ART_GO_FORWARD],
			)
		labels = [
			(u'View',    self.TYPE_NORMAL),
			(u'',        self.TYPE_STRETCH),
			(u'Previous',self.TYPE_NORMAL),
                        (u'Play',    self.TYPE_TOGGLE),
			(u'Stop',    self.TYPE_NORMAL),
                        (u'Next',    self.TYPE_NORMAL),
                        (u'Playlist',self.TYPE_RADIO),
                        (u'Library', self.TYPE_RADIO),
                        (u'Lyric',   self.TYPE_RADIO),
			(u'',        self.TYPE_STRETCH),
			(u'Info',    self.TYPE_NORMAL)
			]
		self.__buttons = [
			(label,get_nonnull_bitmap(icons[label]) if label in icons else None,wx.NewId(),button_type) for (label,button_type) in labels
			]
		self.__ids = dict([(label,id) for label,bmp,id,button_type in self.__buttons])
		self.__labels = dict([(id,label) for label,bmp,id,button_type in self.__buttons])
		for label,icon,id,button_type in self.__buttons:
			if button_type == self.TYPE_STRETCH:
				if environment.userinterface.toolbar_icon_centre:
					self.__tool.AddStretchableSpace()
			elif label == u'View':
				if environment.userinterface.toolbar_icon_dropdown:
					self.__tool.AddLabelTool(id,_(label),icon)
			elif label == u'Info':
				if environment.userinterface.toolbar_icon_info:
					self.__tool.AddLabelTool(id,_(label),icon)
			elif environment.userinterface.toolbar_toggle:
				if button_type == self.TYPE_TOGGLE:
					self.__tool.AddCheckLabelTool(id,_(label),icon)
				elif button_type == self.TYPE_RADIO and not environment.userinterface.toolbar_icon_dropdown:
					self.__tool.AddRadioLabelTool(id,_(label),icon)
				elif button_type == self.TYPE_RADIO:
					pass
				else:
					self.__tool.AddLabelTool(id,_(label),icon)
			elif not(button_type == self.TYPE_RADIO and environment.userinterface.toolbar_icon_dropdown):
				self.__tool.AddLabelTool(id,_(label),icon)
	
		self.__tool.Bind(wx.EVT_TOOL,self.OnTool)
		self.__tool.Realize()
		self.connection.bind(self.connection.UPDATE,self.update_playback)
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
				if label == u'Play':
					obj = self.__tool.FindById(id)
					break
			else:
				return
			if u'state' in self.connection.server_status and self.connection.server_status[u'state'] == u'play':
				if obj.GetLabel() == _(u'Play'):
					obj.SetLabel(_(u'Pause'))
					if environment.userinterface.toolbar_toggle:
						self.__tool.ToggleTool(id,True)
			else:
				if not obj.GetLabel() == _(u'Play'):
					obj.SetLabel(_(u'Play'))
					if environment.userinterface.toolbar_toggle:
						self.__tool.ToggleTool(id,False)
		wx.CallAfter(__update)

	def update_connection(self):
		updates = [u'View',u'Playlist',u'Library',u'Lyric',u'Previous',u'Play',u'Stop',u'Next',u'Info']
		enable = self.connection.connected
		def __update():
			for label,icon,id,button_type in self.__buttons:
				if updates.count(label):
					self.__tool.EnableTool(id,enable)
		wx.CallAfter(__update)

	def update_selector(self):
		if not environment.userinterface.toolbar_toggle or environment.userinterface.toolbar_icon_dropdown:
			return
		updates = [u'Playlist',u'Library',u'Lyric']
		for view in updates:
			self.__tool.ToggleTool(self.__ids[view],view.lower()==self.parent.current_view)

	def OnTool(self,event):
		event_id = event.GetId()
		obj = self.__tool.FindById(event_id)
		func_name = self.__labels[event_id]
		radio = ['Playlist','Library','Lyric']
		if obj.GetLabel() == _(u'Play'):
			self.playback.play()
			obj.SetLabel(_(u'Pause'))
		elif obj.GetLabel() == _(u'Pause'):
			self.playback.pause()
			obj.SetLabel(_(u'Play'))
		elif func_name == 'View':
			self.parent.PopupMenu(ViewMenu(self))
		elif func_name == 'Playlist':
			self.parent.show_playlist()
		elif func_name == 'Library':
			self.parent.show_library()
		elif func_name == 'Lyric':
			self.parent.show_lyric()
		elif func_name == 'Info':
			current = self.client.config.info
			self.client.config.info = not(current)
			self.parent.show_not_connection()
		elif hasattr(self.playback,func_name.lower()):
			getattr(self.playback,func_name.lower())()


class ViewMenu(wx.Menu):
	def __init__(self,parent):
		wx.Menu.__init__(self)
		self.parent = parent
		items = [u'Playlist',u'Library',u'Lyric']
		self.__items = dict([(item,wx.NewId()) for item in items])
		for item in items:
			id = self.__items[item]
			self.AppendRadioItem(id,_(item),_(item))
			if item.lower() == self.parent.parent.current_view:
				self.Check(id,True)
			func_name = 'show_'+item.lower()
			self.Bind(wx.EVT_MENU,getattr(self,func_name),id=id)

	def show_playlist(self,event):
		self.parent.parent.show_playlist()

	def show_library(self,event):
		self.parent.parent.show_library()

	def show_lyric(self,event):
		self.parent.parent.show_lyric()
