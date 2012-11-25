import wx

import toolbar
import playlist
import info
import albumlist


class Frame(wx.Frame):
	def __init__(self,parent,client,debug=False):
		""" generate main app window."""
		self.parent = parent
		self.client = client
		wx.Frame.__init__(self,parent,-1)
		self.SetSize((640,480))

		self.toolbar = toolbar.Toolbar(self,self.client.playback)
		self.playlist = playlist.Playlist(self,self.client.playlist,debug)
		self.info = info.Info(self,self.client,debug)
		self.albumlist = albumlist.AlbumList(self,self.client.playlist,debug)

		self.sizer = wx.BoxSizer()
		s = wx.BoxSizer(wx.VERTICAL)
		s.Add(self.info,0,wx.EXPAND)
		s.Add(self.playlist,1,flag=wx.EXPAND)
		self.sizer.Add(s,1,flag=wx.EXPAND)
		self.sizer.Add(self.albumlist,0,flag=wx.EXPAND)
		self.SetSizer(self.sizer)
		
