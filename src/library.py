#!/usr/bin/python

import wx

default_settings = [
(u'album',u'%album%',u'%number% %title%'),
(u'genre',u'%genre%',u'%album%',u'%number% %title%')




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
		self.Bind(wx.EVT_LEFT_DCLICK,self.OnClick)

	def __reset(self):
		self.state = (0,0)
		x,y = self.state
		self.items = [[(formats[x],y) for formats in self.settings]]
		songs = list(self.library)
		self.songs = [dict([(item,songs) for item,y in self.items[x]])]
		self.SetItemCount(len(self.items[y]))
		self.RefreshAll()

	def __close(self,row):
		x,y = self.state
		key,key_y = self.items[y][row]
		selected = self.items[y][row]
		top = self.GetVisibleBegin()
		del self.songs[key_y+1:]
		del self.items[key_y+1:]
		self.state = (x,key_y)
		self.SetItemCount(len(self.items[-1]))
		new_row = self.items[-1].index(selected)
		self.SetSelection(new_row)
		self.ScrollToLine(top)
		self.RefreshAll()

	def __open(self,row):
		if self.state[1] == 0:
			self.__reset()
			self.state = (row,0)
		x,y = self.state
		key,key_y = self.items[y][row]
		if key_y == y:
			top = self.GetVisibleBegin()
			songs = self.songs[y][key]
			new_items,new_songs = self.__extract(songs,y+1)
			selected = self.items[y][row]
			self.items.append(self.items[y][:row+1]+new_items+self.items[y][row+1:])
			self.songs.append(new_songs)
			self.state = (x,y+1)
			self.SetItemCount(len(self.items[-1]))
			new_row = self.items[y+1].index(selected)
			self.SetSelection(new_row)
			self.ScrollToLine(top)
			self.RefreshAll()
		else:
			self.__close(row)

	def __extract(self,songs,index):
		song_dict = {}
		song_format = self.settings[self.state[0]][index]
		def append(song,song_format):
			key = song.format(song_format)
			if not song_dict.has_key(key):
				song_dict[key] = []
			song_dict[key].append(song)
			return key
		items = [(append(song,song_format),index) for song in songs]
		items = sorted(set(items),key=items.index)
		return items,song_dict
		
		
	def OnMeasureItem(self,index):
		return 20

	def OnDrawItem(self,dc,rect,index):
		x,y = self.state
		dc.SetTextForeground(self.default_font_color)
		dc.SetFont(self.default_font)
		pos = rect.GetPosition()
		pos = (pos[0]+self.items[y][index][1]*10,pos[1])
		try:
			dc.DrawText(self.items[y][index][0],*pos)
		except:
			pass

	def OnClick(self,event):
		index = self.GetSelection()
		self.__open(index)


class Library(LibraryBase):
	pass
			
