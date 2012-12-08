#!/usr/bin/python
import os
import wx

config_dir = '%s/.config/MusicController' % os.environ['HOME']
if wx.PlatformInfo[1] == 'wxMac':
	gui = 'mac'
elif wx.PlatformInfo[1] == 'wxGTK':
	gui = 'gtk'
else:
	gui = ''

class __UI(object):
	"""
	params for ui.*
	"""
	__cached = {}
	def __get_font(self):
		key = u'font'
		if self.__cached.has_key(key):
			return self.__cached[key]
		else:
			font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT )
			self.__cached[key] = font
			return self.__cached[key]
	
	def __get_text_height(self):
		if self.__cached.has_key(u'text_height'):
			return self.__cached[u'text_height']
		else:
			image = wx.EmptyBitmap(100,100)
			image_writer = wx.MemoryDC(image)
			image_writer.SetFont(self.font)
			text_height = image_writer.GetTextExtent('A-glFf')[1]
			self.__cached[u'text_height'] = text_height
			return self.__cached[u'text_height']

	def __set(self,key,value):
		self.__cached[key] = value
	font = property(__get_font,lambda self,value: self.__set(u'font',value))
	text_height = property(__get_text_height)

ui = __UI()
