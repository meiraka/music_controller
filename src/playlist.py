#!/usr/bin/python

import wx

class Playlist(wx.ListBox):
	def __init__(self,parent,playlist,debug=False):
		wx.ListBox.__init__(self,parent,-1)
		self.playlist = playlist
		self.__debug = debug
		self.songs = []
		self.update_playlist()
		self.playlist.bind(self.playlist.UPDATE,self.update_playlist)
		self.Bind(wx.EVT_LISTBOX_DCLICK,self.OnActivate)
		self.playlist.bind(self.playlist.FOCUS,self.focus)

	def OnActivate(self,event):
		index = event.GetInt()
		self.songs[index].play()

	def update_playlist(self,*args,**kwargs):
		if self.__debug: print 'update_playlist'
		wx.CallAfter(self.__update_playlist)

	def __update_playlist(self):
		self.Clear()
		songs = self.__filter()
		if songs and not self.songs == songs:
			self.songs = songs
			self.InsertItems([self._generate_title(song) for song in songs],0)

	def __filter(self):
		album_song = None
		try:
			album_song = self.playlist.focused
		except:
			pass
		if album_song and album_song.has_key(u'album'):
			return [song for song in self.playlist if song.has_key(u'album') and song[u'album'] == album_song[u'album']]
		else:
			return [song for song in self.playlist]
			

	def _generate_title(self,song):
		try:
			return u'%(artist)s - %(title)s' % song
		except Exception,err:
			return str(err)

	def focus(self,*args,**kwargs):
		wx.CallAfter(self.__focus,self.playlist.focused)

	def __focus(self,focus_song):
		self.__update_playlist()
		for index,song in enumerate(self.songs):
			if song[u'pos'] ==focus_song:
				self.SetSelection(index)
