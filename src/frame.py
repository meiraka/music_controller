import wx

import toolbar
import playlist
import library
import info


class Frame(wx.Frame):
	def __init__(self,parent,client,debug=False):
		""" generate main app window."""
		self.parent = parent
		self.client = client
		wx.Frame.__init__(self,parent,-1)
		self.SetSize((640,480))
		if debug: print 'init frame'

		self.toolbar = toolbar.Toolbar(self,self.client.playback)
		if debug: print 'init playlist'
		self.playlist = playlist.Playlist(self,self.client.playlist,self.client.playback,debug)
		if debug: print 'init library'
		self.library = library.Library(self,self.client.library,self.client.playlist,debug)
		#self.info = info.Info(self,self.client,debug)
		if debug: print 'sizing'

		self.sizer = wx.BoxSizer()
		s = wx.BoxSizer(wx.VERTICAL)
		#s.Add(self.info,0,wx.EXPAND)
		s.Add(self.playlist,1,flag=wx.EXPAND)
		s.Add(self.library,1,flag=wx.EXPAND)
		self.sizer.Add(s,1,flag=wx.EXPAND)
		#self.sizer.Add(self.albumlist,0,flag=wx.EXPAND)
		self.library.Hide()
		self.SetSizer(self.sizer)
		self.Layout()
		self.Show()
		if debug: print 'sized.'
		self.client.playback.bind(self.client.playback.UPDATE_PLAYING,self.change_title)
		if debug: print 'binded.'

	def show_library(self):
		self.playlist.Hide()
		self.library.Show()
		self.Layout()
	
	def show_playlist(self):
		self.library.Hide()
		self.playlist.Show()
		self.Layout()

	def change_title(self):
		wx.CallAfter(self.__change_title)

	def __change_title(self):
		status = self.client.playback.status
		if status and status.has_key(u'song'):
			song_id = int(status[u'song'])
			if len(self.client.playlist) > song_id:
				song = self.client.playlist[song_id]
				self.SetTitle(song.format('%title% - %artist%'))
