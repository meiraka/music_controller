"""
Main application window.

"""

import wx

from common import Object
from common import environment
import toolbar
import playlist
import library
import songinfo
import lyrics
import menubar
import preferences

class Frame(wx.Frame,Object):
	TITLE = 'MusicController'
	VIEW = 'view'
	VIEW_PLAYLIST = 'playlist'
	VIEW_LIBRARY = 'library'
	VIEW_LYRIC = 'lyric'
	def __init__(self,parent,client,debug=False):
		""" generate main app window."""
		self.parent = parent
		self.client = client
		self.current_view = 'playlist'
		wx.Frame.__init__(self,parent,-1)
		Object.__init__(self)
		self.SetTitle(self.TITLE)
		icon = wx.ArtProvider.GetIcon('gtk-media-play-ltr',size=(128,128))
		if icon.IsOk():
			self.SetIcon(icon)
	
		self.menubar = menubar.MenuBar(self,client,accele=False if environment.userinterface.style == 'mac' else True)
		# add mac Help -> search item. (not work)
		wx.GetApp().SetMacHelpMenuTitleName(_('Help'))
		self.SetMenuBar(self.menubar)
		self.toolbar = toolbar.Toolbar(self,self.client)
		if environment.userinterface.fill_window_background:
			base = wx.Panel(self,-1)
		else:
			base = self
		self.playlist = playlist.HeaderPlaylist(base,self.client,debug)
		self.library = library.View(base,self.client,debug)
		self.albumlist = playlist.AlbumList(base,self.client,debug)
		self.info = songinfo.Info(base,self.client,debug)
		self.connection = preferences.Connection(base,self.client)
		self.lyric = lyrics.LyricView(base,self.client)
		self.sizer = wx.BoxSizer()
		s = wx.BoxSizer(wx.VERTICAL)
		s.Add(self.playlist,1,flag=wx.EXPAND)
		s.Add(self.library,1,flag=wx.EXPAND)
		s.Add(self.connection,1,flag=wx.EXPAND)
		s.Add(self.lyric,1,flag=wx.EXPAND)
		s.Add(self.albumlist,0,flag=wx.EXPAND)
		self.sizer.Add(s,1,flag=wx.EXPAND)
		self.sizer.Add(self.info,0,wx.EXPAND)
		#self.sizer.Add(self.albumlist,0,flag=wx.EXPAND)
		base.SetSizer(self.sizer)
		if environment.userinterface.fill_window_background:
			sizer = wx.BoxSizer()
			sizer.Add(base,1,wx.EXPAND)
			self.SetSizer(sizer)
		self.hide_children()
		self.Layout()
		window_size = self.client.config.window_size
		if window_size == (-1,-1):
			h = environment.userinterface.text_height
			self.SetSize((h*64,h*48))
		else:
			w,h = window_size
			if w < 100:
				w = 100
			if h < 100:
				h = 100
			self.SetSize((w,h))
		self.preferences = None
		self.change_title()
		if self.client.connection.current:
			self.show_not_connection()
		self.Bind(wx.EVT_SIZE,self.OnSize)
		self.Show()
		if debug: print 'sized.'
		self.client.connection.bind(self.client.connection.UPDATE_PLAYING,self.change_title)
		if debug: print 'binded.'

	def can_get_info(self):
		view = getattr(self,self.current_view)
		return hasattr(view,'IsShown') and view.IsShown() and hasattr(view,'selected_get_info')

	def get_info(self):
		getattr(getattr(self,self.current_view),'selected_get_info')()

	def hide_children(self):
		self.playlist.Hide()
		self.albumlist.Hide()
		self.library.Hide()
		self.connection.Hide()
		self.info.Hide()
		self.lyric.Hide()

	def show_connection(self):
		self.SetTitle(self.TITLE +' - '+ 'connection')
		self.playlist.Hide()
		self.albumlist.Hide()
		self.library.Hide()
		self.lyric.Hide()
		self.info.Hide()
		self.Layout()
		self.connection.Show()
		self.Layout()
		self.call(self.VIEW)

	def show_not_connection(self):
		if not self.current_view:
			if len(self.client.playlist):
				self.show_playlist()
			else:
				self.show_library()
		else:
			if self.current_view == self.VIEW_PLAYLIST:
				self.show_playlist()
			elif self.current_view == self.VIEW_LIBRARY:
				self.show_library()
			else:
				self.show_lyric()

	def show_library(self):
		""" Show library and song info."""
		self.current_view = self.VIEW_LIBRARY
		self.change_title()
		self.connection.Hide()
		self.playlist.Hide()
		self.albumlist.Hide()
		self.lyric.Hide()
		self.Layout()
		self.library.Show()
		self.library.SetFocus()
		if self.client.config.info:
			self.info.Show()
		else:
			self.info.Hide()
		self.Layout()
		self.call(self.VIEW)
	
	def show_playlist(self):
		""" Show playlist and song info."""
		self.current_view = self.VIEW_PLAYLIST
		self.change_title()
		self.connection.Hide()
		self.library.Hide()
		self.lyric.Hide()
		self.Layout()
		self.playlist.Show()
		self.playlist.SetFocus()
		if self.client.config.playlist_albumlist:
			self.albumlist.Show()
		else:
			self.albumlist.Hide()
		if self.client.config.info:
			self.info.Show()
		else:
			self.info.Hide()
		self.Layout()
		self.call(self.VIEW)

	def show_lyric(self):
		""" Show lyric and song info."""
		self.current_view = self.VIEW_LYRIC
		self.change_title()
		self.connection.Hide()
		self.library.Hide()
		self.playlist.Hide()
		self.albumlist.Hide()
		self.Layout()
		self.lyric.Show()
		self.lyric.SetFocus()
		if self.client.config.info:
			self.info.Show()
		else:
			self.info.Hide()
		self.Layout()
		self.call(self.VIEW)

	def __get_search_view(self):
		if self.playlist.IsShown() and hasattr(self.playlist,'search_first'):
			return self.playlist
		else:
			return None

	def search_first(self,text):
		view = self.__get_search_view()
		if view:
			view.search_first(text)

	def search_next(self):
		view = self.__get_search_view()
		if view:
			view.search_next()

	def change_title(self):
		wx.CallAfter(self.__change_title)

	def __change_title(self):
		status = self.client.connection.server_status
		title = self.TITLE
		if status and status.has_key(u'song'):
			song_id = int(status[u'song'])
			if len(self.client.playlist) > song_id:
				song = self.client.playlist[song_id]
				title = self.TITLE +u' - '+ song.format('%title% - %artist%')
		self.SetTitle(title)

	def show_preferences(self):
		if not self.preferences:
			def hide(event):
				event.GetEventObject().Hide()
			self.preferences = preferences.App(None,self.client)
			self.preferences.Bind(wx.EVT_CLOSE,hide)
			
		self.preferences.Show()

	def OnSize(self,event):
		self.client.config.window_size =  self.GetSize()
		event.Skip()

