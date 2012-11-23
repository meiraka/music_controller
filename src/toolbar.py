#!/usr/bin/python
import wx

class MacToolbar(object):
	def __init__(self,parent,playback):
		self.__tool = parent.CreateToolBar(wx.TB_TEXT)
		self.playback = playback
		#size = (19,19)
		size = None
		#self.__tool.SetToolBitmapSize(size)
		icons = dict(
			previous=wx.ArtProvider.GetBitmap(wx.ART_GOTO_FIRST,size=size),
			play=wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD,size=size),
			pause=wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD,size=size),
			next=wx.ArtProvider.GetBitmap(wx.ART_GOTO_LAST,size=size)
			)
		self.icons = dict([(k, (v, wx.NewId() ) ) for k,v in icons.iteritems()])
		for k,(icon,id) in self.icons.iteritems():
			self.__tool.AddLabelTool(id,k,icon)
		self.__tool.Realize()
		self.__tool.Bind(wx.EVT_TOOL,self.OnTool)

	def OnTool(self,event):
		event_id = event.GetId()
		for func_name,(icon,id) in self.icons.iteritems():
			if event_id == id:
				getattr(self.playback,func_name)()

		
		




Toolbar = MacToolbar
