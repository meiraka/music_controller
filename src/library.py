#!/usr/bin/python

import wx
import artwork
import thread
import environment

CRITERIA_STYLE_DEFAULT = u'default'
CRITERIA_STYLE_ALBUM = u'album'
CRITERIA_STYLE_SONG = u'song'
default_settings = [
	[(u'album',CRITERIA_STYLE_DEFAULT),
		(u'%album%',CRITERIA_STYLE_ALBUM),
		(u'%track% %title%',CRITERIA_STYLE_SONG)
	],
	[(u'genre',CRITERIA_STYLE_DEFAULT),
		(u'%genre%',CRITERIA_STYLE_DEFAULT),
		(u'%album%',CRITERIA_STYLE_ALBUM),
		(u'%track% %title%',CRITERIA_STYLE_ALBUM)
	],
	[(u'albumartist',CRITERIA_STYLE_DEFAULT),
		(u'%albumartist%',CRITERIA_STYLE_DEFAULT),
		(u'%album%',CRITERIA_STYLE_ALBUM)
	],
]

default_sorter = '%albumartist% %album% %track% %title%'

class LibraryBase(wx.VListBox):
	def __init__(self,parent,library,playlist,
			criteria_default_height,criteria_album_height,
			criteria_song_height,debug=False):
		wx.VListBox.__init__(self,parent,-1)
		self.library = library
		self.playlist = playlist
		self.settings = [[format for format,style in i] for i in default_settings]
		self.styles = [[style for format,style in i] for i in default_settings]
		self.sorter = default_sorter
		self.__master = []
		self.default_font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT )
		self.default_font_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXTEXT)
		self.__criteria_default_height = criteria_default_height
		self.__criteria_album_height = criteria_album_height
		self.__criteria_song_height = criteria_song_height
		self.Bind(wx.EVT_LEFT_UP,self.OnClick)
		self.library.bind(self.library.UPDATE,self.reset)
		#self.Bind(wx.EVT_LEFT_DCLICK,self.OnActivate)
		self.Bind(wx.EVT_RIGHT_UP,self.OnRightClick)

	def clear(self):
		self.items = []
		self.songs = []
		self.__master = list(self.library)
		wx.CallAfter(self.__reset)

	def reset(self,*args,**kwargs):
		wx.CallAfter(self.__reset)

	def __reset(self):
		self.state = (0,0)
		x,y = self.state
		self.items = [[(formats[x],y) for formats in self.settings]]
		if not self.__master:
			self.__master = list(self.library)
		self.songs = [dict([(item,self.__master) for item,y in self.items[y]])]
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
		x,y = self.state
		if len(self.items[y]) < index:
			return 0
		key,key_y = self.items[y][index]
		style = self.styles[x][key_y]
		if style == CRITERIA_STYLE_DEFAULT:
			return self.__criteria_default_height
		elif style == CRITERIA_STYLE_ALBUM:
			return self.__criteria_album_height
		elif style == CRITERIA_STYLE_SONG:
			return self.__criteria_song_height

	def OnDrawBackground(self,dc,rect,index):
		x,y = self.state
		key,key_y = self.items[y][index]
		style = self.styles[x][key_y]
		if len( self.songs[key_y][key]):
			song = self.songs[key_y][key][0]
		else:
			song = None
		self.draw_background(dc,rect,key,song,index,key_y,style)
	
	def OnDrawItem(self,dc,rect,index):
		dc.SetTextForeground(self.default_font_color)
		dc.SetFont(self.default_font)
		x,y = self.state
		key,key_y = self.items[y][index]
		style = self.styles[x][key_y]
		if len( self.songs[key_y][key]):
			song = self.songs[key_y][key][0]
		else:
			song = None
		if style == CRITERIA_STYLE_DEFAULT:
			self.draw_default(dc,rect,key,song,index,key_y)
		elif style == CRITERIA_STYLE_ALBUM:
			self.draw_album(dc,rect,key,song,index,key_y)
		elif style == CRITERIA_STYLE_SONG:
			self.draw_song(dc,rect,key,song,index,key_y)
		else:
			self.draw_default(dc,rect,key,song,index,key_y)
			

	def draw_default(self,dc,rect,label,song,index,depth):
		pos = rect.GetPosition()
		pos = (pos[0]+depth*10,pos[1])
		try:
			dc.DrawText(label,*pos)
		except:
			pass
	def draw_album(self,dc,rect,label,song,index,depth):
		self.draw_default(dc,rect,label,song,index,depth)
	def draw_song(self,dc,rect,label,song,index,depth):
		self.draw_default(dc,rect,label,song,index,depth)
	def draw_background(self,dc,rect,label,song,index,depth,style):
		pass

	def OnClick(self,event):
		index = self.GetSelection()
		self.__open(index)

	def OnRightClick(self,event):
		index = self.HitTest(event.GetPosition())
		self.SetSelection(index)
		self.PopupMenu(Menu(self,index))

	def and_item(self,index):
		row = index
		x,y = self.state
		key,key_y = self.items[y][row]
		self.__master = self.songs[key_y][key]
		wx.CallAfter(self.__reset)

	def not_item(self,index):
		row = index
		x,y = self.state
		key,key_y = self.items[y][row]
		self.__master = []
		for k,m in self.songs[y].iteritems():
			if not k == key:
				self.__master = self.__master + m
		wx.CallAfter(self.__reset)

	def replace_master(self):
		song_indexed = [(song.format(self.sorter),song) for song in self.__master]
		song_indexed.sort()
		songs = [song for title,song in song_indexed]
		self.playlist.clear()
		self.playlist.extend(songs)
		if len(self.playlist):
			self.playlist[0].play()


class Menu(wx.Menu):
	def __init__(self,parent,index):
		wx.Menu.__init__(self)
		self.parent = parent
		self.index=  index
		items = [u'and',u'not',u'clear',u'replace']
		self.__items = dict([(item,wx.NewId())for item in items])
		for item in items:
			self.Append(self.__items[item],item,item)
			self.Bind(wx.EVT_MENU,getattr(self,item+'_item'),id=self.__items[item])
	
	def and_item(self,event):
		self.parent.and_item(self.index)
				
	def not_item(self,event):
		self.parent.not_item(self.index)

	def clear_item(self,event):
		self.parent.clear()

	def replace_item(self,event):
		self.parent.replace_master()	


class Library(LibraryBase):
	def __init__(self,parent,library,playlist,debug=False):
		text_height = environment.ui.text_height
		LibraryBase.__init__(self,parent,library,playlist,
			text_height*2,text_height*6,text_height*2,debug)
		self.text_height = text_height
		self.artwork = artwork.Artwork()
		self.artwork.attach(self.RefreshAll)
	
	def draw_default(self,dc,rect,label,song,index,depth):
		pos = rect.GetPosition()
		pos = (pos[0]+depth*10+self.text_height/2,pos[1]+self.text_height/2)
		try:
			dc.DrawText(label,*pos)
		except:
			pass

	def draw_album(self,dc,rect,label,song,index,depth):
		bmp = self.artwork[song]
		if bmp:
			dc.DrawBitmap(bmp,*rect.GetPosition())

		
	def draw_background(self,dc,rect,label,song,index,depth,style):
		pass
