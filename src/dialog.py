"""
Dialog windows.

"""

import thread
import wx
from common import environment

MIN_STYLE = wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.FRAME_NO_TASKBAR

class Frame(wx.Frame):
    """
    Frames for dialog. close with Esc key.

    """
    def __init__(self, parent=None, style=MIN_STYLE):
        """ Generates Dialog Frame.

        Binds Escape key to close.
        """
        wx.Frame.__init__(self, parent, -1, style=style)
        id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnClose, id=id)
        table = [(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, id)]
        self.SetAcceleratorTable(wx.AcceleratorTable(table))

    def OnClose(self, event):
        """ Close event."""
        self.Close()


class SongInfo(Frame):
    """
    Song information dialog.

    """
    def __init__(self, parent, songs):
        """ Generates song info dialog.

        Arguments:
            parent -- parent window.
            songs -- song list.

        """
        Frame.__init__(self)
        self.songs = songs
        self.must_tags = [u'artist', u'title', u'album']
        must = wx.CollapsiblePane(self, -1, _('General Info')+':')
        sub = wx.CollapsiblePane(self, -1, _('Extra Info')+':')
        lyric = wx.CollapsiblePane(self, -1, _('Lyric')+':')
        self.__mast_pane = must.GetPane()
        self.__sub_pane = sub.GetPane()
        self.__lyric_pane = lyric.GetPane()
        self.__text_style = wx.TE_READONLY
        self.__border = 3
        if environment.userinterface.fill_readonly_background:
            self.__text_style = wx.TE_READONLY|wx.BORDER_NONE
        if environment.userinterface.subitem_small_font:
            self.__border = 0
        self.title = wx.StaticText(self, -1, style=self.__text_style)
        self.title.SetMinSize((environment.userinterface.text_height*20, -1))
        self.description = wx.StaticText(self, -1, style=self.__text_style)
        must_labels = [wx.StaticText(self.__mast_pane, -1, _(tag)+':') for tag in self.must_tags]
        self.must_values = [wx.TextCtrl(self.__mast_pane, -1, u'', style=self.__text_style) for tag in self.must_tags]
        self.must_values[0].SetFocus()
        self.lyric = wx.TextCtrl(self.__lyric_pane, -1, style=wx.TE_MULTILINE)
        self.lyric.SetMinSize((-1, environment.userinterface.text_height*8))
        if environment.userinterface.fill_readonly_background:
            for value in self.must_values+[self.title, self.description]:
                value.SetThemeEnabled(False)
                value.SetBackgroundColour(self.GetBackgroundColour())
        self.sub_tags = []
        m_sizer = wx.GridBagSizer()

        for index, tag in enumerate(self.must_tags):
            m_sizer.Add(must_labels[index], (index, 0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border=self.__border)
            m_sizer.Add(self.must_values[index], (index, 1), flag=wx.EXPAND|wx.ALL, border=self.__border)
        m_sizer.AddGrowableCol(1)
        if environment.userinterface.subitem_small_font:
            small_font = self.title.GetFont()
            small_font.SetPointSize(int(1.0*small_font.GetPointSize()/1.2))
            smalls = [self.description, must, sub, lyric, self.lyric,
                    self.__mast_pane, self.__sub_pane
                    ]+must_labels+self.must_values
            for i in smalls:
                i.SetFont(small_font)
            self.SetFont(small_font)
            self.__smallfont = small_font
            
        self.s_sizer = wx.GridBagSizer()
        self.__sub_pane.SetSizer(self.s_sizer)
        self.__mast_pane.SetSizer(m_sizer)
        m_sizer.SetSizeHints(self.__mast_pane)
        self.l_sizer = wx.BoxSizer(wx.VERTICAL)
        self.l_sizer.Add(self.lyric, 1, wx.EXPAND|wx.ALL, border=6)
        self.__lyric_pane.SetSizer(self.l_sizer)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.EXPAND|wx.ALL, border=3)
        sizer.Add(self.description, 0, wx.EXPAND|wx.ALL, border=3)
        #sizer.Add(wx.StaticLine(self, -1, style=wx.BORDER_SIMPLE|wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL, border=3)
        sizer.Add(must, 0, wx.EXPAND)
        sizer.Add(sub, 0, wx.EXPAND)
        sizer.Add(lyric, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.show(songs[0])
        must.Expand()
        sub.Expand()
        self.Show()

    def show(self, song):
        """ Show given song info.

        Arguments:
            song -- Song object.
        """
        self.title.SetLabel(song.format('%title% - %artist% %length%'))
        self.description.SetLabel(song.format('%album% %genre%'))
        for index, tag in enumerate(self.must_tags):
            if tag in song:
                self.must_values[index].SetValue(song[tag])
            else:
                self.must_values[index].SetValue(u'')
        self.__mast_pane.Layout()
        tags = [k for k, v in song.iteritems() if not self.must_tags.count(k)]
        for label in self.sub_tags:
            label.SetLabel('')
        for index, tag in enumerate(tags):
            if len(self.sub_tags)-1 <= index:
                self.sub_tags.append(
                    (wx.StaticText(self.__sub_pane, -1, u''),
                    wx.TextCtrl(self.__sub_pane, -1, u'', style=self.__text_style))
                    )
                if environment.userinterface.fill_readonly_background:
                    self.sub_tags[-1][1].SetBackgroundColour(self.GetBackgroundColour())
                    self.sub_tags[-1][1].SetThemeEnabled(False)
                if environment.userinterface.subitem_small_font:
                    self.sub_tags[-1][0].SetFont(self.__smallfont)
                    self.sub_tags[-1][1].SetFont(self.__smallfont)
                self.s_sizer.Add(self.sub_tags[-1][0], (index, 0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border=self.__border)
                self.s_sizer.Add(self.sub_tags[-1][1], (index, 1), flag=wx.EXPAND|wx.ALL, border=self.__border)
                if index == 0:
                    self.s_sizer.AddGrowableCol(1)
            label, value = self.sub_tags[index]
            label.SetLabel(_(tag)+':')
            value.SetValue(song[tag])
        self.SetTitle(u'%s info' % song.format(u'%title% - %artist%'))
        self.lyric.SetValue(song.lyric)

class Downloader(Frame):
    """
    common Download dialog.

    """
    def __init__(self, parent, database, song, labels):
        """
        Generates Downloader dialog.

        Arguments:
            parent -- parent window.
            database -- common.database.Database
            song -- Song for search method.
            labels -- Search query textctrl labels.
        """
        self.parent = parent
        self.database = database
        self.song = song
        self.items = []
        Frame.__init__(self, parent, style=MIN_STYLE|wx.RESIZE_BORDER)
        sizer = wx.GridBagSizer()
        sizer_flag = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL, border=3)
        sizer_flag_right = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT, border=3)
        expand_sizer_flag = dict(flag=wx.ALL|wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL, border=3)
        self.values = {}
        index = 0
        base = self
        if environment.userinterface.fill_window_background:
            base = wx.Panel(self, -1)
        for index, label in enumerate(labels):
            sizer.Add(wx.StaticText(base, -1, _(label)+u':'), (index, 0), **sizer_flag_right)
            value = wx.TextCtrl(base, -1, self.song[label])
            self.values[label] = value
            sizer.Add(value, (index, 1), (1, 2), **expand_sizer_flag)
        self.listview = wx.ListBox(base, -1)
        index = index + 1
        sizer.Add(self.listview, (index, 0), (1, 3), flag=wx.EXPAND)
        sizer.AddGrowableRow(index)
        sizer.AddGrowableCol(1)
        index = index + 1
        self.status_label = wx.StaticText(base, -1)
        self.search_button = wx.Button(base, -1, _('Search'))
        sizer.Add(self.status_label, (index, 0), **sizer_flag)
        sizer.Add(self.search_button, (index, 2), **sizer_flag)
        base.SetSizer(sizer)

        self.search_button.Bind(wx.EVT_BUTTON, self.on_search_button)
        self.listview.Bind(wx.EVT_LISTBOX_DCLICK, self.on_activate_item)
        if environment.userinterface.fill_window_background:
            sizer = wx.BoxSizer()
            sizer.Add(base, 1, wx.EXPAND)
            self.SetSizer(sizer)

    def on_search_button(self, event):
        """ Event function on 'Search' wx.Button.

        Queries api and show results.
        """
        self.listview.Clear()
        keywords = dict((label, value.GetValue()) for label, value in self.values.iteritems())
        def download():
            # requests api
            wx.CallAfter(self.status_label.SetLabel, _('Searching'))
            def download_callback(get, format, list):
                # appends results.
                for i in list:
                    wx.CallAfter(self.listview.Append, format(i))
                    self.items.append((get, i))
                wx.CallAfter(self.Layout)
            self.database.list(self.song, keywords, callback=download_callback)
            if self.items:
                wx.CallAfter(self.status_label.SetLabel, _('%i Items Found') % len(self.items))
            else:
                wx.CallAfter(self.status_label.SetLabel, _('No Items Found'))
        thread.start_new_thread(download, ())

    def on_activate_item(self, event):
        """ Event function on wx.ListBox item.

        Downloads selected item.
        """
        index = event.GetSelection()
        get, urlinfo = self.items[index]
        def download():
            # requests api and saves to database
            wx.CallAfter(self.status_label.SetLabel, _('Downloading'))
            data = get(urlinfo)
            self.database[self.song] = data
            wx.CallAfter(self.status_label.SetLabel, _(''))
        thread.start_new_thread(download, ())
