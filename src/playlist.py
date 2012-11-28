#!/usr/bin/python

import thread

import wx

import artwork

class Playlist(wx.VListBox):
	def __init__(self,parent,playlist,playback,debug=False):
		wx.VListBox.__init__(self,parent,-1,style=wx.LB_MULTIPLE)
		self.playlist = playlist
		self.playback = playback
		self.__debug = debug
		self.ui_songs = []
		self.__focused = None
		self.__selected = []
		self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT )
		self.font_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXTEXT)
		self.active_background_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT )
		self.background_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX)
		self.image_size = (120,120)
		self.list_head_size = 2
		self.list_height = 20
		self.list_min_row = 6
		self.albums = {}
		self.pos_line = {}
		self.artwork = artwork.Artwork()
		self.playlist.bind(self.playlist.UPDATE,self.update_playlist)
		self.playlist.bind(self.playlist.FOCUS,self.focus)
		self.playback.bind(self.playback.UPDATE,self.refresh)
		self.Bind(wx.EVT_LEFT_DCLICK,self.OnActivate)

	def refresh(self,*args):
		wx.CallAfter(self.__refresh)

	def __refresh(self):
		status = self.playback.status
		if status and status.has_key(u'song'):
			song_id = status[u'song']
		else:
			return
		if self.pos_line.has_key(song_id):
			self.RefreshLine(self.pos_line[song_id])

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
				if not self.IsVisible(index):
					self.ScrollLines(index)

	def update_playlist(self,*args,**kwargs):
		wx.CallAfter(self.__update_playlist)

	def __update_playlist(self):
		head = u''
		song_count = 0
		self.ui_songs = []
		old_song = None
		for song in self.playlist:
			new_head = self.head(song)
			if not head == new_head:
				head = new_head
				if self.ui_songs and song_count < self.list_min_row:
					self.ui_songs.extend([('nop',i+song_count,old_song) for i in xrange(self.list_min_row-song_count)])
				song_count = 0
				self.ui_songs.append(('head',0,song))
			self.pos_line[song[u'pos']] = len(self.ui_songs)
			self.ui_songs.append(('song',song_count,song))
			old_song = song
			song_count = song_count + 1
		self.SetItemCount(len(self.ui_songs))
		self.focus()

	def head(self,song):
		if song.has_key(u'album'):
			return song[u'album']
		else:
			return '?'

	def OnMeasureItem(self, index):
		if len(self.ui_songs) > index and self.ui_songs[index][0] == 'head':
			return self.list_height * self.list_head_size
		else:
			return self.list_height

	def OnDrawBackground(self,dc,rect,index):
		#dc = wx.BufferedDC(dc)
		if self.IsSelected(index):
			color = self.active_background_color
		else:
			color = self.background_color
		dc.SetBrush(wx.Brush(color))
		dc.SetPen(wx.Pen(color))
		dc.DrawRectangle(*list(rect.GetPosition())+ list(rect.GetSize()))

	def OnDrawItem(self,dc,rect,index):
		#dc = wx.BufferedDC(dc)
		#dc.SetBrush(wx.Brush(self.background_color))
		#dc.SetPen(wx.Pen(self.background_color))
		#dc.DrawRectangle(*list(rect.GetPosition())+ list(rect.GetSize()))
		dc.SetTextForeground(self.font_color)
		dc.SetFont(self.font)
		type,index,song = self.ui_songs[index]
		if type == 'nop':
			self.OnDrawNothing(dc,rect,song,index)
		elif type == 'song':
			if song[u'pos'] == self.playback.status[u'song']:
				self.OnDrawCurrentSong(dc,rect,song,index)
			else:
				self.OnDrawSong(dc,rect,song,index)
		else:
			self.OnDrawHead(dc,rect,song,index)

	def OnDrawNothing(self,dc,rect,song,index):
		self.OnDrawAlbum(dc,rect,song,index)

	def OnDrawHead(self,dc,rect,song,index):
			left_text = song[u'album']
			right_text = song[u'genre'] if song.has_key(u'genre') else u''
			size = dc.GetTextExtent(left_text+right_text)
			w,h = rect.GetSize()
			margin = 10
			p = h/2 + (h/2 - size[1]) / 2
			left_pos = rect.GetPosition()
			right_pos = rect.GetPosition()
			left_pos[1] = left_pos[1] + p
			right_pos[1] = right_pos[1] + p
			right_pos[0] = right_pos[0] - dc.GetTextExtent(right_text)[0] + dc.GetSize()[0]
			left_pos[0] = left_pos[0] + margin
			right_pos[0] = right_pos[0] - margin
			dc.DrawText(left_text,*left_pos)
			dc.DrawText(right_text,*right_pos)

	def OnDrawSong(self,dc,rect,song,index):
			left_text = song[u'title']
			time = int(song[u'time'])
			right_text = u'%i:%s' % (time/60, str(time%60).zfill(2))
			pad = (rect.GetSize()[1] - dc.GetTextExtent('A-glFf')[1]) / 2
			margin = 10
			left_pos = rect.GetPosition()
			right_pos = rect.GetPosition()
			if index < self.image_size[1] / 20:
				self.OnDrawAlbum(dc,rect,song,index)
				left_pos[0] = left_pos[0] + self.image_size[0]
			left_pos[0] = left_pos[0] + margin
			right_pos[0] = right_pos[0] - dc.GetTextExtent(right_text)[0] + rect.GetSize()[0] - margin
			left_pos = [i+pad for i in left_pos]
			right_pos = [i+pad for i in right_pos]
			dc.DrawText(left_text,*left_pos)
			dc.DrawText(right_text,*right_pos)

	def OnDrawCurrentSong(self,dc,rect,song,index):
			left_text = u'>>>' + song[u'title']
			time = int(song[u'time'])
			status = self.playback.status
			if status and status.has_key(u'time'):
				right_text = '/'.join([ u'%i:%s' % (int(i)/60,str(int(i)%60).zfill(2)) for i in status[u'time'].split(u':')])
			else:
				right_text = u'%i:%s' % (time/60, str(time%60).zfill(2))
			pad = (rect.GetSize()[1] - dc.GetTextExtent('A-glFf')[1]) / 2
			margin = 10
			left_pos = rect.GetPosition()
			right_pos = rect.GetPosition()
			if index < self.image_size[1] / 20:
				self.OnDrawAlbum(dc,rect,song,index)
				left_pos[0] = left_pos[0] + self.image_size[0]
			left_pos[0] = left_pos[0] + margin
			right_pos[0] = right_pos[0] - dc.GetTextExtent(right_text)[0] + rect.GetSize()[0] - margin
			left_pos = [i+pad for i in left_pos]
			right_pos = [i+pad for i in right_pos]
			dc.DrawText(left_text,*left_pos)
			dc.DrawText(right_text,*right_pos)



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
		self.RefreshAll()

