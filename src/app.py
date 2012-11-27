import wx

import client
import frame
import environment
import thread

class App(wx.App):
	"""
	this app class.
	"""
	def __init__(self,**params):
		"""init this app"""
		self.config_dir = environment.config_dir
		self.client = client.Client(self.config_dir)
		self.client.start()
		if params.has_key('debug'):self.__debug = True
		else:self.__debug = False
		wx.App.__init__(self)

	def connect_default(self):
		thread.start_new_thread(self.__connect_default,())

	def __connect_default(self):
		for profile in self.client.config.profiles:
			if self.client.connect(profile):
				break

	def MainLoop(self):
		wx.App.MainLoop(self)

	def OnInit(self):
		""" Event func when app init
		"""

		self.connect_default()
		self.frame = frame.Frame(None,self.client,self.__debug)
		self.frame.Show()
		return True

	def exit(self):
		self.client.connection.close()
		
		
def run(**params):
	app = App(**params)
	app.MainLoop()
	
