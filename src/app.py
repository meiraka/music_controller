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
		if params.has_key('debug'):self.__debug = True
		else:self.__debug = False
		wx.App.__init__(self)

	def connect_default(self):
		thread.start_new_thread(self.__connect_default,())

	def __connect_default(self):
		if self.__debug: print 'connect to default host..'
		if self.client.connect():
			if self.__debug: print 'connected.'
			return
		else:
			if self.__debug: print 'fail.'
		for profile in self.client.config.profiles:
			if self.__debug: print 'connect to %s host..' % str(profile)
			if self.client.connect(profile):
				if self.__debug: print 'connected. (^-^)'
				break
			else:
				if self.__debug: print 'fail! (>_<)'

	def MainLoop(self):
		wx.App.MainLoop(self)

	def OnInit(self):
		""" Event func when app init
		"""

		if self.__debug: print 'init frame.'
		self.frame = frame.Frame(None,self.client,self.__debug)
		if self.__debug: print 'show frame.'
		self.frame.Show()
		if self.__debug: print 'frame viewing now.'
		self.client.start()
		self.connect_default()
		return True

	def exit(self):
		self.client.connection.close()
		
		
def run(**params):
	app = App(**params)
	app.MainLoop()
	
