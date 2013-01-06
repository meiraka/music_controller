#!/usr/bin/python
import os
import wx


config_dir = '%s/.config/MusicController' % os.environ['HOME']

class __UI(object):
	"""
	params for ui.*
	"""
	__cached = dict(
		fill_readonly_background = False,
		subitem_small_font = False,
		subwindow_small_frame = False,
		style = None
		)
	def __init__(self):
		if wx.PlatformInfo[1] == 'wxGTK':
			self.__cached['style'] = u'gtk'
		if wx.PlatformInfo[1] == 'wxMac':
			self.__cached['self.fill_readonly_background'] = True
			self.__cached['self.subitem_small_font'] = True
			self.__cached['self.subwindow_small_frame'] = True
			self.__cached['self.style'] = u'mac'
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

	def __get(key):
		def get(self):
			return self.__cached[key]
		return get
	font = property(__get_font,lambda self,value: self.__set(u'font',value))
	text_height = property(__get_text_height)
	fill_readonly_background =property(__get('fill_readonly_background'))
	subitem_small_font =      property(__get('subitem_small_font'))
	subwindow_small_frame =   property(__get('subwindow_small_frame')) 
	style =                   property(__get('style')) 

userinterface = __UI()
