#!/usr/bin/python

import wx

class Playlist(wx.ListBox):
	def __init__(self,parent,playlist,debug=False):
		wx.ListBox.__init__(self,parent,-1)
		self.playlist = playlist
		self.__debug = debug
		self.update_playlist()
		self.playlist.bind(self.playlist.UPDATE,self.update_playlist)
		self.Bind(wx.EVT_LISTBOX_DCLICK,self.OnActivate)

	def OnActivate(self,event):
		index = event.GetInt()
		self.playlist[index].play()

	def update_playlist(self,*args,**kwargs):
		if self.__debug: print 'update_playlist'
		wx.CallAfter(self.__update_playlist)

	def __update_playlist(self):
		self.Clear()
		songs = [self._generate_title(song) for song in self.playlist]
		if songs:
			self.InsertItems(songs,0)

	def _generate_title(self,song):
		try:
			return u'%(artist)s - %(title)s' % song
		except Exception,err:
			return str(err)
