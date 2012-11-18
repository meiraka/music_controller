#!/usr/bin/python

import wx

class Playlist(wx.ListBox):
	def __init__(self,parent,playlist):
		wx.ListBox.__init__(self,parent,-1)
		self.playlist = playlist

		self.update_playlist()

	def update_playlist(self):
		self.Clear()
		songs = [self._generate_title(song) for song in self.playlist]
		self.InsertItems(songs,0)

	def _generate_title(self,song):
		return '%(artist)s - %(title)s' % song
