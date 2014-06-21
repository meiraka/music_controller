"""
Main application window.

"""

import wx

from common import Object
from common import environment
import toolbar
import playlist
import listfilter
import songinfo
import lyrics
import menubar
import preferences


class Frame(wx.Frame, Object):
    TITLE = 'MusicController'
    VIEW = 'view'
    VIEW_LIST = u'List'
    VIEW_LIST_GRID = u'List Grid'
    VIEW_GRID = u'Grid'
    VIEW_LISTFILTER = u'ListFilter'
    VIEW_LYRIC = u'Lyric'
    VIEW_STYLES = [VIEW_LIST, VIEW_LIST_GRID, VIEW_GRID,
                   VIEW_LISTFILTER,  VIEW_LYRIC]

    def __init__(self, parent, client, debug=False):
        """ generate main app window."""
        self.parent = parent
        self.client = client
        if self.client.config.view not in self.VIEW_STYLES:
            self.client.config.view = self.VIEW_STYLES[0]
        wx.Frame.__init__(self, parent, -1)
        Object.__init__(self)
        self.SetTitle(self.TITLE)
        icon = wx.ArtProvider.GetIcon('gtk-media-play-ltr', size=(128, 128))
        if icon.IsOk():
            self.SetIcon(icon)

        self.menubar = menubar.MenuBar(self, client,
                                       environment.userinterface.accele)
        # add mac Help -> search item. (not work)
        wx.GetApp().SetMacHelpMenuTitleName(_('Help'))
        self.SetMenuBar(self.menubar)
        self.toolbar = toolbar.Toolbar(self, self.client)
        if environment.userinterface.fill_window_background:
            base = wx.Panel(self, -1)
        else:
            base = self
        self.playlist = playlist.HeaderPlaylist(base, self.client, debug)
        self.listfilter = listfilter.View(base, self.client, debug)
        self.albumlist = playlist.AlbumList(base, self.client, False)
        self.albumview = playlist.AlbumList(base, self.client, True)
        self.info = songinfo.Info(base, self.client, debug)
        self.connection = preferences.Connection(base, self.client)
        self.lyric = lyrics.LyricView(base, self.client)
        self.views = [
            self.connection,
            self.playlist,
            self.albumlist,
            self.albumview,
            self.lyric,
            self.listfilter]
        self.sizer = wx.BoxSizer()
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(self.playlist, 1, flag=wx.EXPAND)
        s.Add(self.listfilter, 1, flag=wx.EXPAND)
        s.Add(self.connection, 1, flag=wx.EXPAND)
        s.Add(self.lyric, 1, flag=wx.EXPAND)
        s.Add(self.albumlist, 0, flag=wx.EXPAND)
        s.Add(self.albumview, 1, flag=wx.EXPAND)
        self.sizer.Add(s, 1, flag=wx.EXPAND)
        self.sizer.Add(self.info, 0, wx.EXPAND)
        base.SetSizer(self.sizer)
        if environment.userinterface.fill_window_background:
            sizer = wx.BoxSizer()
            sizer.Add(base, 1, wx.EXPAND)
            self.SetSizer(sizer)
        self.hide_children()
        self.Layout()
        window_size = self.client.config.window_size
        if window_size == (-1, -1):
            h = environment.userinterface.text_height
            self.SetSize((h*64, h*48))
        else:
            w, h = window_size
            if w < 100:
                w = 100
            if h < 100:
                h = 100
            self.SetSize((w, h))
        self.preferences = None
        self.change_title()
        if self.client.connection.current:
            self.show_not_connection()
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Show()
        self.client.connection.bind(self.client.connection.UPDATE_PLAYING,
                                    self.change_title)

    def can_get_info(self):
        for view in self.views:
            if (
                    hasattr(view, 'selected_get_info')
                    and hasattr(view, 'IsShown')
                    and view.IsShown()):
                return True
        else:
            return False

    def get_info(self):
        for view in self.views:
            if (
                    hasattr(view, 'selected_get_info')
                    and hasattr(view, 'IsShown')
                    and view.IsShown()):
                view.selected_get_info()

    def hide_children(self):
        self.playlist.Hide()
        self.albumlist.Hide()
        self.albumview.Hide()
        self.listfilter.Hide()
        self.connection.Hide()
        self.info.Hide()
        self.lyric.Hide()

    def show_connection(self):
        self.SetTitle(self.TITLE + ' - ' + 'connection')
        self.__show_views(self.connection)
        self.info.Hide()

    def show_not_connection(self):
        if not self.client.config.view:
            if len(self.client.playlist):
                self.show_playlist()
            else:
                self.show_songlistfilter()
        else:
            try:
                self.show_view(self.client.config.view)
            except AttributeError:
                self.show_list()

    def __update_infoview(self):
        if self.client.config.info:
            self.info.Show()
        else:
            self.info.Hide()

    def show_view(self,  view):
        getattr(self,  'show_' + view.lower().replace(' ',  '_'))()

    def __show_views(self,  *shows):
        self.change_title()
        views = [
            self.connection,
            self.playlist,
            self.albumlist,
            self.albumview,
            self.lyric,
            self.listfilter]
        for view in views:
            if view not in shows:
                view.Hide()
        self.Layout()
        for view in shows:
            view.Show()
            if hasattr(view, 'SetFocus'):
                view.SetFocus()
        self.__update_infoview()
        self.Layout()
        self.call(self.VIEW)

    def show_listfilter(self):
        """ Show listfilter and song info."""
        self.client.config.view = self.VIEW_LISTFILTER
        self.__show_views(self.listfilter)

    def show_list(self):
        self.client.config.view = self.VIEW_LIST
        self.__show_views(self.playlist)

    def show_list_grid(self):
        self.client.config.view = self.VIEW_LIST_GRID
        self.__show_views(self.albumlist,  self.playlist)

    def show_grid(self):
        self.client.config.view = self.VIEW_GRID
        self.__show_views(self.albumview)

    def show_lyric(self):
        """ Show lyric and song info."""
        self.client.config.view = self.VIEW_LYRIC
        self.__show_views(self.lyric)

    def __get_search_view(self):
        if self.playlist.IsShown():
            return self.playlist
        elif self.listfilter.IsShown():
            return self.listfilter
        else:
            return None

    def search_focus(self):
        view = self.__get_search_view()
        if view:
            self.toolbar.search.SetFocus()

    def search_unfocus(self):
        view = self.__get_search_view()
        if view:
            view.SetFocus()

    def search_first(self, text):
        view = self.__get_search_view()
        if view:
            view.search_first(text)

    def search_next(self):
        view = self.__get_search_view()
        if view:
            view.search_next()

    def change_title(self):
        wx.CallAfter(self.__change_title)

    def __change_title(self):
        status = self.client.connection.server_status
        title = self.TITLE
        if status and u'song' in status:
            song_id = int(status[u'song'])
            if len(self.client.playlist) > song_id:
                song = self.client.playlist[song_id]
                title = self.TITLE + u' - ' + song.format('%title% - %artist%')
        self.SetTitle(title)

    def show_preferences(self):
        if not self.preferences:
            def hide(event):
                event.GetEventObject().Hide()
            self.preferences = preferences.App(None, self.client)
            self.preferences.Bind(wx.EVT_CLOSE, hide)

        self.preferences.Show()

    def OnSize(self, event):
        self.client.config.window_size = self.GetSize()
        event.Skip()
