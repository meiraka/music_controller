#!/usr/bin/python

import wx

class Playlist(wx.VListBox):
	def __init__(self,parent,playlist,debug=False):
		wx.VListBox.__init__(self,parent,-1)
		self.playlist = playlist
		self.__debug = debug
		self.ui_songs = []
		self.screen_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		self.update_playlist()
		self.playlist.bind(self.playlist.UPDATE,self.update_playlist)
		self.image_size = (120,120)

	def update_playlist(self,*args,**kwargs):
		wx.CallAfter(self.__update_playlist)
	def __update_playlist(self):
		head = u''
		head_row = 2
		song_count = 0
		min_row = 6
		self.ui_songs = []
		for song in self.playlist:
			new_head = self.head(song)
			if not head == new_head:
				head = new_head
				if self.ui_songs and song_count < min_row:
					self.ui_songs.extend([('nop',i+song_count,None) for i in xrange(min_row-song_count)])
				song_count = 0
				self.ui_songs.extend([('head',i,song) for i in xrange(head_row)])
			self.ui_songs.append(('song',song_count,song))
			song_count = song_count + 1
		self.SetItemCount(len(self.ui_songs))

	def head(self,song):
		if song.has_key(u'album'):
			return song[u'album']
		else:
			return '?'

	def OnMeasureItem(self, index):
		return 20

	def OnDrawItem(self,dc,rect,index):
		#dc = wx.BufferedDC(dc)
		bg_color = wx.Colour(0,0,0,150)
		dc.SetTextForeground(bg_color)
		dc.SetFont(self.screen_font)
		type,index,song = self.ui_songs[index]
		if type == 'nop':
			self.OnDrawNothing(dc,rect)
		elif type == 'song':
			self.OnDrawSong(dc,rect,song,index)
		else:
			self.OnDrawHead(dc,rect,song,index)

	def OnDrawNothing(self,dc,rect):
		pass

	def OnDrawHead(self,dc,rect,song,index):
			dc.DrawText(song[u'album'],*rect.GetPosition())

	def OnDrawSong(self,dc,rect,song,index):
			dc.DrawText(song[u'title'],*rect.GetPosition())

	
class aPlaylist(wx.ListBox):
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
		songs = self.__filter()
		if songs and not self.songs == songs:
			self.Clear()
			self.songs = songs
			self.InsertItems([self._generate_title(song) for song in songs],0)

	def __filter(self):
		album_song = self.playlist.focused
		if album_song and album_song.has_key(u'album'):
			return [song for song in self.playlist if song.has_key(u'album') and song[u'album'] == album_song[u'album']]
		else:
			return []
			

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
