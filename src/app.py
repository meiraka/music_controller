import wx

from common import client
from common import environment

import frame
import thread
import time
import gettext

NAME = 'MusicController'

"""
Main Application.
"""
class App(wx.App):
	""" Initializes Application.

	loads config directory and installs language.
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
		""" Connects to default host and runs mpd monitor daemon in background."""
		thread.start_new_thread(self.__connect_default,())

	def __connect_default(self):
		""" Connects to default host and runs mpd monitor daemon."""
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
		# run monitor daemon
		self.client.start()

	def reconnect(self):
		""" Reconnects to previously connected host in background."""
		thread.start_new_thread(self.__reconnect,())

	def __reconnect(self):
		""" Reconnects to previously connected host."""
		if self.__debug: print 'reconnecting...',
		time.sleep(3)
		if self.client.connect():
			if self.__debug: print ' done.'
			pass
		else:
			if self.__debug: print ' fail.'
			wx.CallAfter(self.frame.show_connection)

	def connected(self):
		""" Hides connection panel."""
		wx.CallAfter(self.frame.show_not_connection)

	def MainLoop(self):
		""" Runs Application mainloop."""
		wx.App.MainLoop(self)

	def OnInit(self):
		""" Event func when app init
		"""
		self.SetAppName(NAME)
		if self.__debug: print 'init frame.'
		self.frame = frame.Frame(None,self.client,self.__debug)
		if environment.userinterface.style == 'mac':
			self.frame.Bind(wx.EVT_CLOSE,self.OnClose)
			self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)
		if self.__debug: print 'show frame.'
		self.frame.Show()
		if self.__debug: print 'frame viewing now.'
		self.connect_default()
		return True

	def OnClose(self,event):
		""" catch window close event.
		close event is raises in Mac environment only. Hide window.
		"""
		self.frame.Hide()

	def OnActivate(self,event):
		""" catch application activate event.
		application activate event is raises in Mac environment only.
		Show window.
		"""
		self.frame.Show()

	def MacReopenApp(self):
		""" Show window.
		this function is called when App icon was clicked in Mac environment.
		"""
		self.frame.Show()

	def exit(self):
		""" Close connection."""
		self.client.connection.close()
		

"""
Runs Application.
"""		
def run(**params):
	wx.Log_EnableLogging(False)
	app = App(**params)
	app.MainLoop()
	
