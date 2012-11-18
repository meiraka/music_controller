import wx

import client
import frame
import environment

class App(wx.App):
	"""
	this app class.
	"""
	def __init__(self,**params):
		"""init this app"""
		self.config_dir = environment.config_dir
		self.client = client.Client(self.config_dir)
		wx.App.__init__(self)

	def connect_default(self):
		self.client.config.profiles = [[u'server',u'192.168.0.4',u'6600',False,u'']]
		self.client.connect()

	def MainLoop(self):
		wx.App.MainLoop(self)

	def OnInit(self):
		""" Event func when app init
		"""

		self.connect_default()
		self.frame = frame.Frame(None,self.client)
		self.frame.Show()
		return True

	def exit(self):
		self.client.connection.close()
		
		
def run(**params):
	app = App(**params)
	app.MainLoop()
	
