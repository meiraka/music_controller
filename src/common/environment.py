#!/usr/bin/python
import os
import sys
import wx


config_dir = '%s/.config/MusicController' % os.environ['HOME']

class __Common(object):
	__cached = dict(
		name = 'MusicController',
		description = 'Pretty client for MusicPlayerDaemon.',
		copyright = 'Copyright (C) 2012-2013  mei raka',
		licence = """
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
		)

	def __init__(self):
		pass
	def __get(key):
		def get(self):
			return self.__cached[key]
		return get

	name =              property(__get('name'))
	description=        property(__get('description'))
	copyright =         property(__get('copyright'))
	licence =           property(__get('licence'))



class __UI(object):
	"""
	params for ui.*
	
	parameters:
		+ cat get values at anytime.
		fill_readonly_background - fill background readonly wx.TextCtrl
		subitem_small_font - decrease font size to div font pt by 1.2 
		subwindow_small_frame - uses wx.MiniFrame when True
		style - gtk or mac or None.
		
		+ can get values after wx.App inited.
		colors - two color found in app.
		font - desktop font.
		text_height - desktop font height.
	"""
	__cached = dict(
		fill_readonly_background = False,
		subitem_small_font = False,
		subwindow_small_frame = False,
		style = None,
		draw_double_buffered = True,
		toolbar_toggle = True,
		toolbar_icon_centre = False,
		toolbar_icon_horizontal = True,
		toolbar_icon_dropdown = False,
		toolbar_icon_info = False,
		about_licence = True,
		)
	def __init__(self):
		if wx.PlatformInfo[1] == 'wxGTK':
			self.__cached['style'] = u'gtk'
		if wx.PlatformInfo[1] == 'wxMac':
			self.__cached['fill_readonly_background'] = True
			self.__cached['subitem_small_font'] = True
			self.__cached['subwindow_small_frame'] = True
			self.__cached['style'] = u'mac'
			self.__cached['draw_double_buffered'] = False
			self.__cached['toolbar_toggle'] = False
			self.__cached['toolbar_icon_centre'] = True
			self.__cached['toolbar_icon_horizontal'] = False
			self.__cached['toolbar_icon_dropdown'] = True
			self.__cached['toolbar_icon_info'] = True
			self.__cached['about_licence'] = False
		self.argv_override()

	def argv_override(self):
		argv_override = True
		for arg in sys.argv:
			if arg.count('='):
				key,value = arg.split('=',1)
				if key in self.__cached:
					bool_value = True if value == 'True' else False
					if not self.__cached[key] == bool_value:
						self.__cached[key] = bool_value
						print 'override: %s to %s' % (key,str(bool_value))
				else:
					print 'no keys: ' + key
					argv_override = False
		if not argv_override:
			for k,v in self.__cached.iteritems():
				print '%s=%s' % (k,str(v))
					
					
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

	def __get_colors(self):
		if self.__cached.has_key(u'colors'):
			return self.__cached[u'colors']
		else:
			base = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWFRAME)
			indexes = [wx.SYS_COLOUR_WINDOW,wx.SYS_COLOUR_HIGHLIGHT,wx.SYS_COLOUR_WINDOWTEXT,wx.SYS_COLOUR_HIGHLIGHTTEXT,wx.SYS_COLOUR_BTNFACE]
			if not base == wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX):
				self.__cached[u'colors'] = (base, wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX))
			for index in indexes:
				if not base == wx.SystemSettings.GetColour(index):
					self.__cached[u'colors'] = (base,wx.SystemSettings.GetColour(index))
					break
			else:
				self.__cached[u'colors'] = (base,base)
			return self.__cached[u'colors']

	def __set(key):
		def set(self,value):
			self.__cached[key] = value
		return set

	def __get(key):
		def get(self):
			return self.__cached[key]
		return get

	fill_readonly_background = property(__get('fill_readonly_background'))
	subitem_small_font =       property(__get('subitem_small_font'))
	subwindow_small_frame =    property(__get('subwindow_small_frame')) 
	style =                    property(__get('style')) 
	draw_double_buffered =     property(__get('draw_double_buffered')) 
	toolbar_toggle =           property(__get('toolbar_toggle'))
	toolbar_icon_centre =      property(__get('toolbar_icon_centre'))
	toolbar_icon_dropdown =    property(__get('toolbar_icon_dropdown'))
	toolbar_icon_info =        property(__get('toolbar_icon_info'))
	toolbar_icon_horizontal =  property(__get('toolbar_icon_horizontal'))
	about_licence =            property(__get('about_licence'))
	colors =                   property(__get_colors)
	font =                     property(__get_font, __set(u'font'))
	text_height =              property(__get_text_height)

userinterface = __UI()
common = __Common()
