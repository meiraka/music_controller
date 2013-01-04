
import wx

class SongDialog(wx.Frame):
	def __init__(self,parent,songs):
		wx.Frame.__init__(self,None,-1)
		self.songs = songs
		self.must_tags = [u'artist',u'title',u'album']
		must = wx.CollapsiblePane(self,-1,'')
		sub = wx.CollapsiblePane(self,-1,'')
		must.Expand()
		sub.Expand()
		self.__mast_pane = must.GetPane()
		self.__sub_pane = sub.GetPane()
		self.__text_style = wx.TE_READONLY|wx.BORDER_NONE|wx.TE_MULTILINE|wx.TE_DONTWRAP
		must_labels = [wx.StaticText(self.__mast_pane,-1,tag+':') for tag in self.must_tags]
		self.must_values = [wx.TextCtrl(self.__mast_pane,-1,u'',style=self.__text_style) for tag in self.must_tags]
		for value in self.must_values:
			value.SetBackgroundColour(self.GetBackgroundColour())
		self.sub_tags = []
		m_sizer = wx.GridBagSizer()
		for index,tag in enumerate(self.must_tags):
			m_sizer.Add(must_labels[index],(index,0),flag=wx.ALIGN_RIGHT)
			m_sizer.Add(self.must_values[index],(index,1),flag=wx.EXPAND)
		m_sizer.AddGrowableCol(1)
		self.s_sizer = wx.GridBagSizer()
		self.__sub_pane.SetSizer(self.s_sizer)
		self.__mast_pane.SetSizer(m_sizer)
		m_sizer.SetSizeHints(self.__mast_pane)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(must,0,wx.EXPAND)
		sizer.Add(sub,0,wx.EXPAND)
		self.SetSizer(sizer)
		self.show(songs[0])
		self.Show()

	def show(self,song):
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
				self.sub_tags[-1][1].SetBackgroundColour(self.GetBackgroundColour())
				self.s_sizer.Add(self.sub_tags[-1][0],(index,0),flag=wx.ALIGN_RIGHT)
				self.s_sizer.Add(self.sub_tags[-1][1],(index,1),flag=wx.EXPAND)
				if index == 0:
					self.s_sizer.AddGrowableCol(1)
			label,value = self.sub_tags[index]
			label.SetLabel(tag+':')
			value.SetValue(song[tag])
		self.SetTitle(u'%s info' % song.format(u'%title% - %artist%'))
