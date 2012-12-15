import wx

class Frame(wx.Frame):
	def __init__(self,parent,client,debug=False):
		wx.Frame.__init__(self,parent,-1)
		self.client = client
		self.connection = Connection(self,client.connection,client.config)


class Connection(wx.Panel):
	def __init__(self,parent,connection,config):
		wx.Panel.__init__(self,parent,-1)
		self.connection = connection
		self.config = config

		self.box = wx.ListBox(self,-1)
		self.add = wx.Button(self,-1,'+',style=wx.BU_EXACTFIT)
		self.delete = wx.Button(self,-1,'-',style=wx.BU_EXACTFIT)
		
		self.mpd = wx.StaticText(self,-1,u'mpd')
		self.host_label = wx.StaticText(self,-1,u'host:')
		self.host = wx.TextCtrl(self,-1)
		self.port_label = wx.StaticText(self,-1,u'port:')
		self.port = wx.TextCtrl(self,-1)
		self.use_password = wx.CheckBox(self,-1,u'password:')
		self.password = wx.TextCtrl(self,-1)
		self.connect = wx.Button(self,-1,u'connect')
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
		border = wx.BoxSizer()
		border.Add(sizer,1,wx.ALL|wx.EXPAND,9)
	
		self.SetSizer(border)
		self.selected = None
		self.selected_index = -1
		self.__update()
		self.box.Bind(wx.EVT_LISTBOX,self.OnBox)
		self.connect.Bind(wx.EVT_BUTTON,self.OnConnect)
		self.add.Bind(wx.EVT_BUTTON,self.OnNew)
		self.delete.Bind(wx.EVT_BUTTON,self.OnDel)
		self.Bind(wx.EVT_TEXT,self.OnText)
		self.Bind(wx.EVT_CLOSE,self.OnClose)
	

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
	
	def OnClose(self,event):
		self.Hide()
		

