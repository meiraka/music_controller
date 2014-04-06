"""
Preferences dialogs.

"""

import wx

import dialog
from common import environment

class App(dialog.Frame):
    """
    Application preferences window.
    """
    def __init__(self, parent, client, debug=False):
        dialog.Frame.__init__(self, parent)
        self.client = client
        self.__windows = [
            (u'Connection', Connection, ['server', wx.ART_GO_HOME]),
            (u'Playback', Playback, ['gtk-media-play-ltr', wx.ART_GO_FORWARD]),
            (u'Artwork', Artwork, ['folder-music', wx.ART_PASTE]),
            (u'Lyrics', Lyrics, ['folder-documents', wx.ART_PASTE]),
            (u'Notification', Notify, ['update-notifier', wx.ART_GO_HOME])
            ]

        self.__ids = {}
        self.__indexes = []
        self.SetTitle(_(self.__windows[0][0]))
        # toolbar
        toolbar_style = wx.TB_TEXT
        if environment.userinterface.toolbar_icon_horizontal:
            toolbar_style = wx.TB_HORZ_TEXT
        self.__tool = self.CreateToolBar(toolbar_style)
        for label, c, icons in self.__windows:
            id = wx.NewId()
            self.__ids[label] = id
            self.__indexes.append(id)
            bmp = None
            for icon in icons:
                bmp = wx.ArtProvider.GetBitmap(icon)
                if bmp.IsOk() and not bmp.GetSize() == (-1, -1):
                    break
            if environment.userinterface.toolbar_toggle:
                self.__tool.AddRadioLabelTool(id, _(label), bmp)
            else:
                self.__tool.AddLabelTool(id, _(label), bmp)
        self.__tool.Bind(wx.EVT_TOOL, self.OnTool)
        self.__tool.Realize()
        # generate panels
        base = self
        if environment.userinterface.fill_window_background:
            base = wx.Panel(self, -1)

        self.__sizers = [config_class(base, client) for label, config_class, i in self.__windows]
        sizer = wx.BoxSizer()
        for config_sizer in self.__sizers:
            config_sizer.Hide()
            sizer.Add(config_sizer, 1, wx.EXPAND)
        self.__sizers[0].Show()
        base.SetSizer(sizer)
        if environment.userinterface.fill_window_background:
            sizer = wx.BoxSizer()
            sizer.Add(base, 1, wx.EXPAND)
            self.SetSizer(sizer)
        sizer.Fit(self)

    def OnTool(self, event):
        click_id = event.GetId()
        click_index = self.__indexes.index(click_id)
        for label, id in self.__ids.iteritems():
            if environment.userinterface.toolbar_toggle:
                self.__tool.ToggleTool(id, id==click_id)
            if id == click_id:
                self.SetTitle(_(label))
        for index, sizer in enumerate(self.__sizers):
            if index == click_index:
                sizer.Show()
            else:
                sizer.Hide()


class Artwork(wx.BoxSizer):
    def __init__(self, parent, client):
        self.parent = parent
        self.client = client
        wx.BoxSizer.__init__(self, wx.VERTICAL)
        self.__downloads_api = [
            u'lastfm'
            ]
        self.__is_download = wx.CheckBox(parent, -1, _(u'Download Artwork'))
        self.__is_download.Bind(wx.EVT_CHECKBOX, self.click_is_download)
        self.__is_downloads_api = [
            wx.CheckBox(parent, -1, _(u'Download from %s') % api) for api in self.__downloads_api
            ]
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.__is_download, 0, wx.ALL, border=3)
        downloads_sizer = wx.BoxSizer(wx.VERTICAL)
        for download_api in self.__is_downloads_api:
            downloads_sizer.Add(download_api, 0, wx.ALL, border=3)
            download_api.Bind(wx.EVT_CHECKBOX, self.click_is_download_api)
        sizer.Add(downloads_sizer, 0, wx.LEFT|wx.RIGHT, border=15)
        self.Add(sizer, 0, wx.ALL, border=6)
        self.load_config()

    def load_config(self):
        download = self.client.config.lyrics_download
        self.__is_download.SetValue(download)
        for download_api in self.__is_downloads_api:
            download_api.Enable(download)
        for index, api in enumerate(self.__downloads_api):
            attr = 'artwork_api_' + api.replace(u'.', u'_')
            use_api = getattr(self.client.config, attr)
            self.__is_downloads_api[index].SetValue(use_api)

    def click_is_download(self, event):
        download = self.__is_download.GetValue()
        self.client.config.lyrics_download = download
        self.load_config()

    def click_is_download_api(self, event):
        obj = event.GetEventObject()
        index = self.__is_downloads_api.index(obj)
        label = self.__downloads_api[index]
        attr = 'artwork_api_' + label.replace(u'.', u'_')
        setattr(self.client.config, attr, obj.GetValue())

    def Hide(self):
        self.ShowItems(False)
        self.parent.Layout()

    def Show(self):
        self.ShowItems(True)
        self.parent.Layout()


class Lyrics(wx.BoxSizer):
    def __init__(self, parent, client):
        self.parent = parent
        self.client = client
        wx.BoxSizer.__init__(self, wx.VERTICAL)
        self.__downloads_api = [
            u'geci.me'
            ]
        self.__is_download = wx.CheckBox(parent, -1, _(u'Download Lyric'))
        self.__is_download.Bind(wx.EVT_CHECKBOX, self.click_is_download)
        self.__is_downloads_api = [
            wx.CheckBox(parent, -1, _(u'Download from %s') % api) for api in self.__downloads_api
            ]
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.__is_download, 0, wx.ALL, border=3)
        downloads_sizer = wx.BoxSizer(wx.VERTICAL)
        for download_api in self.__is_downloads_api:
            downloads_sizer.Add(download_api, 0, wx.ALL, border=3)
            download_api.Bind(wx.EVT_CHECKBOX, self.click_is_download_api)
        sizer.Add(downloads_sizer, 0, wx.LEFT|wx.RIGHT, border=15)
        self.Add(sizer, 0, wx.ALL, border=6)
        self.load_config()

    def load_config(self):
        download = self.client.config.lyrics_download
        self.__is_download.SetValue(download)
        for download_api in self.__is_downloads_api:
            download_api.Enable(download)
        for index, api in enumerate(self.__downloads_api):
            attr = 'lyrics_api_' + api.replace(u'.', u'_')
            use_api = getattr(self.client.config, attr)
            self.__is_downloads_api[index].SetValue(use_api)

    def click_is_download(self, event):
        download = self.__is_download.GetValue()
        self.client.config.lyrics_download = download
        self.load_config()

    def click_is_download_api(self, event):
        obj = event.GetEventObject()
        index = self.__is_downloads_api.index(obj)
        label = self.__downloads_api[index]
        attr = 'lyrics_api_' + label.replace(u'.', u'_')
        setattr(self.client.config, attr, obj.GetValue())

    def Hide(self):
        self.ShowItems(False)
        self.parent.Layout()

    def Show(self):
        self.ShowItems(True)
        self.parent.Layout()


class Notify(wx.BoxSizer):
    def __init__(self, parent, client):
        self.parent = parent
        self.client = client
        wx.BoxSizer.__init__(self, wx.VERTICAL)
        sizer = wx.GridBagSizer()
        self.growl = wx.CheckBox(parent, -1, _(u'Growl'))
        growl_host_label = wx.StaticText(parent, -1, _(u'Host')+u':')
        growl_pass_label = wx.StaticText(parent, -1, _(u'Password')+u':')
        self.growl_host = wx.TextCtrl(parent, -1, self.client.config.notify_growl_host)
        self.growl_pass = wx.TextCtrl(parent, -1, self.client.config.notify_growl_pass)
        self.osd = wx.CheckBox(parent, -1, _(u'Notify OSD'))
        self.test = wx.Button(parent, -1, _(u'Test'))
        params = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL, border=3)
        params_label = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT, border=3)
        params_expand = dict(flag=wx.ALL|wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL, border=3)
        sizer.Add(wx.StaticText(parent, -1, _(u'Notify System')), (0, 0), (1, 2), **params)
        sizer.Add(self.growl, (1, 1), (1, 2), **params)
        sizer.Add(growl_host_label, (2, 1), **params_label)
        sizer.Add(self.growl_host, (2, 2), (1, 3), **params_expand)
        sizer.Add(growl_pass_label, (3, 1), **params_label)
        sizer.Add(self.growl_pass, (3, 2), (1, 3), **params_expand)
        sizer.Add(self.osd, (4, 1), (1, 2), **params)
        sizer.Add(self.test, (6, 4), **params)
        sizer.AddGrowableCol(3)
        sizer.AddGrowableRow(5)
        self.test.Bind(wx.EVT_BUTTON, self.on_test)
        self.growl.Bind(wx.EVT_CHECKBOX, self.on_activate)
        self.osd.Bind(wx.EVT_CHECKBOX, self.on_activate)
        self.growl_host.Bind(wx.EVT_TEXT, self.on_growl_settings)
        app = wx.GetApp()
        self.osd.Enable(app.notifyosd.active)
        self.growl.Enable(app.growlnotify.active)
        self.growl_host.Enable(app.growlnotify.active)
        self.growl_pass.Enable(app.growlnotify.active)
        growl_host_label.Enable(app.growlnotify.active)
        growl_pass_label.Enable(app.growlnotify.active)

        self.osd.SetValue(self.client.config.notify_osd)
        self.growl.SetValue(self.client.config.notify_growl)
        self.Add(sizer, 1, wx.ALL|wx.EXPAND, 9)

    def on_growl_settings(self, event):
        app = wx.GetApp()
        if app.growlnotify.active:
            obj = event.GetEventObject()
            if obj == self.growl_host:
                self.client.config.notify_growl_host = obj.GetValue()
            elif obj == self.growl_pass:
                self.client.config.notify_growl_port = obj.GetValue()
            app.growlnotify.reconnect()
        
    def on_activate(self, event):
        obj = event.GetEventObject()
        if obj == self.growl:
            self.client.config.notify_growl = obj.GetValue()
        elif obj == self.osd:
            self.client.config.notify_osd = obj.GetValue()

    def on_test(self, event):
        app = wx.GetApp()
        app.growlnotify.test()
        app.notifyosd.test()

    def Hide(self):
        self.ShowItems(False)
        self.parent.Layout()

    def Show(self):
        self.ShowItems(True)
        self.parent.Layout()



class Connection(wx.BoxSizer):
    def __init__(self, parent, client):
        wx.BoxSizer.__init__(self)
        self.parent = parent
        self.connection = client.connection
        self.config = client.config

        self.box = wx.ListBox(parent, -1)
        self.add = wx.Button(parent, -1, '+', style=wx.BU_EXACTFIT)
        self.delete = wx.Button(parent, -1, '-', style=wx.BU_EXACTFIT)
        
        self.mpd = wx.StaticText(parent, -1, u'mpd')
        self.profile_label = wx.StaticText(parent, -1, _(u'Profile')+':')
        self.profile = wx.TextCtrl(parent, -1)
        self.host_label = wx.StaticText(parent, -1, _(u'Host')+':')
        self.host = wx.TextCtrl(parent, -1)
        self.host.SetFocus()
        self.port_label = wx.StaticText(parent, -1, _(u'Port')+':')
        self.port = wx.TextCtrl(parent, -1)
        self.use_password = wx.CheckBox(parent, -1, _(u'Password')+':')
        self.password = wx.TextCtrl(parent, -1)
        self.status = wx.StaticText(parent, -1, '')
        self.connect = wx.Button(parent, -1, _(u'Connect'))
        sizer = wx.GridBagSizer()
        params = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL, border=3)
        params_label = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT, border=3)
        params_expand = dict(flag=wx.ALL|wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL, border=3)
        sizer.Add(self.box, (0, 0), (7, 3), **params_expand)
        sizer.Add(self.add, (7, 0), **params)
        sizer.Add(self.delete, (7, 1), **params)
        sizer.Add(self.mpd, (0, 3), **params)
        sizer.Add(self.profile_label, (1, 3), **params_label)
        sizer.Add(self.profile, (1, 4), (1, 2), **params_expand)
        sizer.Add(self.host_label, (2, 3), **params_label)
        sizer.Add(self.host, (2, 4), (1, 2), **params_expand)
        sizer.Add(self.port_label, (3, 3), **params_label)
        sizer.Add(self.port, (3, 4), (1, 2), **params_expand)
        sizer.Add(self.use_password, (4, 3), **params_label)
        sizer.Add(self.password, (4, 4), (1, 2), **params_expand)
        sizer.Add(self.status, (6, 3), (1, 3), **params_expand)
        sizer.Add(self.connect, (7, 5), **params)
        sizer.AddGrowableCol(4)
        sizer.AddGrowableRow(5)
        self.Add(sizer, 1, wx.ALL|wx.EXPAND, 9)
    
        self.selected = None
        self.selected_index = -1
        self.__update()
        self.box.Bind(wx.EVT_LISTBOX, self.OnBox)
        self.connect.Bind(wx.EVT_BUTTON, self.OnConnect)
        self.add.Bind(wx.EVT_BUTTON, self.OnNew)
        self.delete.Bind(wx.EVT_BUTTON, self.OnDel)
        texts = [self.profile, self.host, self.port, self.password]
        for text in texts:
            text.Bind(wx.EVT_TEXT, self.OnText)
        self.use_password.Bind(wx.EVT_CHECKBOX, self.OnCheck)
        self.Layout()
        self.connection.bind(self.connection.CONNECT, self.update)
        self.connection.bind(self.connection.CLOSE, self.update)
        self.connection.bind(self.connection.CLOSE_UNEXPECT, self.update)

    def Hide(self):
        self.ShowItems(False)
        self.parent.Layout()

    def Show(self):
        self.ShowItems(True)
        self.parent.Layout()

    def update(self):
        wx.CallAfter(self.__update)

    def __set_text(self):
        self.profile.ChangeValue(self.selected[0])
        self.host.ChangeValue(self.selected[1])
        self.port.ChangeValue(self.selected[2])
        self.use_password.SetValue(self.selected[3])
        self.password.Enable(self.selected[3])
        self.password.ChangeValue(self.selected[4])
        self.connect.Enable()
        if self.connection.current:
            if self.connection.current == self.selected:
                self.connect.Disable()
            p, host, port, up, pa = self.connection.current
            self.status.SetLabel(_('Connected %s:%s') % (host, port))
        else:
            self.status.SetLabel(_('Not Connected'))
                

    def __update(self):
        profiles = self.config.profiles
        labels = [profile[0] for profile in profiles]
        self.box.Set(labels)
        if not self.host.GetValue():
            current = self.connection.current
            self.selected = current if current else profiles[0]
            selected_index = labels.index(self.selected[0])
            if selected_index > -1:
                self.selected_index = selected_index
        if 0 < len(labels) <= self.selected_index:
            self.selected_index = len(labels) - 1
            self.selected = profiles[self.selected_index]
        if not len(labels) == 0 and not self.selected_index == -1:
            self.box.SetSelection(self.selected_index)
            self.__set_text()
        self.profiles = profiles

    def __new(self):
        profiles = self.config.profiles
        labels = [profile[0] for profile in profiles]
        new_label = u'new'
        if labels.count(new_label):
            index = 1
            while True:
                temp_label = new_label+ ' (%i)' % index
                if not labels.count(temp_label):
                    new_label = temp_label
                    break
                else:
                    index = index + 1
        new_profile = [new_label, u'localhost', u'6600', False, u'']
        profiles.append(new_profile)
        self.config.profiles = profiles
        self.selected = new_profile
        self.selected_index = len(profiles) - 1
        self.delete.Enable()
        self.__update()

    def __del(self, index):
        profiles = self.config.profiles
        del profiles[index]
        self.config.profiles = profiles
        self.__update()
        if len(profiles) <= 1:
            self.delete.Disable()

    def OnCheck(self, event):
        profiles = self.config.profiles
        current = profiles[self.selected_index][3]
        new = self.use_password.GetValue()
        profiles[self.selected_index][3] = new
        self.config.profiles = profiles
        self.password.Enable(new)

    def OnBox(self, event):
        index = self.box.GetSelection()
        if -1 < index and not index == self.selected_index:
            self.selected = self.profiles[index]
            self.selected_index = index
            self.__set_text()

    def OnText(self, event):
        obj = event.GetEventObject()
        index = {self.profile:0, self.host:1, self.port:2, self.password:4}
        profiles = self.config.profiles
        current = profiles[self.selected_index][index[obj]]
        new = obj.GetValue()
        if not new == current:
            profiles[self.selected_index][index[obj]] = new
            self.selected = profiles[self.selected_index]
            self.config.profiles = profiles
            if index[obj] == 0:
                self.box.SetString(self.selected_index, obj.GetValue())

    def OnConnect(self, event):
        self.connection.close()
        self.connection.connect(self.selected)

    def OnNew(self, event):
        self.__new()

    def OnDel(self, event):
        index = self.box.GetSelection()
        self.__del(index)


class Playback(wx.BoxSizer):
    def __init__(self, parent, client):
        params = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL, border=3)
        params_label = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT, border=3)
        params_expand = dict(flag=wx.ALL|wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL, border=3)
        wx.BoxSizer.__init__(self)
        self.parent = parent
        self.connection = client.connection
        self.playback = client.playback
        self.config = client.config
        self.__devices_list = []

        gauges = [
            (u'Volume', u'volume', 0, 100),
            (u'Crossfade', u'crossfade', 0, 10),
            ]
        sizer = wx.GridBagSizer()
        def get_slider(sizer, index, name, attr, min, max):
            label = wx.StaticText(parent, -1, _(name))
            slider = wx.Slider(parent, -1, min, min, max)
            control = wx.SpinCtrl(parent, min=min, max=max)
            control.SetValue(min)
            def OnSlider(event):
                control.SetValue(slider.GetValue())
                setattr(self.playback, str(attr), slider.GetValue())
            def OnControl(event):
                slider.SetValue(control.GetValue())
                setattr(self.playback, str(attr), control.GetValue())
            slider.Bind(wx.EVT_SCROLL, OnSlider)
            control.Bind(wx.EVT_SPINCTRL, OnControl)
            sizer.Add(label, (index*2, 0), **params_label)
            sizer.Add(slider, (index*2+1, 1), **params_expand)
            sizer.Add(control, (index*2+1, 2), **params)
            return name, attr, label, slider, control
        self.sliders = [get_slider(sizer, index, *gauge) for index, gauge in enumerate(gauges)]
        sizer.Add(wx.StaticText(parent, -1, _(u'Devices')), (len(self.sliders)*2, 0), **params_label)
        self.devices = wx.CheckListBox(parent, -1)
        self.devices.Bind(wx.EVT_CHECKLISTBOX, self.on_devices)
        sizer.Add(self.devices, (len(self.sliders)*2+1, 0), (1, 3), **params_expand)
        sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(len(self.sliders)*2+1)
        self.Add(sizer, 1, wx.ALL|wx.EXPAND, 9)
        self.Layout()
        self.update()
        self.connection.bind(self.connection.UPDATE, self.update)

    def update(self):
        if not self.parent.IsShown():
            return
        def update(devices):
            for name, attr, label, slider, control in self.sliders:
                value = getattr(self.playback, attr)
                if not control.GetValue() == value:
                    slider.SetValue(value)
                    control.SetValue(value)
            if not self.__devices_list == devices:
                self.__devices_list = devices
                if not self.devices.GetCount() == len(self.__devices_list):
                    self.devices.Clear()
                    self.devices.Set([d.name for d in self.__devices_list])
                for i, d in enumerate(self.__devices_list):
                    if not self.devices.GetString(i) == d.name:
                        self.devices.SetString(i, d.name)
                    if not self.devices.IsChecked(i) == d.is_enable():
                        self.devices.Check(i, d.is_enable())
        devices = self.playback.devices
        wx.CallAfter(update, devices)

    def on_devices(self, event):
        index = event.GetInt()
        attr = 'enable' if self.devices.IsChecked(index) else 'disable'
        getattr(self.__devices_list[index], attr)()

    def Hide(self):
        self.ShowItems(False)
        self.parent.Layout()

    def Show(self):
        self.ShowItems(True)
        self.parent.Layout()
        self.update()


