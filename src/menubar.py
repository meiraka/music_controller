
import wx
import preferences

class MenuBar(wx.MenuBar):
	NORMAL = 'normal'
	TOGGLE = 'toggle'
	SPLITTER = 'splitter'
	def __init__(self,parent,client,accele=True):
		wx.MenuBar.__init__(self)
		self.accele = accele
		self.parent = parent
		self.client = client
		self.menu_list = [
			('Edit',[
				(wx.ID_PREFERENCES,u'Preferences',self.NORMAL)
				]),
			('Playback',[
				(wx.NewId(),u'Play',self.NORMAL),
				(wx.NewId(),u'Pause',self.NORMAL),
				(wx.NewId(),u'Stop',self.NORMAL),
				(wx.NewId(),u'Previous',self.NORMAL),
				(wx.NewId(),u'Next',self.NORMAL),
				(wx.NewId(),u'splitter',self.SPLITTER),
				(wx.NewId(),u'Shuffle',self.TOGGLE),
				(wx.NewId(),u'Repeate',self.TOGGLE),
				(wx.NewId(),u'Repeate one',self.TOGGLE),
				])
			]

		self.__functions = {
				u'Edit_Preferences':self.parent.show_preferences

				}
		self.__keys = {
				u'Edit_Preferences':'Ctrl+,'
				}

		self.__ids = {}
		for head,items in self.menu_list:
			menu = wx.Menu()
			menu.Bind(wx.EVT_MENU,self.OnMenu)
			self.Append(menu,head)
			for id,label,menu_type in items:
				if menu_type == self.NORMAL:
					self.__ids[id] = head+u'_'+label
					menu.Append(id,label)
		self.parent.Bind(wx.EVT_MENU,self.OnMenu)
		self.set_accelerator_table(self.__keys)
		self.set_menu_accelerator(self.__keys,self.accele)

	def set_accelerator_table(self,keys):
		key_tables = dict(Ctrl=wx.ACCEL_CTRL)
		table = []
		def get_key(key,head,id,label):
			if not keys.has_key(head+u'_'+label):
				return (None,None)
			key = keys[head+u'_'+label]
			splitted = key.split('+')
			flags = None
			keycode = None
			for i in splitted:
				if key_tables.has_key(i):
					if flags == None:
						flags = key_tables[i]
					else:
						flags = flags | key_tables[i]
				else:
					keycode = ord(i)
			if not flags:
				flags = wx.ACCEL_NORNAL
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

	def menu_label(self,label,accele):
		if accele:
			i18n = label
			if i18n[0] == label[0]:
				return u'&%s' % label[0] + i18n[1:]
			else:
				return i18n + u'(&%s)' % label[0]
		else:
			return label

	def OnMenu(self,event):
		label = self.__ids[event.GetId()]
		func = self.__functions[label]
		func()

