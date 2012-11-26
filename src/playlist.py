#!/usr/bin/python

import thread

import wx

import artwork

class Playlist(wx.VListBox):
	def __init__(self,parent,playlist,debug=False):
		wx.VListBox.__init__(self,parent,-1)
		self.playlist = playlist
		self.__debug = debug
		self.ui_songs = []
		self.screen_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		self.image_size = (120,120)
		self.albums = {}
		self.artwork = artwork.Artwork()
		self.playlist.bind(self.playlist.UPDATE,self.update_playlist)

	def update_playlist(self,*args,**kwargs):
		wx.CallAfter(self.__update_playlist)

	def __update_playlist(self):
		head = u''
		song_count = 0
		min_row = 6
		self.ui_songs = []
		old_song = None
		for song in self.playlist:
			new_head = self.head(song)
			if not head == new_head:
				head = new_head
				if self.ui_songs and song_count < min_row:
					self.ui_songs.extend([('nop',i+song_count,old_song) for i in xrange(min_row-song_count)])
				song_count = 0
				self.ui_songs.append(('head',0,song))
			self.ui_songs.append(('song',song_count,song))
			old_song = song
			song_count = song_count + 1
		self.SetItemCount(len(self.ui_songs))

	def head(self,song):
		if song.has_key(u'album'):
			return song[u'album']
		else:
			return '?'

	def OnMeasureItem(self, index):
		type,index,song = self.ui_songs[index]
		if type == 'head':
			return 20 * 2
		else:
			return 20

	def OnDrawItem(self,dc,rect,index):
		#dc = wx.BufferedDC(dc)
		bg_color = wx.Colour(0,0,0,150)
		dc.SetTextForeground(bg_color)
		dc.SetFont(self.screen_font)
		type,index,song = self.ui_songs[index]
		if type == 'nop':
			self.OnDrawNothing(dc,rect,song,index)
		elif type == 'song':
			self.OnDrawSong(dc,rect,song,index)
		else:
			self.OnDrawHead(dc,rect,song,index)

	def OnDrawNothing(self,dc,rect,song,index):
		self.OnDrawAlbum(dc,rect,song,index)

	def OnDrawHead(self,dc,rect,song,index):
			dc.DrawText(song[u'album'],*rect.GetPosition())

	def OnDrawSong(self,dc,rect,song,index):
			pos = rect.GetPosition()
			if index < self.image_size[1] / 20:
				self.OnDrawAlbum(dc,rect,song,index)
				pos[0] = pos[0] + self.image_size[0]
			dc.DrawText(song[u'title'],*pos)

	def OnDrawAlbum(self,dc,rect,song,index):
		bmp = self.get_album(song)
		if bmp:
			image_pos = rect.GetPosition()
			image_pos[1] = image_pos[1] - 20 * index 
			dc.DrawBitmap(bmp,*image_pos)


	def get_album(self,song):
		if not song.has_key(u'album'):
			return None
		if not self.albums.has_key(song[u'album']):
			self.albums[song[u'album']] = None
			thread.start_new_thread(self.load_image,(song,))
		else:
			return self.albums[song[u'album']]

	def load_image(self,song):
		path = self.artwork[song]
		if path:
			image = wx.Image(path)
			w,h = image.GetSize()
			if w > h:
				new_size = (self.image_size[0],h/w*self.image_size[1])
			else:
				new_size = (w/h*self.image_size[0],self.image_size[1])
			image.Rescale(*new_size,quality=wx.IMAGE_QUALITY_HIGH)
			wx.CallAfter(self.__load_image,song,image)
	
	def __load_image(self,song,image):
		bmp = wx.BitmapFromImage(image)
		self.albums[song[u'album']] = bmp
		self.SetItemCount(len(self.ui_songs))

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
