#!/usr/bin/python

import thread

import wx

import artwork

class Playlist(wx.VListBox):
	def __init__(self,parent,playlist,debug=False):
		wx.VListBox.__init__(self,parent,-1,style=wx.LB_MULTIPLE)
		self.playlist = playlist
		self.__debug = debug
		self.ui_songs = []
		self.__focused = None
		self.__selected = []
		self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT )
		self.font_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXTEXT)
		self.image_size = (120,120)
		self.albums = {}
		self.artwork = artwork.Artwork()
		self.playlist.bind(self.playlist.UPDATE,self.update_playlist)
		self.playlist.bind(self.playlist.FOCUS,self.focus)
		self.Bind(wx.EVT_LEFT_DCLICK,self.OnActivate)

	def OnActivate(self,event):
		index,n = self.GetFirstSelected()
		if len(self.ui_songs) > index:
			type,index,song = self.ui_songs[index]
			if song:
				song.play()

	def focus(self,*args,**kwargs):
		wx.CallAfter(self.__focus,self.playlist.focused)

	def __focus(self,song):
		self.DeselectAll()
		for index,(t,i,s) in enumerate(self.ui_songs):
			if t == 'song' and s == song:
				self.Select(index,True)
				if not self.IsRowVisible(index):
					self.ScrollRows(index)
				break

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
		if len(self.ui_songs) <= index:
			return 0
		type,index,song = self.ui_songs[index]
		if type == 'head':
			return 20 * 2
		else:
			return 20

	def OnDrawItem(self,dc,rect,index):
		#dc = wx.BufferedDC(dc)
		dc.SetTextForeground(self.font_color)
		dc.SetFont(self.font)
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
				new_size = (self.image_size[0],int(1.0*h/w*self.image_size[1]))
			else:
				new_size = (int(1.0*w/h*self.image_size[0]),self.image_size[1])
			if all([i > 0 for i in new_size]):
				image.Rescale(*new_size,quality=wx.IMAGE_QUALITY_HIGH)
			wx.CallAfter(self.__load_image,song,image)
	
	def __load_image(self,song,image):
		bmp = wx.BitmapFromImage(image)
		self.albums[song[u'album']] = bmp
		self.SetItemCount(len(self.ui_songs))

