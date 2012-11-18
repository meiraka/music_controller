import wx

import client
import frame

class App(wx.App):
	"""
	this app class.
	"""
	def __init__(self):
		"""init this app"""
		wx.App.__init__(self)
		self.client = None
		pass

	def connect_default(self):
		self.client.connect()

	def OnInit(self):
		""" Event func when app init
		"""
		self.client = client.Client()
		self.connect_default()
		self.frame = frame.Frame(None,self.client)
		self.frame.Show()
		return True

	def exit(self):
		self.client.connection.close()
		
		
def run(**params):
	app = App()
	for attr, value in params.iteritems():
		setattr(app,attr,value)
	app.MainLoop()
	
