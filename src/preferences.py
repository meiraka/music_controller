import wx
import environment

class App(wx.Frame):
	"""
	Application preferences window.
	"""
	def __init__(self,parent,client,debug=False):
		wx.Frame.__init__(self,parent,-1)
		self.client = client
		self.__windows = [
			(u'Connection',Connection,wx.ART_GO_FORWARD),
			(u'Lyrics',Lyrics,wx.ART_GO_FORWARD)
			]

		self.__ids = {}
		self.__indexes = []

		# toolbar
		toolbar_style = wx.TB_TEXT
		if environment.userinterface.toolbar_icon_horizontal:
			toolbar_style = wx.TB_HORZ_TEXT
		self.__tool = self.CreateToolBar(toolbar_style)
		for label,c,icon in self.__windows:
			id = wx.NewId()
			self.__ids[label] = id
			self.__indexes.append(id)
			bmp = wx.ArtProvider.GetBitmap(icon)
			if environment.userinterface.toolbar_toggle:
				self.__tool.AddRadioLabelTool(id,label,bmp)
			else:
				self.__tool.AddLabelTool(id,label,bmp)
		self.__tool.Bind(wx.EVT_TOOL,self.OnTool)
		self.__tool.Realize()

		self.__sizers = [config_class(self,client) for label,config_class,i in self.__windows]
		sizer = wx.BoxSizer()
		for config_sizer in self.__sizers:
			config_sizer.Hide()
			sizer.Add(config_sizer,1,wx.EXPAND)
		self.__sizers[0].Show()
		self.SetSizer(sizer)
		self.set_accelerator()

	def set_accelerator(self):
		id = wx.NewId()
		self.Bind(wx.EVT_MENU,self.close)
		table = [(wx.ACCEL_NORMAL,wx.WXK_ESCAPE,id)]
		self.SetAcceleratorTable(wx.AcceleratorTable(table))

	def close(self,event):
		self.Hide()

	def OnTool(self,event):
		click_id = event.GetId()
		click_index = self.__indexes.index(click_id)
		for label,id in self.__ids.iteritems():
			if environment.userinterface.toolbar_toggle:
				self.__tool.ToggleTool(id,id==click_id)
		for index,sizer in enumerate(self.__sizers):
			if index == click_index:
				sizer.Show()
			else:
				sizer.Hide()

class Lyrics(wx.BoxSizer):
	def __init__(self,parent,client):
		self.parent = parent
		self.client = client
		wx.BoxSizer.__init__(self,wx.VERTICAL)
		self.__downloads_api = [
			u'geci.me'
			]
		self.__is_download = wx.CheckBox(parent,-1,u'Download lyric')
		self.__is_download.Bind(wx.EVT_CHECKBOX,self.click_is_download)
		self.__is_downloads_api = [
			wx.CheckBox(parent,-1,u'Download from '+api) for api in self.__downloads_api
			]
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.__is_download,0,wx.ALL,border=3)
		downloads_sizer = wx.BoxSizer(wx.VERTICAL)
		for download_api in self.__is_downloads_api:
			downloads_sizer.Add(download_api,0,wx.ALL,border=3)
			download_api.Bind(wx.EVT_CHECKBOX,self.click_is_download_api)
		sizer.Add(downloads_sizer,0,wx.LEFT|wx.RIGHT,border=15)
		self.Add(sizer,0,wx.ALL,border=6)
		self.load_config()

	def load_config(self):
		download = self.client.config.lyrics_download
		self.__is_download.SetValue(download)
		for download_api in self.__is_downloads_api:
			download_api.Enable(download)
		for index,api in enumerate(self.__downloads_api):
			attr = 'lyrics_api_' + api.replace(u'.',u'_')
			use_api = getattr(self.client.config,attr)
			self.__is_downloads_api[index].SetValue(use_api)

	def click_is_download(self,event):
		download = self.__is_download.GetValue()
		self.client.config.lyrics_download = download
		self.load_config()

	def click_is_download_api(self,event):
		obj = event.GetEventObject()
		index = self.__is_downloads_api.index(obj)
		label = self.__downloads_api[index]
		attr = 'lyrics_api_' + label.replace(u'.',u'_')
		setattr(self.client.config,attr,obj.GetValue())

	def Hide(self):
		self.ShowItems(False)
		self.parent.Layout()

	def Show(self):
		self.ShowItems(True)
		self.parent.Layout()



class Connection(wx.BoxSizer):
	def __init__(self,parent,client):
		wx.BoxSizer.__init__(self)
		self.parent = parent
		self.connection = client.connection
		self.config = client.config

		self.box = wx.ListBox(parent,-1)
		self.add = wx.Button(parent,-1,'+',style=wx.BU_EXACTFIT)
		self.delete = wx.Button(parent,-1,'-',style=wx.BU_EXACTFIT)
		
		self.mpd = wx.StaticText(parent,-1,u'mpd')
		self.host_label = wx.StaticText(parent,-1,u'host:')
		self.host = wx.TextCtrl(parent,-1)
		self.host.SetFocus()
		self.port_label = wx.StaticText(parent,-1,u'port:')
		self.port = wx.TextCtrl(parent,-1)
		self.use_password = wx.CheckBox(parent,-1,u'password:')
		self.password = wx.TextCtrl(parent,-1)
		self.connect = wx.Button(parent,-1,u'connect')
		sizer = wx.GridBagSizer()
		params = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL,border=3)
		params_label = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT,border=3)
		params_expand = dict(flag=wx.ALL|wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL,border=3)
		sizer.Add(self.box,(0,0),(6,3),**params_expand)
		sizer.Add(self.add,(6,0),**params)
		sizer.Add(self.delete,(6,1),**params)
		sizer.Add(self.mpd,(0,3),**params)
		sizer.Add(self.host_label,(1,3),**params_label)
		sizer.Add(self.host,(1,4),(1,2),**params_expand)
		sizer.Add(self.port_label,(2,3),**params_label)
		sizer.Add(self.port,(2,4),(1,2),**params_expand)
		sizer.Add(self.use_password,(3,3),**params_label)
		sizer.Add(self.password,(3,4),(1,2),**params_expand)
		
		sizer.Add(self.connect,(6,5),**params)
		sizer.AddGrowableCol(4)
		sizer.AddGrowableRow(5)
		self.sizer = wx.BoxSizer()
		self.Add(sizer,1,wx.ALL|wx.EXPAND,9)
	
		self.selected = None
		self.selected_index = -1
		self.__update()
		self.box.Bind(wx.EVT_LISTBOX,self.OnBox)
		self.connect.Bind(wx.EVT_BUTTON,self.OnConnect)
		self.add.Bind(wx.EVT_BUTTON,self.OnNew)
		self.delete.Bind(wx.EVT_BUTTON,self.OnDel)
		texts = [self.host,self.port,self.password]
		for text in texts:
			text.Bind(wx.EVT_TEXT,self.OnText)
		self.Layout()

	def Hide(self):
		self.ShowItems(False)
		self.parent.Layout()

	def Show(self):
		self.ShowItems(True)
		self.parent.Layout()

	def update(self):
		wx.CallAfter(self.__update)

	def __set_text(self):
		self.host.SetValue(self.selected[1])
		self.port.SetValue(self.selected[2])
		self.use_password.SetValue(self.selected[3])
		self.password.Enable(self.selected[3])
		self.password.SetValue(self.selected[4])

	def __update(self):
		profiles = self.config.profiles
		labels = [profile[0] for profile in profiles]
		self.box.Set(labels)
		if not self.host.GetValue():
			self.selected = self.connection.current
			if self.selected:
				self.selected_index = labels.index(self.selected[0])
		if len(labels) <= self.selected_index:
			self.selected_index = len(labels) - 1
			self.selected = profiles[self.selected_index]
		if not len(labels) == 0 and not self.selected_index == -1:
			self.box.SetSelection(self.selected_index)
			self.__set_text()
		self.profiles = profiles

	def __new(self):
		profiles = self.config.profiles
		labels = [profile[0] for profile in profiles]
		new_label = u'new'
		if labels.count(new_label):
			index = 1
			while True:
				if not labels.count(new_label+ ' (%i)' % index):
					new_label = new_label+ ' (%i)' % index
					break
				else:
					index = index + 1
		new_profile = [new_label,u'localhost',u'6600',False,u'']
		profiles.append(new_profile)
		self.config.profiles = profiles
		self.selected = new_profile
		self.selected_index = len(profiles) - 1
		self.delete.Enable()
		self.__update()

	def __del(self,index):
		profiles = self.config.profiles
		del profiles[index]
		self.config.profiles = profiles
		self.__update()
		if len(profiles) <= 1:
			self.delete.Disable()

	def OnBox(self,event):
		index = self.box.GetSelection()
		if not index == self.selected_index:
			self.selected = self.profiles[index]
			self.selected_index = index
			self.__set_text()

	def OnText(self,event):
		obj = event.GetEventObject()
		index = {self.host:1,self.port:2,self.password:4}
		profiles = self.config.profiles
		profiles[self.selected_index][index[obj]] = obj.GetValue()
		self.selected = profiles[self.selected_index]
		self.config.profiles = profiles

	def OnConnect(self,event):
		self.connection.close()
		self.connection.connect(self.selected)

	def OnNew(self,event):
		self.__new()

	def OnDel(self,event):
		index = self.box.GetSelection()
		self.__del(index)


