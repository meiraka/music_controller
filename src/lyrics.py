#!/usr/bin/python

import wx
import environment

"""
Draw lyric 
"""

class LyricBase(object):
	pass



class Lyric(wx.Panel):
	def __init__(self,parent,client):
		self.client = client
		self.parent = parent
		wx.Panel.__init__(self,parent,-1)
		self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX))
		self.font = environment.userinterface.font
		#self.timer = wx.Timer(self.parent,-1)
		#wx.EVT_TIMER(self.parent,-1,self.update)
		#self.timer.Start(200)
		self.parent.Bind(wx.EVT_ERASE_BACKGROUND,self.update)
		self.parent.Bind(wx.EVT_PAINT,self.OnPaint)
		self.update()

	def OnPaint(self,event):
		self.update(event)

	def update(self,event=None):
		dc = wx.ClientDC(self)
		dc.BeginDrawing()
		try:
			dc = event.GetDC()
		except:
			pass
		dc.SetFont(self.font)
		x,y = self.GetPosition()
		w,h = self.GetSize()
		self.draw(dc,(x,y,w,h))
		dc.EndDrawing()

	def draw(self,dc,rect):
		self.Refresh()
		x,y,w,h = rect
		try:
			dc.DrawText('hello test',0,0)
		except Exception,err:
			print err
		
	
