
import wx
import environment
import lyrics

frame = wx.Frame
if environment.userinterface.subwindow_small_frame:
	frame = wx.MiniFrame

class SongInfo(frame):
	def __init__(self,parent,songs):
		frame.__init__(self,None,-1,style=wx.CLOSE_BOX|wx.CAPTION)
		self.songs = songs
		self.lyrics_database = lyrics.Database()
		self.must_tags = [u'artist',u'title',u'album']
		must = wx.CollapsiblePane(self,-1,'General info:')
		sub = wx.CollapsiblePane(self,-1,'Extra info:')
		lyric = wx.CollapsiblePane(self,-1,'Lyric:')
		self.__mast_pane = must.GetPane()
		self.__sub_pane = sub.GetPane()
		self.__lyric_pane = lyric.GetPane()
		self.__text_style = wx.TE_READONLY
		self.__border = 3
		if environment.userinterface.fill_readonly_background:
			self.__text_style = wx.TE_READONLY|wx.BORDER_NONE
		if environment.userinterface.subitem_small_font:
			self.__border = 0
		self.title = wx.StaticText(self,-1,style=self.__text_style)
		self.title.SetMinSize((environment.userinterface.text_height*20,-1))
		self.description = wx.StaticText(self,-1,style=self.__text_style)
		must_labels = [wx.StaticText(self.__mast_pane,-1,tag+':') for tag in self.must_tags]
		self.must_values = [wx.TextCtrl(self.__mast_pane,-1,u'',style=self.__text_style) for tag in self.must_tags]
		self.must_values[0].SetFocus()
		self.lyric = wx.TextCtrl(self.__lyric_pane,-1,style=wx.TE_MULTILINE)
		self.lyric.SetMinSize((-1,environment.userinterface.text_height*8))
		if environment.userinterface.fill_readonly_background:
			for value in self.must_values+[self.title,self.description]:
				value.SetThemeEnabled(False)
				value.SetBackgroundColour(self.GetBackgroundColour())
		self.sub_tags = []
		m_sizer = wx.GridBagSizer()

		for index,tag in enumerate(self.must_tags):
			m_sizer.Add(must_labels[index],(index,0),flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL|wx.ALL,border=self.__border)
			m_sizer.Add(self.must_values[index],(index,1),flag=wx.EXPAND|wx.ALL,border=self.__border)
		m_sizer.AddGrowableCol(1)
		if environment.userinterface.subitem_small_font:
			small_font = self.title.GetFont()
			small_font.SetPointSize(int(1.0*small_font.GetPointSize()/1.2))
			smalls = [self.description,must,sub,lyric,self.lyric,
					self.__mast_pane,self.__sub_pane
					]+must_labels+self.must_values
			for i in smalls:
				i.SetFont(small_font)
			self.SetFont(small_font)
			self.__smallfont = small_font
			
		self.s_sizer = wx.GridBagSizer()
		self.__sub_pane.SetSizer(self.s_sizer)
		self.__mast_pane.SetSizer(m_sizer)
		m_sizer.SetSizeHints(self.__mast_pane)
		self.l_sizer = wx.BoxSizer(wx.VERTICAL)
		self.l_sizer.Add(self.lyric,1,wx.EXPAND|wx.ALL,border=6)
		self.__lyric_pane.SetSizer(self.l_sizer)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.title,0,wx.EXPAND|wx.ALL,border=3)
		sizer.Add(self.description,0,wx.EXPAND|wx.ALL,border=3)
		#sizer.Add(wx.StaticLine(self,-1,style=wx.BORDER_SIMPLE|wx.LI_HORIZONTAL),0,wx.EXPAND|wx.ALL,border=3)
		sizer.Add(must,0,wx.EXPAND)
		sizer.Add(sub,0,wx.EXPAND)
		sizer.Add(lyric,0,wx.EXPAND)
		self.SetSizer(sizer)
		self.show(songs[0])
		must.Expand()
		sub.Expand()
		self.Show()
		self.set_accelerator()

	def set_accelerator(self):
		id = wx.NewId()
		self.Bind(wx.EVT_MENU,self.close)
		table = [(wx.ACCEL_NORMAL,wx.WXK_ESCAPE,id)]
		self.SetAcceleratorTable(wx.AcceleratorTable(table))

	def close(self,event):
		self.Close()




	def show(self,song):
		self.title.SetLabel(song.format('%title% - %artist% %length%'))
		self.description.SetLabel(song.format('%album% %genre%'))
		for index,tag in enumerate(self.must_tags):
			if tag in song:
				self.must_values[index].SetValue(song[tag])
			else:
				self.must_values[index].SetValue(u'')
		self.__mast_pane.Layout()
		tags = [k for k,v in song.iteritems() if not self.must_tags.count(k)]
		for label in self.sub_tags:
			label.SetLabel('')
		for index,tag in enumerate(tags):
			if len(self.sub_tags)-1 <= index:
				self.sub_tags.append(
					(wx.StaticText(self.__sub_pane,-1,u''),
					wx.TextCtrl(self.__sub_pane,-1,u'',style=self.__text_style))
					)
				if environment.userinterface.fill_readonly_background:
					self.sub_tags[-1][1].SetBackgroundColour(self.GetBackgroundColour())
					self.sub_tags[-1][1].SetThemeEnabled(False)
				if environment.userinterface.subitem_small_font:
					self.sub_tags[-1][0].SetFont(self.__smallfont)
					self.sub_tags[-1][1].SetFont(self.__smallfont)
				self.s_sizer.Add(self.sub_tags[-1][0],(index,0),flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL|wx.ALL,border=self.__border)
				self.s_sizer.Add(self.sub_tags[-1][1],(index,1),flag=wx.EXPAND|wx.ALL,border=self.__border)
				if index == 0:
					self.s_sizer.AddGrowableCol(1)
			label,value = self.sub_tags[index]
			label.SetLabel(tag+':')
			value.SetValue(song[tag])
		self.SetTitle(u'%s info' % song.format(u'%title% - %artist%'))
		self.lyric.SetValue(self.lyrics_database[song])