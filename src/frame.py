import wx

import toolbar
import playlist


class Frame(wx.Frame):
	def __init__(self,parent,client,debug=False):
		""" generate main app window."""
		self.parent = parent
		self.client = client
		wx.Frame.__init__(self,parent,-1)
		self.toolbar = toolbar.Toolbar(self,self.client.playback)
		self.playlist = playlist.Playlist(self,self.client.playlist,debug)
