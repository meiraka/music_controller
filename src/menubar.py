
import wx
import preferences

class MenuBar(wx.MenuBar):
	def __init__(self,parent,client):
		wx.MenuBar.__init__(self)
		self.parent = parent
		self.client = client
		self.menu_list = [
			('Edit',[
				(wx.ID_PREFERENCES,u'Preferences')
				])
			]

		self.__functions = {
				u'Edit_Preferences':lambda: preferences.Frame(self.parent,self.client).Show()

				}
		self.__keys = {
				u'Edit_Preferences':'Ctrl+,'
				}

		self.__ids = {}
		for head,items in self.menu_list:
			menu = wx.Menu()
			menu.Bind(wx.EVT_MENU,self.OnMenu)
			self.Append(menu,head)
			for id,label in items:
				self.__ids[id] = head+u'_'+label
				menu.Append(id,label)
		self.parent.Bind(wx.EVT_MENU,self.OnMenu)
		self.set_accelerator_table(self.__keys)

	def set_accelerator_table(self,keys):
		key_tables = dict(Ctrl=wx.ACCEL_CTRL)
		table = []
		for head,items in self.menu_list:
			for id,label in items:
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
				if keycode:
					table.append((flags,keycode,id))
					print key
		self.parent.SetAcceleratorTable(wx.AcceleratorTable(table))
				


	def set_menu_accelerator(self,keys):
		pass
	def OnMenu(self,event):
		label = self.__ids[event.GetId()]
		func = self.__functions[label]
		func()

