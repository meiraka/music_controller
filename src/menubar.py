
import sys
import webbrowser
import wx

from common import environment

import preferences
import version

class MenuBar(wx.MenuBar):
	NORMAL = 'normal'
	TOGGLE = 'toggle'
	SELECT = 'select'
	SPLITTER = 'splitter'
	def __init__(self,parent,client,accele=True):
		wx.MenuBar.__init__(self)
		self.accele = accele
		self.parent = parent
		self.client = client
		self.menu_list = [
			('File',[
				(wx.NewId(),u'Rescan Library',self.NORMAL),
				(wx.ID_EXIT,u'Quit',self.NORMAL),
				(wx.NewId(),u'',self.SPLITTER),
				(wx.NewId(),u'Get Info',self.NORMAL),
				]),
			('Edit',[
				(wx.NewId(),u'Select All',self.NORMAL),
				(wx.ID_PREFERENCES,u'Preferences',self.NORMAL)
				]),
			('Playback',[
				(wx.NewId(),u'Play',self.NORMAL),
				(wx.NewId(),u'Stop',self.NORMAL),
				(wx.NewId(),u'Previous',self.NORMAL),
				(wx.NewId(),u'Next',self.NORMAL),
				(wx.NewId(),u'splitter',self.SPLITTER),
				(wx.NewId(),u'Shuffle',self.TOGGLE),
				(wx.NewId(),u'Repeat',self.TOGGLE),
				(wx.NewId(),u'Single',self.TOGGLE),
				]),
			('View',[
				(wx.NewId(),u'Playlist',self.SELECT),
				(wx.NewId(),u'Library',self.SELECT),
				(wx.NewId(),u'Lyric',self.SELECT),
				(wx.NewId(),u'splitter',self.SPLITTER),
				(wx.NewId(),u'Albumlist',self.TOGGLE),
				(wx.NewId(),u'Info',self.TOGGLE),
				(wx.NewId(),u'splitter',self.SPLITTER),
				(wx.NewId(),u'Focus Current Song',self.NORMAL)
				]),
			('Help',[
				(wx.ID_ABOUT,u'About',self.NORMAL),
				(wx.NewId(),u'MusicController Website',self.NORMAL),
				])
			]

		self.__functions = {
				u'File_Rescan Library':self.client.library.update,
				u'File_Get Info':self.parent.get_info,
				u'File_Quit':sys.exit,
				u'Edit_Select All':self.set_select_all,
				u'Edit_Preferences':self.parent.show_preferences,
				u'Playback_Play':self.set_play,
				u'Playback_Stop':self.client.playback.stop,
				u'Playback_Previous':self.client.playback.previous,
				u'Playback_Next':self.client.playback.next,
				u'Playback_Shuffle':self.set_shuffle,
				u'Playback_Repeat':self.set_repeat,
				u'Playback_Single':self.set_single,
				u'View_Playlist':self.parent.show_playlist,
				u'View_Library':self.parent.show_library,
				u'View_Lyric':self.parent.show_lyric,
				u'View_Albumlist':self.toggle_config_value('playlist_albumlist',self.parent.show_not_connection),
				u'View_Info':self.toggle_config_value('info',self.parent.show_not_connection),
				u'View_Focus Current Song':self.focus_song,
				u'Help_About':AboutDialog,
				u'Help_MusicController Website':self.show_repository,
				}
		self.__keys = {
				u'File_Quit':'Ctrl+Q',
				u'File_Get Info':'Ctrl+I',
				u'Edit_Select All':'Ctrl+A',
				u'Edit_Preferences':'Ctrl+,',
				u'Playback_Play':'Space',
				u'Playback_Next':'Ctrl+Right',
				u'Playback_Previous':'Ctrl+Left',
				u'Playback_Shuffle':'Ctrl+b',
				u'Playback_Repeat':'Ctrl+n',
				u'Playback_Single':'Ctrl+m',
				u'View_Playlist':'Ctrl+1',
				u'View_Library':'Ctrl+2',
				u'View_Lyric':'Ctrl+3',
				}

		self.__ids = {}
		self.__labels = {}
		self.SetAutoWindowMenu(0)
		for head,items in self.menu_list:
			menu = wx.Menu()
			menu.Bind(wx.EVT_MENU,self.OnMenu)
			for id,label,menu_type in items:
				if menu_type == self.NORMAL:
					self.__ids[id] = head+u'_'+label
					self.__labels[head+u'_'+label] = id
					menu.Append(id,label)
				elif menu_type == self.SPLITTER:
					menu.AppendSeparator()
				elif menu_type == self.TOGGLE:
					self.__ids[id] = head+u'_'+label
					self.__labels[head+u'_'+label] = id
					menu.AppendCheckItem(id,label)
				elif menu_type == self.SELECT:
					self.__ids[id] = head+u'_'+label
					self.__labels[head+u'_'+label] = id
					menu.AppendRadioItem(id,label)
			self.Append(menu,head)
			self.parent.Bind(wx.EVT_MENU,self.OnMenu,id=id)
					
		self.parent.Bind(wx.EVT_MENU,self.OnMenu)
		if self.accele:
			self.set_accelerator_table(self.__keys)
		self.set_menu_accelerator(self.__keys,self.accele)
		self.client.playback.bind(self.client.playback.UPDATE,self.OnUpdate)
		self.parent.bind(self.parent.VIEW,self.update_by_frame)
		self.parent.Bind(wx.EVT_IDLE,self.update_by_idle)
		self.client.connection.bind(self.client.connection.CONNECT,self.update_by_connection)
		self.client.connection.bind(self.client.connection.CLOSE,self.update_by_connection)
		self.client.connection.bind(self.client.connection.CLOSE_UNEXPECT,self.update_by_connection)
		self.update_by_config()

	def set_accelerator_table(self,keys):
		flag_tables = dict(Ctrl=wx.ACCEL_CTRL)
		key_tables = dict(Space=wx.WXK_SPACE,
					Right=wx.WXK_RIGHT,
					Left=wx.WXK_LEFT)
		table = []
		def get_key(key,head,id,label):
			if not keys.has_key(head+u'_'+label):
				return (None,None)
			key = keys[head+u'_'+label]
			splitted = key.split('+')
			flags = None
			keycode = None
			for i in splitted:
				if flag_tables.has_key(i):
					if flags == None:
						flags = flag_tables[i]
					else:
						flags = flags | flag_tables[i]
				elif i in key_tables:
					keycode = key_tables[i]
				else:
					keycode = ord(i)
			if not flags:
				flags = wx.ACCEL_NORMAL
			return (flags,keycode)

		for head,items in self.menu_list:
			for id,label,menu_type in items:
				if not menu_type == self.SPLITTER:
					flags,keycode = get_key(keys,head,id,label)
					if keycode:
						table.append((flags,keycode,id))
		self.parent.SetAcceleratorTable(wx.AcceleratorTable(table))
				
	def set_menu_accelerator(self,keys,accele):
		for index,(head,items) in enumerate(self.menu_list):
			menu = self.GetMenu(index)
			self.SetLabelTop(index,self.menu_label(head,accele))
			for id,label,menu_type in items:
				if not menu_type == self.SPLITTER:
					if keys.has_key(head+u'_'+label):
						key = keys[head+u'_'+label]
						menu.SetLabel(id,self.menu_label(label,accele)+u'\t'+key)
					else:
						menu.SetLabel(id,self.menu_label(label))

	def menu_label(self,label,accele=None):
		if accele:
			i18n = _(label)
			if i18n[0] == label[0]:
				return u'&%s' % label[0] + i18n[1:]
			else:
				return i18n + u'(&%s)' % label[0]
		else:
			return _(label)

	def update_by_idle(self,event):
		widget = self.FindFocus()
		# File
		index = 0
		head,items = self.menu_list[index]
		menu = self.GetMenu(index)
			
		for id,label,menu_type in items:
			if label == u'Get Info':
				menu.Enable(id,self.parent.can_get_info())
		# Edit
		index = 1
		head,items = self.menu_list[index]
		menu = self.GetMenu(index)
			
		for id,label,menu_type in items:
			if label == u'Select All':
				menu.Enable(id,widget and hasattr(widget,'HasMultipleSelection') and widget.HasMultipleSelection() or type(widget) is wx.TextCtrl and hasattr(widget,'SetSelection'))

	def update_by_connection(self,event=None):
		updates = [
			u'Rescan Library',
			u'Get Info',
			u'Play',
			u'Stop',
			u'Previous',
			u'Next',
			u'Shuffle',
			u'Repeat',
			u'Single',
			u'Playlist',
			u'Library',
			u'Lyric',
			u'Albumlist',
			u'Info',
			u'Focus Current Song',
			]
		def __update():
			for index,(head,items) in enumerate(self.menu_list):
				menu = self.GetMenu(index)
				for id,label,menu_type in items:
					for update_label in updates:
						if label == update_label:
							menu.Enable(id,self.client.connection.connected)
		wx.CallAfter(__update)
	
	def update_by_config(self):
		""" change menubar items by config value. """
		for index,(head,items) in enumerate(self.menu_list):
			for id,label,menu_type in items:
				menu = self.GetMenu(index)
				if label == u'Albumlist':
					current = menu.IsChecked(id)
					new = self.client.config.playlist_albumlist
					if not current == new:
						menu.Check(id,new)
				if label == u'Info':
					current = menu.IsChecked(id)
					new = self.client.config.info
					if not current == new:
						menu.Check(id,new)
					
	def update_by_status(self):
		""" change menubar items by playback status. """
		status = self.client.playback.status
		if not status:
			return
		for index,(head,items) in enumerate(self.menu_list):
			for id,label,menu_type in items:
				menu = self.GetMenu(index)
				if label == u'Shuffle':
					key = u'random'
					current = menu.IsChecked(id)
					new = True if key in status and status[key] == u'1' else False
					if not current == new:
						menu.Check(id,new)
				if label == u'Repeat':
					key = u'repeat'
					current = menu.IsChecked(id)
					new = True if key in status and status[key] == u'1' else False
					if not current == new:
						menu.Check(id,new)
							
				if label == u'Single':
					key = u'single'
					current = menu.IsChecked(id)
					new = True if key in status and status[key] == u'1' else False
					if not current == new:
						menu.Check(id,new)

	def update_by_frame(self):
		""" change menubar items by main view. """
		current = self.parent.current_view
		if not current:
			current = 'playlist'
		id = self.__labels['View_' + current.capitalize()]
		if not self.IsChecked(id):
			self.Check(id,True)

	def set_select_all(self):
		widget = self.FindFocus()
		if widget:
			if hasattr(widget,'SelectAll'):
				widget.SelectAll()
			elif hasattr(widget,'SetSelection'):
				widget.SetSelection(-1,-1)
			
	def set_play(self):
		playback = self.client.playback
		status = playback.status
		if status and u'state' in status:
			playback.pause() if status[u'state'] == u'play' else playback.play()

	def toggle_config_value(self,attr,callback=None):
		def set():
			value = getattr(self.client.config,attr)
			setattr(self.client.config,attr,not(value))
			if callback:
				callback()
			self.update_by_config()
		return set

	def set_shuffle(self):
		for index,(head,items) in enumerate(self.menu_list):
			for id,label,menu_type in items:
				if label == u'Shuffle':
					menu = self.GetMenu(index)
					self.client.playback.random(menu.IsChecked(id))
					break
			
	def set_repeat(self):
		for index,(head,items) in enumerate(self.menu_list):
			for id,label,menu_type in items:
				if label == u'Repeat':
					menu = self.GetMenu(index)
					self.client.playback.repeat(menu.IsChecked(id))
					break
	def set_single(self):
		for index,(head,items) in enumerate(self.menu_list):
			for id,label,menu_type in items:
				if label == u'Single':
					menu = self.GetMenu(index)
					self.client.playback.single(menu.IsChecked(id))
					break

	def focus_song(self):
		self.parent.playlist.focus()
		self.parent.albumlist.focus()

	def OnMenu(self,event):
		label = self.__ids[event.GetId()]
		func = self.__functions[label]
		func()

	def OnUpdate(self,*args,**kwargs):
		self.update_by_status()

	def show_repository(self):
		webbrowser.open('https://bitbucket.org/meiraka/music_controller')


class AboutDialog(object):
	def __init__(self):
		info = wx.AboutDialogInfo()
		info.SetName(environment.common.name)
		info.SetVersion(version.__version__)
		app_description = _(environment.common.description)
		python_version = _('Python %(python)s on %(system)s') % \
			{u'python': sys.version.split()[0] ,u'system':sys.platform}
		platform = list(wx.PlatformInfo[1:])
		platform[0] += (" " + wx.VERSION_STRING)
		wx_info = ", ".join(platform)
		build_info = 'execute source'
		try:
			import buildinfo
			build_info = 'build by %s@%s' %(buildinfo.user,buildinfo.host)
			if buildinfo.revision:
				info.SetVersion(version.__version__+'.'+buildinfo.revision)
		except Exception,err:
			pass
		info.SetDescription(u'\n'.join([app_description,python_version,wx_info,build_info]))
		if environment.userinterface.about_licence:
			info.SetLicence(environment.common.licence)
		info.SetCopyright(environment.common.copyright)
		wx.AboutBox(info)


