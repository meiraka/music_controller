
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


		self.__ids = {}
		for head,items in self.menu_list:
			menu = wx.Menu()
			menu.Bind(wx.EVT_MENU,self.OnMenu)
			self.Append(menu,head)
			for id,label in items:
				self.__ids[id] = head+u'_'+label
				menu.Append(id,label)

	def OnMenu(self,event):
		label = self.__ids[event.GetId()]
		func = self.__functions[label]
		func()

