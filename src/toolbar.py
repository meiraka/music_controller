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
			view =     ['gtk-media-play-ltr',wx.ART_GO_DOWN],
			previous = ['gtk-media-next-rtl',wx.ART_GO_BACK],
			play =     ['gtk-media-play-ltr',wx.ART_GO_FORWARD],
			stop =     ['gtk-media-stop',wx.ART_GO_UP],
			next =     ['gtk-media-next-ltr',wx.ART_GO_FORWARD],
			playlist = ['media-tape',wx.ART_NORMAL_FILE],
			library =  ['folder-music',wx.ART_HARDDISK],
			lyric =    ['applications-office',wx.ART_PASTE],
			info =     [wx.ART_GO_FORWARD],
			)
		labels = [
			(u'view',    self.TYPE_NORMAL),
			(u'',        self.TYPE_STRETCH),
			(u'previous',self.TYPE_NORMAL),
                        (u'play',    self.TYPE_TOGGLE),
			(u'stop',    self.TYPE_NORMAL),
                        (u'next',    self.TYPE_NORMAL),
                        (u'playlist',self.TYPE_RADIO),
                        (u'library', self.TYPE_RADIO),
                        (u'lyric',   self.TYPE_RADIO),
			(u'',        self.TYPE_STRETCH),
			(u'info',    self.TYPE_NORMAL)
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
			elif label == u'view':
				if environment.userinterface.toolbar_icon_dropdown:
					self.__tool.AddLabelTool(id,label,icon)
			elif label == u'info':
				if environment.userinterface.toolbar_icon_info:
					self.__tool.AddLabelTool(id,label,icon)
			elif environment.userinterface.toolbar_toggle:
				if button_type == self.TYPE_TOGGLE:
					self.__tool.AddCheckLabelTool(id,label,icon)
				elif button_type == self.TYPE_RADIO and not environment.userinterface.toolbar_icon_dropdown:
					self.__tool.AddRadioLabelTool(id,label,icon)
				elif button_type == self.TYPE_RADIO:
					pass
				else:
					self.__tool.AddLabelTool(id,label,icon)
			elif not(button_type == self.TYPE_RADIO and environment.userinterface.toolbar_icon_dropdown):
				self.__tool.AddLabelTool(id,label,icon)
	
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
		updates = [u'view',u'playlist',u'library',u'lyric']
		enable = self.connection.connected
		def __update():
			for label,icon,id,button_type in self.__buttons:
				if updates.count(label):
					self.__tool.EnableTool(id,enable)
		wx.CallAfter(__update)

	def update_selector(self):
		if not environment.userinterface.toolbar_toggle or environment.userinterface.toolbar_icon_dropdown:
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
		elif func_name == 'view':
			self.parent.PopupMenu(ViewMenu(self))
		elif func_name == 'playlist':
			self.parent.show_playlist()
		elif func_name == 'library':
			self.parent.show_library()
		elif func_name == 'lyric':
			self.parent.show_lyric()
		elif func_name == 'info':
			current = self.client.config.info
			self.client.config.info = not(current)
			self.parent.show_not_connection()
		elif hasattr(self.playback,func_name):
			getattr(self.playback,func_name)()


class ViewMenu(wx.Menu):
	def __init__(self,parent):
		wx.Menu.__init__(self)
		self.parent = parent
		items = [u'playlist',u'library',u'lyric']
		self.__items = dict([(item,wx.NewId()) for item in items])
		for item in items:
			self.Append(self.__items[item],item,item)
			self.Bind(wx.EVT_MENU,getattr(self,'show_'+item),id=self.__items[item])

	def show_playlist(self,event):
		self.parent.parent.show_playlist()

	def show_library(self,event):
		self.parent.parent.show_library()

	def show_lyric(self,event):
		self.parent.parent.show_lyric()
