#!/usr/bin/python

import wx
import environment
import client
import sqlite3
import urllib
import json
import thread
import re
"""
Draw lyric 
"""

class LyricDatabase(client.Object):
	"""
	Downloads and manages lyric.
	"""
	UPDATE = 'update'
	def __init__(self):
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
			thread.start_new_thread(self.download,(song,))
			return ''
		else:
			return lyric[0]
		
	def download(self,song,index=0):
		sql_write = '''
		INSERT OR REPLACE INTO lyrics
		(artist,title,album,lyric)
		VALUES(?, ?, ?, ?)
		'''
		title = song.format(u'%title%').replace(u'/',u' ').encode('utf8')
		artist = song.format(u'%artist%').replace(u'/',u' ').encode('utf8')
		query = urllib.quote(title+'/'+artist)
		json_text = urllib.urlopen('http://geci.me/api/lyric/'+query).read()
		json_parsed = json.loads(json_text.decode('utf8'))
		if u'result' in json_parsed and not json_parsed[u'result']:
			query = urllib.quote(title)
			json_text = urllib.urlopen('http://geci.me/api/lyric/'+query).read()
			json_parsed = json.loads(json_text.decode('utf8'))

		lyric = u''
		if u'result' in json_parsed and json_parsed[u'result']:
			lyric_page = urllib.urlopen(json_parsed[u'result'][0][u'lrc'])
			lyric_encode = lyric_page.info()
			lyric = lyric_page.read().decode('utf8')
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
		if not lyric:
			print 'not found'
			print json_text
		connection.commit()
		self.call(self.UPDATE,lyric)



class Lyric(wx.Panel):
	def __init__(self,parent,client):
		self.client = client
		self.parent = parent
		self.bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
		self.fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
		self.hbg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
		self.hfg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
		self.database = LyricDatabase()
		self.__time = 0
		self.__time_msec = 0.0
		self.__index = 0
		self.__offset = 0
		self.__song = None
		self.__raw_lyric = u''
		self.__lyric = []
		self.__update_interval = 100
		wx.Panel.__init__(self,parent,-1)
		self.SetBackgroundColour(self.bg)
		self.font = environment.userinterface.font
		self.timer = wx.Timer(self.parent,-1)
		wx.EVT_TIMER(self.parent,-1,self.update)
		self.timer.Start(self.__update_interval)
		#self.parent.Bind(wx.EVT_ERASE_BACKGROUND,self.update)
		self.client.playback.bind(self.client.playback.UPDATE_PLAYING,self.update_data)
		self.database.bind(self.database.UPDATE,self.decode_raw_lyric)
		self.update()

	def update_time(self):
		status = self.client.playback.status
		if status and u'time' in status:
			time = status[u'time']
			time = int(time.split(u':')[0])
			if not self.__time == time:
				self.__time = time
				self.__time_msec = 0.0

	def update_data(self):
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
		self.__offset = 0.0
		self.__raw_lyric = lyric
		self.__lyric = []
		result = []
		for line in lyric.split(u'\n'):
			for i in self.__decode_line(line):
				result.append(i)
		result.sort()
		self.__lyric = result

	def __decode_line(self,line):
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
		self.update(event)

	def update(self,event=None):
		dc = wx.ClientDC(self)
		dc.BeginDrawing()
		try:
			dc = event.GetDC()
		except:
			pass
		dc.SetFont(self.font)
		x,y = self.GetPosition()
		w,h = self.GetSize()
		self.draw(dc,(x,y,w,h))
		dc.EndDrawing()

	def draw(self,dc,rect):
		self.update_time()
		#dc = wx.GCDC(dc)
		dc.Clear()
		dc.SetBackground(wx.Brush(self.bg))
		dc.SetPen(wx.Pen(self.bg))
		dc.SetBrush(wx.Brush(self.bg))
		dc.SetTextForeground(self.fg)
		dc.DrawRectangle(0,0,*self.GetSize())
		dc.SetPen(wx.Pen(self.hbg))
		dc.SetBrush(wx.Brush(self.hbg))

		x,y,w,h = rect
		
		# calc offset
		last_time = 0.0
		height = environment.userinterface.text_height * 2
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
			#dc.DrawText(self.__raw_lyric,0,0)
			pos =  self.GetSize()[0] / height / 2
			for index,(time,line) in enumerate(self.__lyric):
				if index == current_line:
					y = (index+pos)*height-int(self.__offset)
					dc.DrawRectangle(0,y,self.GetSize()[0],height)
					dc.SetTextForeground(self.hfg)
				else:
					dc.SetTextForeground(self.fg)
				draw_y = height/4+(index+pos)*height-int(self.__offset)
				if -height < draw_y < self.GetSize()[1]:
					dc.DrawText(line,12,draw_y)
		except Exception,err:
			print err
		
	
