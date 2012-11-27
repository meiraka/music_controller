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
