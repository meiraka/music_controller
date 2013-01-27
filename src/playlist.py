#!/usr/bin/python

import thread

import wx

import artwork
import environment
import dialog

class ViewBase(wx.VListBox):
	def __init__(self,parent,playlist,playback,head_format,
			list_height,list_head_size,list_min_low,debug=False):
		wx.VListBox.__init__(self,parent,-1,style=wx.LB_MULTIPLE)
		# set client objects.
		self.playlist = playlist
		self.playback = playback
		# generates by this ui.
		self.songs = []       # playlist struct
		self.__line_song = {} # key=line index value=song
		# sets by this ui and another playlist ui.
		self.__focused = None
		self.__selected = []
		# set __init__ args to private values.
		self.__head_format = head_format
		self.__list_head_size = list_head_size
		self.__list_height = list_height
		self.__list_min_row = list_min_low
		self.__debug = debug

		self.font = environment.userinterface.font
		self.font_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXTEXT)
		self.playlist.bind(self.playlist.UPDATE,self.update_playlist)
		self.playlist.bind(self.playlist.FOCUS,self.focus)
		self.playback.bind(self.playback.UPDATE,self.refresh)
		self.Bind(wx.EVT_LEFT_DCLICK,self.OnActivate)
		self.Bind(wx.EVT_LEFT_UP,self.OnFocus)
		self.Bind(wx.EVT_KEY_DOWN,self.OnKeysDown)
		self.Bind(wx.EVT_KEY_UP,self.OnKeysUp)
		self.Bind(wx.EVT_RIGHT_UP,self.OnRightClick)

	def refresh(self,*args):
		""" Refreashes current playing song pos in main thread."""
		wx.CallAfter(self.__refresh)

	def __refresh(self):
		""" Refreashes current playing song pos."""
		status = self.playback.status
		if status and status.has_key(u'song'):
			song_id = status[u'song']
		else:
			return
		if self.__line_song.has_key(song_id):
			self.RefreshLine(self.__line_song[song_id])

		

	def play(self,index):
		if len(self.songs) > index:
			type,index,song = self.songs[index]
			if song:
				song.play()

	def focus(self,*args,**kwargs):
		wx.CallAfter(self.__focus,self.playlist.focused)

	def __focus(self,song):
		index,n = self.GetFirstSelected()
		if index in self.songs and song == self.songs[index][2]:
			return
		if index > -1 and not self.IsVisible(index):
			self.Select(0,True)
		self.DeselectAll()
		for index,(t,i,s) in enumerate(self.songs):
			if t == 'song' and s == song:
				self.Select(index,True)
				if not self.IsVisible(index):
					self.ScrollLines(index)
				break
	def update_playlist(self,*args,**kwargs):
		""" Updates playlist view in main thread.
		"""
		wx.CallAfter(self.__update_playlist)

	def __update_playlist(self):
		""" Updates playlist view.

		generates new playlist struct
		and focuses current song.
		"""
		self.songs,self.__line_song = self.__generate_playlist_struct()
		self.SetItemCount(len(self.songs))
		self.focus()

	def __generate_playlist_struct(self):
		""" Generates list struct for this playlist ui.

		returns:
			(playlist struct, playlist index-song dict)

		playlist struct is:
		[
			(
				string line type,
				int index starts at 'head' type,
				client.Playlist.Song object
			)
		]
		"""
		head = u''        #group key
		song_count = 0
		ui_songs = []
		pos_line = {}
		old_song = None
		for song in self.playlist:
			new_head = song.format(self.__head_format)
			if not head == new_head:
				head = new_head
				if ui_songs and song_count < self.__list_min_row and old_song:
					ui_songs.extend([('nop',i+song_count,old_song) for i in xrange(self.__list_min_row-song_count)])
				song_count = 0
				ui_songs.append(('head',0,song))
			pos_line[song[u'pos']] = len(ui_songs)
			ui_songs.append(('song',song_count,song))
			old_song = song
			song_count = song_count + 1
		return (ui_songs,pos_line)


	def OnMeasureItem(self, index):
		if len(self.songs) > index and self.songs[index][0] == 'head':
			return self.__list_height * self.__list_head_size
		else:
			return self.__list_height

	def OnDrawBackground(self,dc,rect,index):
		self.draw_background(dc,rect,index)

	def OnDrawItem(self,dc,rect,index):
		if not len(self.songs) > index:
			return
		dc.SetTextForeground(self.font_color)
		dc.SetFont(self.font)
		type,group_index,song = self.songs[index]
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

	def OnActivate(self,event):
		""" catch double-click event. play the clicked song."""
		index,n = self.GetFirstSelected()
		self.play(index)

	def OnClick(self,event):
		""" detect focus song.

		if focus song was changed, set new focused song.
		"""
		current = self.playlist.focused
		index,n = self.GetFirstSelected()
		if index > -1:
			type,group_index,song = self.songs[index]
			if type == 'song' and not song == current:
				self.playlist.focused = song
				return
		event.Skip()

	def OnKeysUp(self,event):
		index,n = self.GetFirstSelected()
		key = event.GetKeyCode()
		if key == wx.WXK_RETURN:
			self.play(index)
		else:
			event.Skip()

	def OnKeysDown(self,event):
		""" key down event. change focused item in playlist."""
		index,n = self.GetFirstSelected()
		key = event.GetKeyCode()
		if key == wx.WXK_UP:
			current_song = self.songs[index][2]
			pos = int(current_song[u'pos'])
			if 0 < pos <= len(self.playlist)-1:
				song = self.playlist[pos-1]
				self.playlist.focused = song
		elif key == wx.WXK_DOWN:
			current_song = self.songs[index][2]
			pos = int(current_song[u'pos'])
			if 0 <= pos < len(self.playlist)-1:
				song = self.playlist[pos+1]
				self.playlist.focused = song
		elif key == wx.WXK_LEFT:
			current_song = self.songs[index][2]
			uis = self.songs[:index+1]
			uis.reverse()
			head_count = 0
			for type,group_index,song in uis:
				if type == 'head':
					head_count = head_count + 1
				if head_count == 2:
					break
			if song:
				self.playlist.focused = song
		elif key == wx.WXK_RIGHT:
			current_song = self.songs[index][2]
			uis = self.songs[index:]
			head_count = 0
			for type,group_index,song in uis:
				if type == 'head':
					head_count = head_count + 1
				if head_count == 1:
					break
			if song:
				self.playlist.focused = song
		else:
			event.Skip()

	def OnRightClick(self,event):
		index = self.HitTest(event.GetPosition())
		selected = self.__selected_indexes()
		if not index in selected:
			self.DeselectAll()
			self.SetSelection(index)
		self.PopupMenu(Menu(self))

	def __selected_indexes(self):
		"""Returns selected indexes in Playlist."""
		index,n = self.GetFirstSelected()
		items = []
		while not index == wx.NOT_FOUND:
			items.append(index)
			index,n = self.GetNextSelected(n)
		return items	
	
	def __selected(self):
		"""Returns selected songs in Playlist."""
		songs = [self.songs[index][2] for index in self.__selected_indexes()]
		return songs
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
		dialog.SongInfo(self.parent,self.parent.selected)

	def remove_item(self,event):
		for song in self.parent.selected:
			song.remove()

class AlbumList(wx.ScrolledWindow):
	def __init__(self,parent,playlist,playback,debug=False):
		wx.ScrolledWindow.__init__(self,parent,style=wx.TAB_TRAVERSAL)
		self.playlist = playlist
		self.albums = []
		self.__focused_index = -1
		text_height = environment.userinterface.text_height
		self.image_width = text_height * 10
		self.box_size = (self.image_width,self.image_width)
		self.SetMinSize((-1,self.image_width))
		self.Bind(wx.EVT_PAINT,self.OnPaint)
		self.artwork = artwork.Artwork()
		self.scroll_block = text_height
		self.artwork.size = (text_height*8,text_height*8)
		self.artwork.bind(self.artwork.UPDATE,self.update)
		self.active_background_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT )
		self.background_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX)
		self.SetBackgroundColour(self.background_color)
		thread.start_new_thread(self.__update_album_list,())
		self.playlist.bind(self.playlist.UPDATE,self.__update_album_list)
		self.playlist.bind(self.playlist.FOCUS, self.focus)
		self.Bind(wx.EVT_LEFT_DCLICK,self.OnActivate)
		self.Bind(wx.EVT_LEFT_UP,    self.OnClick)
		self.Bind(wx.EVT_KEY_UP,     self.OnKeysUp)
		self.Bind(wx.EVT_KEY_DOWN,   self.OnKeysDown)

	def OnActivate(self,event):
		mouse = event.GetPosition()
		x,y = self.CalcUnscrolledPosition(mouse)
		w,h = self.box_size
		index = x/w
		song = self.albums[index]
		song.play()
	
	def OnClick(self,event):
		mouse = event.GetPosition()
		x,y = self.CalcUnscrolledPosition(mouse)
		w,h = self.box_size
		index = x/w
		if not self.__focused_index == index:
			self.playlist.focused = self.albums[index]

	def OnKeysUp(self,event):
		""" Key up event. 
		press return key to play the focused album's song.
		"""
		key = event.GetKeyCode()
		if key == wx.WXK_RETURN:
			song = self.albums[self.__focused_index]
			song.play()
		else:
			event.Skip()


	def OnKeysDown(self,event):
		""" Key down event.
		change song forcus.
		"""
		key = event.GetKeyCode()
		if key == wx.WXK_LEFT:
			if 0 < self.__focused_index <= len(self.albums)-1:
				self.__focused_index = self.__focused_index -1
				self.playlist.focused = self.albums[self.__focused_index]
		elif key == wx.WXK_RIGHT:
			if 0 <= self.__focused_index < len(self.albums)-1:
				self.__focused_index = self.__focused_index + 1
				self.playlist.focused = self.albums[self.__focused_index]
		elif key == wx.WXK_UP:
			song = self.playlist.focused
			pos = int(song[u'pos'])
			if 0 < pos <= len(self.playlist)-1:
				self.playlist.focused = self.playlist[pos-1]
		elif key == wx.WXK_DOWN:
			song = self.playlist.focused
			pos = int(song[u'pos'])
			if 0 <= pos < len(self.playlist)-1:
				self.playlist.focused = self.playlist[pos+1]
		else:
			event.Skip()
		
		

	def focus(self):
		def __scroll(self,index):
			""" scroll to given index."""
			x,y = self.GetViewStart()
			wu,hu = self.GetScrollPixelsPerUnit()
			w,h = self.GetSize()
			item_w,item_h = self.box_size
			goto = index*item_w
			if x*wu < goto < x*wu + w:
				return -1
			else:
				# new pos is greater than current pos
				if x*wu < goto:
					goto = goto - w + item_w
				self.Scroll(goto/wu,-1)
				return goto
		focused = self.playlist.focused
		last_album = None
		index = -1
		for song in self.playlist:
			if not last_album == song.format('%album%'):
				last_album = song.format('%album%')
				index = index + 1
			if song == focused:
				break
		else:
			index = -1
		self.__focused_index = index
		wx.CallAfter(self.update)
		if index > -1:
			wx.CallAfter(__scroll,self,index)
	

	def __update_album_list(self):
		last_album = None
		albums = []
		for song in self.playlist:
			if not last_album == song.format('%album%'):
				last_album = song.format('%album%')
				albums.append(song)
		self.albums = albums
		wx.CallAfter(self.__update_window_size)
		wx.CallAfter(self.focus)

	def __update_window_size(self):
		self.SetScrollbars(self.scroll_block,self.scroll_block,
			len(self.albums)*self.image_width/self.scroll_block,1)

	def OnPaint(self,event):
		dc = wx.BufferedPaintDC(self)
		self.update_canvas(dc)

	def update(self):
		dc = wx.ClientDC(self)
		dc = wx.BufferedDC(dc)
		self.update_canvas(dc)

	def update_canvas(self,dc):
		w,h = self.box_size
		size_w,size_h = self.GetSize()
		for index,song in enumerate(self.albums):
			x,y = self.CalcScrolledPosition(index*w,0)
			if 0-w < x < size_w and 0-h < y < size_h:
				rect = (x,y,w,h)
				self.draw_background(index,song,dc,rect)
				self.draw_album(index,song,dc,rect)

	def draw_background(self,index,song,dc,rect):
		if index == self.__focused_index:
			color = self.active_background_color
		else:
			color = self.background_color
		dc.SetBrush(wx.Brush(color))
		dc.SetPen(wx.Pen(color))
		dc.DrawRectangle(*rect)

	def draw_album(self,index,song,dc,rect):
		x,y,w,h = rect
		text_height = environment.userinterface.text_height
		x = x + text_height*1
		y = y + text_height*1
		image = self.artwork[song]
		if not image:
			image = self.artwork.empty
		dc.DrawBitmap(image,x,y)

class View(ViewBase):
	def __init__(self,parent,playlist,playback,debug=False):
		text_height = environment.userinterface.text_height
		ViewBase.__init__(self,parent,playlist,playback,u'%album%',
			text_height*3/2,2,6,debug)
		self.active_background_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT )
		self.background_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX)
		self.artwork = artwork.Artwork()
		self.artwork.size = (text_height*8,text_height*8)
		self.artwork.bind(self.artwork.UPDATE,self.RefreshAll)

	def draw_background(self,dc,rect,index):
		if self.IsSelected(index):
			color = self.active_background_color
		else:
			color = self.background_color
		dc.SetBrush(wx.Brush(color))
		dc.SetPen(wx.Pen(color))
		dc.DrawRectangle(*list(rect.GetPosition())+ list(rect.GetSize()))

	def draw_head(self,dc,rect,index,song):
		left_text = song.format(u'%album%')
		right_text = song.format(u'%genre%')
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
		left_text = song.format(u'%title%')
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
		left_text = u'>>>' + song.format(u'%title%')
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
			image_pos = [i+environment.userinterface.text_height/2 for i in image_pos]
			dc.DrawBitmap(bmp,*image_pos)

