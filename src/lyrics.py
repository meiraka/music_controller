#!/usr/bin/python

import wx
import environment
import client
import sqlite3
import urllib
import json
import thread
import re
import socket
"""
Draw lyric 
"""

class Database(client.Object):
	"""
	Downloads and manages lyric.
	"""
	UPDATING = 'updating'
	UPDATE = 'update'
	def __init__(self):
		""" init values and database."""
		self.__downloading = []
		self.download_auto = False
		self.download_background = False
		self.downloaders = dict(
			geci_me = True
			)

		""" init database.

		if not exists database, create table.
		"""
		sql_init = '''
		CREATE TABLE IF NOT EXISTS lyrics
		(
			artist TEXT,
			title TEXT,
			album TEXT,
			lyric TEXT
		);
		'''
		client.Object.__init__(self)
		connection = self.__get_connection()
		connection.execute(sql_init)
		
	def __get_connection(self):
		""" Returns database instance.

		must generate instance at everytime cause
		sqlite3 is not thread-safe.
		"""
		db = sqlite3.connect(environment.config_dir+'/lyrics')
		return db
		
	def __getitem__(self,song):
		""" Returns lyric.

		Arguments:
			song - client.Song object.

		Returns u'' if lyric is not found.
		if not found and self.download_auto,
		downloads and returns lyric.
		if download_background is True,
		run in another thread and raises UPDATING and UPDATE event.

		check self.downloading param to downloading lyric list.
		"""
		sql_search = '''
		SELECT lyric FROM lyrics WHERE
			artist=? and
			title=? and
			album=?
		'''
		connection = self.__get_connection()
		cursor = connection.cursor()
		cursor.execute(sql_search,
				(
				song.format('%artist%'),
				song.format('%title%'),
				song.format('%album%')
				)
			)
		lyric = cursor.fetchone()
		if lyric is None:
			if self.download_auto:
				if self.download_background:
					thread.start_new_thread(self.download,(song,))
				else:
					return self.download(song)
			return u''
		else:
			return lyric[0]
		
	def download(self,song):
		sql_write = '''
		INSERT OR REPLACE INTO lyrics
		(artist,title,album,lyric)
		VALUES(?, ?, ?, ?)
		'''
		self.__downloading.append(song)
		self.call(self.UPDATING)
		lyric = u''
		for label,is_download in self.downloaders.iteritems():
			if is_download:
				downloader = getattr(self,'download_from_'+label)
				try:
					lyric = downloader(song)
				except socket.error:
					pass
				if lyric:
					break
			else:
				pass
		connection = self.__get_connection()
		cursor = connection.cursor()
		cursor.execute(sql_write,
				(
				song.format('%artist%'),
				song.format('%title%'),
				song.format('%album%'),
				lyric
				)
			)
		connection.commit()
		del self.__downloading[self.__downloading.index(song)]
		self.call(self.UPDATE,lyric)
		return lyric

	def download_from_geci_me(self,song):
		title = song.format(u'%title%').replace(u'/',u' ').encode('utf8')
		artist = song.format(u'%artist%').replace(u'/',u' ').encode('utf8')
		query = urllib.quote(title+'/'+artist)
		json_text = urllib.urlopen('http://geci.me/api/lyric/'+query).read()
		json_parsed = json.loads(json_text.decode('utf8'))
		if u'result' in json_parsed and json_parsed[u'result']:
			lyric_page = urllib.urlopen(json_parsed[u'result'][0][u'lrc'])
			lyric_encode = lyric_page.info()
			lyric = lyric_page.read().decode('utf8')
			return lyric
		return u''

	downloading = property(lambda self:self.__downloading)

class DatabaseWithConfig(Database):
	""" extends Database class with config."""
	def __init__(self,client):
		self.client = client
		Database.__init__(self)

	def download(self,song):
		""" download lyric.

		if turn off by config ,
		does not download or does not use some api.
		"""
		if self.client.config.lyrics_download:
			downloaders = {}
			for label,isd in self.downloaders.iteritems():
				attr = u'lyrics_api_'+label
				downloaders[label] = getattr(self.client.config,attr)
			self.downloaders = downloaders
			Database.download(self,song)
		else:
			pass

class LyricView(wx.Panel):
	"""
	Draw lyric.
	"""
	def __init__(self,parent,client):
		self.client = client
		self.parent = parent
		self.bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
		self.fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
		self.hbg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
		self.hfg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
		self.database = DatabaseWithConfig(client)
		self.database.download_auto = True
		self.database.download_background = True
		self.__time = 0
		self.__time_msec = 0.0
		self.__index = 0
		self.__offset = 0
		self.__song = None
		self.__raw_lyric = u''
		self.__lyric = []
		self.__update_interval = 100
		wx.Panel.__init__(self,parent,-1)
		#self.SetBackgroundColour(self.bg)
		self.font = environment.userinterface.font
		self.timer = wx.Timer(self.parent,-1)
		wx.EVT_TIMER(self.parent,-1,self.__update)
		self.timer.Start(self.__update_interval)
		#self.parent.Bind(wx.EVT_ERASE_BACKGROUND,self.update)
		self.client.playback.bind(self.client.playback.UPDATE_PLAYING,self.update_data)
		self.database.bind(self.database.UPDATING,self.update)
		self.database.bind(self.database.UPDATE,self.decode_raw_lyric)
		self.Bind(wx.EVT_RIGHT_UP,self.OnRightClick)
		self.__update()

	def update_time(self):
		status = self.client.playback.status
		if status and u'time' in status:
			time = status[u'time']
			time = int(time.split(u':')[0])
			if not self.__time == time:
				self.__time = time
				self.__time_msec = 0.0

	def update_data(self):
		""" update lyric data."""
		self.update_time()
		status = self.client.playback.status
		if status and u'song' in status:
			song_id = int(status[u'song'])
			if len(self.client.playlist) > song_id:
				song = self.client.playlist[song_id]
				if not self.__song == song:
					self.__song = song
					self.decode_raw_lyric(self.database[song])

	def decode_raw_lyric(self,lyric):
		""" convert raw LRC lyric text to list."""
		self.__offset = 0.0
		self.__raw_lyric = lyric
		self.__lyric = []
		result = []
		if not lyric:
			return
		for line in lyric.split(u'\n'):
			for i in self.__decode_line(line):
				result.append(i)
		result.sort()
		self.__lyric = result

	def __decode_line(self,line):
		""" convert raw LRC lyric line to tuple."""
		def convert_sec(time):
			sec = float(time[0])*60.0+float(time[1])
			if len(time) > 2:
				sec = sec + float(time[2])*0.01
			return sec

		matchers = [	'\\[(\\d+):(\\d+)\\.(\\d+)\\]',
				'\\[(\\d+):(\\d+):(\\d+)\\]',
				'\\[(\\d+):(\\d+)\\]']
		compiled_matcher = [re.compile(i) for i in matchers]

		for p in compiled_matcher:
			times = p.findall(line)
			if times:
				splitter = times[-1][-1]+u']'
				lyric = line.rsplit(splitter,1)[-1]
				return [(convert_sec(mss),lyric) for mss in times]
		return []

	def OnPaint(self,event):
		self.__update(event)

	def update(self):
		""" update lyric file at main thread."""
		wx.CallAfter(self.__update)

	def __update(self,event=None):
		""" update lyric file"""
		dc = wx.ClientDC(self)
		if environment.userinterface.draw_double_buffered:
			dc = wx.BufferedDC(dc)
		dc.SetFont(self.font)
		dc.SetBackground(wx.Brush(self.bg))
		dc.SetPen(wx.Pen(self.bg))
		dc.SetBrush(wx.Brush(self.bg))
		dc.SetTextForeground(self.fg)
		dc.DrawRectangle(0,0,*self.GetSize())
		x,y = self.GetPosition()
		w,h = self.GetSize()
		if self.__lyric:
			self.draw(dc,(x,y,w,h))
		else:
			if self.database.downloading.count(self.__song):
				title = u'Searching lyric...'
			else:
				title = u'Lyrics not found.'
			x = (w - dc.GetTextExtent(title)[0])/2
			y = h / 2
			dc.DrawText(title,x,y)

	def draw(self,dc,rect):
		self.update_time()

		dc.SetPen(wx.Pen(self.hbg))
		dc.SetBrush(wx.Brush(self.hbg))

		x,y,w,h = rect
		
		# calc offset
		last_time = 0.0
		text_height = environment.userinterface.text_height
		height = text_height * 3 / 2
		interval = float(self.__update_interval)/1000.0
		current_line = -1
		for index,(time,line) in enumerate(self.__lyric):
			if last_time < self.__time < time:
				# we draw *guess_count* times to get next line pos
				guess_count = (time-self.__time-self.__time_msec)/(float(self.__update_interval)/1000)
				current_line = index-1
				if guess_count>0:
					add_offset = (index*height-self.__offset)/guess_count
					if add_offset > height:
						# too far from current pos, jump.
						self.__offset = (index)*height
					else:
						self.__offset = self.__offset + add_offset 
				break
			else:
				last_time = time
		self.__time_msec = self.__time_msec + interval
		try:
			pos =  self.GetSize()[0] / height / 2
			for index,(time,line) in enumerate(self.__lyric):
				# do not draw line text is empty.
				if line.strip():
					if index == current_line:
						y = (index+pos)*height-int(self.__offset)
						dc.DrawRectangle(0,y,self.GetSize()[0],height)
						dc.SetTextForeground(self.hfg)
					else:
						dc.SetTextForeground(self.fg)
					draw_y = (height-text_height)/2+(index+pos)*height-int(self.__offset)
					if -height < draw_y < self.GetSize()[1]:
						dc.DrawText(line,12,draw_y)
		except Exception,err:
			print err

	def OnRightClick(self,event):
		self.PopupMenu(Menu(self,self.__song))

class Menu(wx.Menu):
	def __init__(self,parent,song):
		wx.Menu.__init__(self)
		self.parent = parent
		self.song = song
		items = [u'edit']
		self.__items = dict([(item,wx.NewId()) for item in items])
		for item in items:
			label = item.replace(u'_',' ')
			self.Append(self.__items[item],label,label)
			self.Bind(wx.EVT_MENU,getattr(self,item+'_item'),id=self.__items[item])

	def edit_item(self,event):
		editor = Editor(self.parent,self.parent.client,self.song)
		editor.Show()
		
class Editor(wx.Frame):
	TOOLBAR_TOGGLE = 'toggle'
	TOOLBAR_RADIO = 'radio'
	TOOLBAR_NORMAL = 'normal'
	def __init__(self,parent,client,song):
		self.client = client
		self.parent = parent
		self.song = song
		self.db = Database()
		toolbar_item = [
			(self.TOOLBAR_RADIO,'text',['',wx.ART_GO_HOME]),
			(self.TOOLBAR_RADIO,'timetag',['',wx.ART_GO_HOME]),
			(self.TOOLBAR_TOGGLE,'single',['',wx.ART_GO_HOME]),
			]
		self.toolbar_item = [(wx.NewId(),t,l,i) for t,l,i in toolbar_item]
		wx.Frame.__init__(self,None,-1)
		toolbar_style = wx.TB_TEXT
		if environment.userinterface.toolbar_icon_horizontal:
			toolbar_style = wx.TB_HORZ_TEXT
		self.__tool = self.CreateToolBar(toolbar_style)
		for id,button_type,label,icons in self.toolbar_item:
			bmp = None
			for icon in icons:
				bmp = wx.ArtProvider.GetBitmap(icon)
				if bmp.IsOk() and not bmp.GetSize() == (-1,-1):
					break
			if environment.userinterface.toolbar_toggle:
				if button_type == self.TOOLBAR_TOGGLE:
					self.__tool.AddCheckLabelTool(id,label,bmp)
				elif button_type == self.TOOLBAR_RADIO:
					self.__tool.AddRadioLabelTool(id,label,bmp)
				else:
					self.__tool.AddLabelTool(id,label,bmp)
			else:
				self.__tool.AddLabelTool(id,label,bmp)
		self.text = wx.TextCtrl(self,-1,self.db[song],style=wx.TE_MULTILINE)
