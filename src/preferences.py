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
		self.connect = wx.Button(self,-1,u'connect')

		sizer = wx.GridBagSizer()
		params = dict(flag=wx.ALL,border=3)
		params_expand = dict(flag=wx.ALL|wx.EXPAND,border=3)
		sizer.Add(self.box,(0,0),(6,3),**params_expand)
		sizer.Add(self.add,(6,0),**params)
		sizer.Add(self.delete,(6,1),**params)
		sizer.Add(self.mpd,(0,3),**params)
		sizer.Add(self.host_label,(1,3),**params)
		sizer.Add(self.host,(1,4),(1,2),**params_expand)
		sizer.Add(self.port_label,(2,3),**params)
		sizer.Add(self.port,(2,4),(1,2),**params_expand)
		sizer.Add(self.connect,(6,5),**params)
		sizer.AddGrowableCol(2)
		sizer.AddGrowableCol(4)
		sizer.AddGrowableRow(5)
		border = wx.BoxSizer()
		border.Add(sizer,1,wx.ALL|wx.EXPAND,9)
	
		self.SetSizer(border)
		self.selected = None
		self.__update()
		self.box.Bind(wx.EVT_LISTBOX,self.OnBox)
		self.connect.Bind(wx.EVT_BUTTON,self.OnConnect)
		self.add.Bind(wx.EVT_BUTTON,self.OnNew)
	

	def update(self):
		wx.CallAfter(self.__update)

	def __update(self):
		profiles = self.config.profiles
		labels = [profile[0] for profile in profiles]
		self.box.Set(labels)
		if not self.host.GetValue():
			self.selected = self.connection.current
		index = labels.index(self.selected[0])
		self.box.SetSelection(index)
		self.host.SetValue(self.selected[1])
		self.port.SetValue(self.selected[2])
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
		self.__update()

	def OnBox(self,event):
		index = self.box.GetSelection()
		if not self.host.GetValue() == self.profiles[index][1]:
			self.selected = self.profiles[index]
			self.host.SetValue(self.selected[1])
			self.port.SetValue(self.selected[2])

	def OnText(self,event):
		obj = event.GetEventObject()
			

	def OnConnect(self,event):
		self.connection.close()
		self.connection.connect(self.selected)

	def OnNew(self,event):
		self.__new()
	

		

