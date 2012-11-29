#!/usr/bin/python

import wx

default_settings = [
(u'%Album%',u'%number% %title%'),
(u'%genre%',u'%album%',u'%number% %title%')




]

class LibraryBase(wx.VListBox):
	def __init__(self,parent,library,playlist,debug=False):
		wx.VListBox.__init__(self,parent,-1)
		self.library = library
		self.playlist = playlist
		self.settings = default_settings
		self.default_font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT )
		self.default_font_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXTEXT)
		self.__reset()
		self.Bind(wx.EVT_LEFT_DCLICK,self.OnActivate)

	def __reset(self):
		self.state = (0,-1)
		self.items = [[(formats[0].replace(u'%',u''),-1) for formats in self.settings]]
		self.songs = [list(self.library)]
		self.SetItemCount(len(self.items[0]))

	def __open_first(self,row):
		self.songs = [list(self.library)]
		songs = {}
		def cache(song,song_format):
			string = song.format(song_format)
			if not songs.has_key(string):
				songs[string] = []
			songs[string].append(song)
			return string
		song_format = self.settings[row][0]
		items = [cache(song,song_format) for song in self.songs[0]]
		items = sorted(set(items),key=items.index)
		items = [(item,0) for item in items]
		self.state = (row,0)
		self.songs.append(songs)
		self.items.append(self.items[0][:row+1]+items+self.items[row+1:])
		self.SetItemCount(len(self.items[1]))

	def OnMeasureItem(self,index):
		return 20

	def OnDrawItem(self,dc,rect,index):
		dc.SetTextForeground(self.default_font_color)
		dc.SetFont(self.default_font)
		print self.items[self.state[1]+1][index]
		dc.DrawText(self.items[self.state[1]+1][index][0],*rect.GetPosition())

	def OnActivate(self,event):
		index = self.GetSelection()
		if self.state[1] == -1:
			self.__open_first(index)	
			
class Library(LibraryBase):
	pass
			
