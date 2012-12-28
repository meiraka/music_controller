import wx

import client
import frame
import environment
import thread
import time
import gettext

NAME = 'MusicController'

class App(wx.App):
	"""
	this app class.
	"""
	def __init__(self,**params):
		"""init this app"""
		self.config_dir = environment.config_dir
		self.client = client.Client(self.config_dir)
		self.client.connection.bind(
			self.client.connection.CLOSE_UNEXPECT,self.reconnect)
		self.client.connection.bind(
			self.client.connection.CONNECT,self.connected)
		if params.has_key('debug'):self.__debug = True
		else:self.__debug = False
		self.__connected = None
		gettext.install('music-controller',unicode=1)
		wx.App.__init__(self)

	def connect_default(self):
		thread.start_new_thread(self.__connect_default,())

	def __connect_default(self):
		if self.__debug: print 'connect to default host..'
		if self.client.connect():
			if self.__debug: print 'connected.'
		else:
			if self.__debug: print 'fail.'
			for profile in self.client.config.profiles:
				if self.__debug: print 'connect to %s host..' % str(profile)
				if self.client.connect(profile):
					self.__connected = profile
					if self.__debug: print 'connected. (^-^)'
					break
				else:
					if self.__debug: print 'fail! (>_<)'
			else:
				wx.CallAfter(self.frame.show_connection)
		self.client.start()

	def reconnect(self):
		thread.start_new_thread(self.__reconnect,())

	def __reconnect(self):
		if self.__debug: print 'reconnecting...',
		time.sleep(3)
		if self.client.connect():
			if self.__debug: print ' done.'
			pass
		else:
			if self.__debug: print ' fail.'
			wx.CallAfter(self.frame.show_connection)

	def connected(self):
		wx.CallAfter(self.frame.show_playlist)

	def MainLoop(self):
		wx.App.MainLoop(self)

	def OnInit(self):
		""" Event func when app init
		"""
		self.SetAppName(NAME)
		if self.__debug: print 'init frame.'
		self.frame = frame.Frame(None,self.client,self.__debug)
		if environment.gui == 'mac':
			self.frame.Bind(wx.EVT_CLOSE,self.OnClose)
			self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)
		if self.__debug: print 'show frame.'
		self.frame.Show()
		if self.__debug: print 'frame viewing now.'
		self.connect_default()
		return True

	def OnClose(self,event):
		self.frame.Hide()

	def OnActivate(self,event):
		self.frame.Show()

	def MacReopenApp(self):
		self.frame.Show()

	def exit(self):
		self.client.connection.close()
		
		
def run(**params):
	app = App(**params)
	app.MainLoop()
	
