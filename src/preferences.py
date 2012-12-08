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
		
		self.mpd = wx.StaticText(self,-1,u'mpd')
		self.host_label = wx.StaticText(self,-1,u'host:')
		self.host = wx.TextCtrl(self,-1)
		self.port_label = wx.StaticText(self,-1,u'port:')
		self.port = wx.TextCtrl(self,-1)
		self.connect = wx.Button(self,-1,u'connect')

		sizer = wx.GridBagSizer()
		params = dict(flag=wx.ALL,border=3)
		params_expand = dict(flag=wx.ALL|wx.EXPAND,border=3)
		sizer.Add(self.box,(0,0),(7,1),**params_expand)
		sizer.Add(self.mpd,(0,1),**params)
		sizer.Add(self.host_label,(1,1),**params)
		sizer.Add(self.host,(1,2),(1,2),**params_expand)
		sizer.Add(self.port_label,(2,1),**params)
		sizer.Add(self.port,(2,2),(1,2),**params_expand)
		sizer.Add(self.connect,(6,3),**params)
		sizer.AddGrowableCol(2)
		sizer.AddGrowableRow(5)
		self.SetSizer(sizer)
