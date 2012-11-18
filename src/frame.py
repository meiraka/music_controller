import wx


class Frame(wx.Frame):
	def __init__(self,parent,client):
		""" generate main app window."""
		self.parent = parent
		self.client = client
		wx.Frame.__init__(self,parent,-1)
