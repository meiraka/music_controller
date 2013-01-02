#!/usr/bin/python

import thread

import wx

import artwork
import environment
import song

class PlaylistBase(wx.VListBox):
	def __init__(self,parent,playlist,playback,
			list_height,list_head_size,list_min_low,debug=False):
		wx.VListBox.__init__(self,parent,-1,style=wx.LB_MULTIPLE)
		self.playlist = playlist
		self.playback = playback
		self.__debug = debug
		self.ui_songs = []
		self.__focused = None
		self.__selected = []
		self.albums = {}
		self.pos_line = {}
		self.__list_head_size = list_head_size
		self.__list_height = list_height
		self.__list_min_row = list_min_low
		self.font = environment.ui.font
		self.font_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXTEXT)
		self.playlist.bind(self.playlist.UPDATE,self.update_playlist)
		self.playlist.bind(self.playlist.FOCUS,self.focus)
		self.playback.bind(self.playback.UPDATE,self.refresh)
		self.Bind(wx.EVT_LEFT_DCLICK,self.OnActivate)
		self.Bind(wx.EVT_KEY_UP,self.OnKeys)
		self.Bind(wx.EVT_RIGHT_UP,self.OnRight)

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
		self.play(index)

	def play(self,index):
		if len(self.ui_songs) > index:
			type,index,song = self.ui_songs[index]
			if song:
				song.play()

	def focus(self,*args,**kwargs):
		wx.CallAfter(self.__focus,self.playlist.focused)

	def __focus(self,song):
		index,n = self.GetFirstSelected()
		if index > -1 and not self.IsVisible(index):
			self.Select(0,True)
		self.DeselectAll()
		for index,(t,i,s) in enumerate(self.ui_songs):
			if t == 'song' and s == song:
				self.Select(index,True)
				if not self.IsVisible(index):
					self.ScrollLines(index)
				break
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
				if self.ui_songs and song_count < self.__list_min_row:
					self.ui_songs.extend([('nop',i+song_count,old_song) for i in xrange(self.__list_min_row-song_count)])
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
			return self.__list_height * self.__list_head_size
		else:
			return self.__list_height

	def OnDrawBackground(self,dc,rect,index):
		self.draw_background(dc,rect,index)

	def OnDrawItem(self,dc,rect,index):
		if not len(self.ui_songs) > index:
			return
		dc.SetTextForeground(self.font_color)
		dc.SetFont(self.font)
		type,group_index,song = self.ui_songs[index]
		songs_pos = rect.GetPosition()
		songs_pos[1] = songs_pos[1] - self.OnMeasureItem(index) * group_index
		songs_rect = wx.Rect(*(list(songs_pos)+list(rect.GetSize())))
		try:
			if type == 'nop':
				self.draw_songs(dc,songs_rect,song)
				self.draw_nothing(dc,rect,index,song,group_index)
			elif type == 'song':
				self.draw_songs(dc,songs_rect,song)
				if self.playback.status.has_key(u'song') and song[u'pos'] == self.playback.status[u'song']:
					self.draw_current_song(dc,rect,index,song,group_index)
				else:
					self.draw_song(dc,rect,index,song,group_index)
			else:
				self.draw_head(dc,rect,index,song)
		except:
			pass
	def OnKeys(self,event):
		if event.GetUnicodeKey() == wx.WXK_RETURN:
			index,n = self.GetFirstSelected()
			self.play(index)
		else:
			event.Skip()

	def OnRight(self,event):
		self.PopupMenu(Menu(self))


	def __selected(self):
		index,n = self.GetFirstSelected()
		items = []
		while not index == wx.NOT_FOUND:
			type,group_index,song = self.ui_songs[index]
			items.append(song)
			index,n = self.GetNextSelected(n)
		return items	
	selected = property(__selected)

class Menu(wx.Menu):
	def __init__(self,parent):
		wx.Menu.__init__(self)
		self.parent = parent
		items = [u'get_info',u'remove']
		self.__items = dict([(item,wx.NewId()) for item in items])
		for item in items:
			label = item.replace(u'_',' ')
			self.Append(self.__items[item],label,label)
			self.Bind(wx.EVT_MENU,getattr(self,item+'_item'),id=self.__items[item])

	def get_info_item(self,event):
		song.SongDialog(self.parent,self.parent.selected)

	def remove_item(self,event):
		pass

class Playlist(PlaylistBase):
	def __init__(self,parent,playlist,playback,debug=False):
		text_height = environment.ui.text_height
		PlaylistBase.__init__(self,parent,playlist,playback,
			text_height*3/2,2,6,debug)
		self.active_background_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT )
		self.background_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX)
		self.artwork = artwork.Artwork()
		self.artwork.size = (text_height*8,text_height*8)
		self.artwork.attach(self.RefreshAll)

	def head(self,song):
		if song.has_key(u'album'):
			return song[u'album']
		else:
			return '?'

	def draw_background(self,dc,rect,index):
		if self.IsSelected(index):
			color = self.active_background_color
		else:
			color = self.background_color
		dc.SetBrush(wx.Brush(color))
		dc.SetPen(wx.Pen(color))
		dc.DrawRectangle(*list(rect.GetPosition())+ list(rect.GetSize()))

	def draw_head(self,dc,rect,index,song):
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

	def draw_song(self,dc,rect,index,song,group_index):
		left_text = song[u'title']
		time = int(song[u'time'])
		right_text = u'%i:%s' % (time/60, str(time%60).zfill(2))
		pad = (rect.GetSize()[1] - dc.GetTextExtent('A-glFf')[1]) / 2
		margin = 10
		left_pos = rect.GetPosition()
		right_pos = rect.GetPosition()
		if group_index < 6:
			left_pos[0] = left_pos[0] + self.artwork.size[0]
		left_pos[0] = left_pos[0] + margin
		right_pos[0] = right_pos[0] - dc.GetTextExtent(right_text)[0] + rect.GetSize()[0] - margin
		left_pos = [i+pad for i in left_pos]
		right_pos = [i+pad for i in right_pos]
		dc.DrawText(left_text,*left_pos)
		dc.DrawText(right_text,*right_pos)

	def draw_current_song(self,dc,rect,index,song,group_index):
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
		if group_index < 6:
			left_pos[0] = left_pos[0] + self.artwork.size[0]
		left_pos[0] = left_pos[0] + margin
		right_pos[0] = right_pos[0] - dc.GetTextExtent(right_text)[0] + rect.GetSize()[0] - margin
		left_pos = [i+pad for i in left_pos]
		right_pos = [i+pad for i in right_pos]
		dc.DrawText(left_text,*left_pos)
		dc.DrawText(right_text,*right_pos)

	def draw_nothing(self,dc,rect,index,song,group_index):
		pass

	def draw_songs(self,dc,rect,song):
		bmp = self.artwork[song]
		if bmp:
			image_pos = rect.GetPosition()
			image_pos = [i+environment.ui.text_height/2 for i in image_pos]
			dc.DrawBitmap(bmp,*image_pos)

