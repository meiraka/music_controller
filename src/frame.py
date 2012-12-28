import wx

import toolbar
import playlist
import library
import info
import menubar
import preferences
import environment

class Frame(wx.Frame):
	TITLE = 'MusicController'
	def __init__(self,parent,client,debug=False):
		""" generate main app window."""
		self.parent = parent
		self.client = client
		wx.Frame.__init__(self,parent,-1)
		self.SetTitle(self.TITLE)
		self.SetSize((640,480))
		self.menubar = menubar.MenuBar(self,client,accele=False if environment.gui == 'mac' else True)
		self.SetMenuBar(self.menubar)
		if debug: print 'init frame'
		self.toolbar = toolbar.Toolbar(self,self.client.playback)

		if debug: print 'init playlist'
		self.playlist = playlist.Playlist(self,self.client.playlist,self.client.playback,debug)
		if debug: print 'init library'
		self.library = library.Library(self,self.client.library,self.client.playlist,debug)
		self.info = info.Info(self,self.client,debug)
		self.connection = preferences.Connection(self,self.client.connection,self.client.config)
		self.dammy = wx.Panel(self,-1)
		if debug: print 'sizing'

		self.sizer = wx.BoxSizer()
		s = wx.BoxSizer()
		s.Add(self.playlist,1,flag=wx.EXPAND)
		s.Add(self.library,1,flag=wx.EXPAND)
		s.Add(self.connection,1,flag=wx.EXPAND)
		s.Add(self.dammy,1,flag=wx.EXPAND)
		self.sizer.Add(s,1,flag=wx.EXPAND)
		self.sizer.Add(self.info,0,wx.EXPAND)
		#self.sizer.Add(self.albumlist,0,flag=wx.EXPAND)
		self.playlist.Hide()
		self.library.Hide()
		self.connection.Hide()
		self.SetSizer(self.sizer)
		self.Layout()
		self.info.Hide()
		h = environment.ui.text_height
		self.SetSize((h*48,h*36))
		self.preferences = None
		self.change_title()
		if self.client.connection.current:
			self.show_playlist()
		self.Show()
		if debug: print 'sized.'
		self.client.playback.bind(self.client.playback.UPDATE_PLAYING,self.change_title)
		if debug: print 'binded.'

	def show_connection(self):
		self.SetTitle(self.TITLE +' - '+ 'connection')
		self.dammy.Hide()
		self.playlist.Hide()
		self.library.Hide()
		self.info.Hide()
		self.connection.Show()
		self.Layout()

	def show_library(self):
		self.dammy.Hide()
		self.connection.Hide()
		self.playlist.Hide()
		self.info.Show()
		self.library.Show()
		self.Layout()
	
	def show_playlist(self):
		self.dammy.Hide()
		self.connection.Hide()
		self.library.Hide()
		self.info.Show()
		self.playlist.Show()
		self.Layout()

	def change_title(self):
		wx.CallAfter(self.__change_title)

	def __change_title(self):
		status = self.client.playback.status
		title = self.TITLE
		if status and status.has_key(u'song'):
			song_id = int(status[u'song'])
			if len(self.client.playlist) > song_id:
				song = self.client.playlist[song_id]
				title = self.TITLE +u' - '+ song.format('%title% - %artist%')
		self.SetTitle(title)

	def show_preferences(self):
		if not self.preferences:
			self.preferences = preferences.Frame(None,self.client)
		self.preferences.Show()

