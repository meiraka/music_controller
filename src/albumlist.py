#!/usr/bin/python

import thread

import wx

import artwork


class AlbumList(wx.ListCtrl):
	def __init__(self,parent,playlist,debug=False):
		self.playlist = playlist
		self.artwork_loader = artwork.Artwork()
		self.__image_size = (128,128)
		wx.ListCtrl.__init__(self,parent,-1,
			style=wx.LC_SINGLE_SEL|wx.LC_NO_HEADER|wx.LC_REPORT|wx.LC_VIRTUAL,
			size=(150,150))
		self.InsertColumn(0,'')
		self.SetColumnWidth(0,150)
		self.image_list = wx.ImageList(*self.__image_size)
		self.index_song = []
		self.image_list_index = {}
		self.image_list_album_index = {}
		self.SetImageList(self.image_list,wx.IMAGE_LIST_SMALL)
		self.playlist.bind(self.playlist.UPDATE,self.update)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnClick)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnActivate)

	def update(self,*args,**kwargs):
		thread.start_new_thread(self.__update,())

	def __update(self):
		prev = ''
		albums = []
		self.index_song = []
		for song in self.playlist:
			if not prev == song[u'album']:
				prev = song[u'album']
				albums.append(song)
				self.index_song.append(song)
		wx.CallAfter(self.SetItemCount,len(self.index_song))
		self.focus()

	def __add_image_list(self,song):
		path = self.artwork_loader[song]
		if path:
			if not self.image_list_index.has_key(path):
				image = wx.Image(path)
				w,h = image.GetSize()
				if w > h:
					resize = (self.__image_size[0],h/w*self.__image_size[0])
				else:
					resize = (w/h*self.__image_size[1],self.__image_size[1])
				image.Rescale(*resize,quality=wx.IMAGE_QUALITY_HIGH)
				bmp = wx.BitmapFromImage(image)
				index = self.image_list.GetImageCount() 
				self.image_list_index[path] = index
				self.image_list_album_index[song[u'album']] = index
				self.image_list.Add(bmp)
				self.SetImageList(self.image_list,wx.IMAGE_LIST_SMALL)

	def focus(self,*args,**kwargs):
		wx.CallAfter(self.__focus,self.playlist.focused)

	def __focus(self,focus_song):
		if focus_song and focus_song.has_key(u'album') and not focus_song == self.__get_selected():
			current_index = self.GetNextItem(-1,wx.LIST_NEXT_ALL,wx.LIST_STATE_SELECTED)
			prev = ''
			index = -1
			for song in self.playlist:
				if not prev == song[u'album']:
					prev = song[u'album']
					index = index + 1
				if song == focus_song:
					break
			if not current_index == index:
				self.Focus(index)
				self.Select(index,True)

	def __get_selected(self):
		index = self.GetNextItem(-1,wx.LIST_NEXT_ALL,wx.LIST_STATE_SELECTED)
		if not index == -1 and index < len(self.index_song):
			return self.index_song[index]
		else:
			return None


	def OnGetItemText(self,row,col):
		return ''

	def OnGetItemImage(self,row):
		if self.image_list_album_index.has_key(self.index_song[row][u'album']):
			return self.image_list_album_index[self.index_song[row][u'album']]
		else:
			self.__add_image_list(self.index_song[row])
		
	def OnClick(self,event=None):
		"""Focuses to selected item.
		"""
		index = self.GetNextItem(-1,wx.LIST_NEXT_ALL,wx.LIST_STATE_SELECTED)
		if not index == -1 and index < len(self.index_song):
			self.playlist.focused = self.index_song[index]

	def OnActivate(self,event=None):
		"""Activates a item.
		"""
		index = self.GetNextItem(-1,wx.LIST_NEXT_ALL,wx.LIST_STATE_SELECTED)
		if not index == -1 and index < len(self.index_song):
			self.index_song[index].play()



		
