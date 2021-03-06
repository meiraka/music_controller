"""
Lyric view,  menu and dialogs.

"""

import sqlite3
import time
import urllib
import urllib2
import json
import thread
import re

from core import environment

import wx
import dialog


class LyricView(wx.Panel):
    """
    Lyric view.
    """
    def __init__(self, parent, client):
        self.client = client
        self.parent = parent
        self.bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        self.fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        self.hbg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        self.hfg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
        self.database = client.lyrics

        self.time = 0
        self.time_msec = 0.0
        self.__index = 0
        self.__offset = 0
        self.__song = None
        self.__raw_lyric = u''
        self.__lyric = []
        self.__update_interval = 100
        self.__last_speed = 0.0 # last speed in draw() add_offset
        wx.Panel.__init__(self, parent, -1)
        self.font = environment.userinterface.font
        self.timer = wx.Timer(self.parent, -1)
        wx.EVT_TIMER(self.parent, -1, self.__update)
        self.timer.Start(self.__update_interval)
        self.client.connection.bind(self.client.connection.UPDATE_PLAYING, self.update_data)
        self.client.connection.bind(self.client.connection.CONNECT, self.update_data)
        self.database.bind(self.database.UPDATING, self.update)
        self.database.bind(self.database.UPDATE, self.decode_raw_lyric)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)
        self.__update()

    def selected_get_info(self):
        dialog.SongInfo(self.parent, [self.__song])

    def update_time(self):
        """ updates LyricView managed time.
        """
        status = self.client.connection.server_status
        if status and u'time' in status:
            time = status[u'time']
            time = int(time.split(u':')[0])
            if not self.time == time:
                self.time = time
                self.time_msec = 0.0

    def update_msec(self):
        """ updates LyricView managed time(mseconds).
        """
        interval = float(self.__update_interval)/1000.0
        self.time_msec = self.time_msec + interval

    def update_data(self):
        """ update lyric data.

        call update_time(),  set current song and decode song lyric.
        """
        self.update_time()
        status = self.client.connection.server_status
        if status and u'song' in status:
            song_id = int(status[u'song'])
            if len(self.client.playlist) > song_id:
                song = self.client.playlist[song_id]
                if not self.__song == song:
                    self.__song = song
                    self.__offset = 0.0
                    self.decode_raw_lyric(song, self.database[song])

    def decode_raw_lyric(self, song, lyric):
        """ convert raw LRC lyric text to list."""
        if not self.__song == song:
            return
        self.__raw_lyric = lyric
        self.__lyric = []
        result = []
        if not lyric:
            return
        for line in lyric.split(u'\n'):
            for i in self.__decode_line(line):
                result.append(i)
        result.sort()
        if 'time' in song and song['time'].isdigit() and result:
            result.append((float(song['time']), ''))
        self.__lyric = result

    def __decode_line(self, line):
        """ convert raw LRC lyric line to tuple.

        Supports 3 types:
            [00:00.00]
            [00:00:00]
            [00:00]
        currently,  karaoke tag is not supported.
        """
        def convert_sec(time):
            sec = float(time[0])*60.0+float(time[1])
            if len(time) > 2:
                sec = sec + float(time[2])*0.01
            return sec

        matchers = [    '\\[(\\d+):(\\d+)\\.(\\d+)\\]',
                '\\[(\\d+):(\\d+):(\\d+)\\]',
                '\\[(\\d+):(\\d+)\\]']
        compiled_matcher = [re.compile(i) for i in matchers]

        for p in compiled_matcher:
            times = p.findall(line)
            if times:
                splitter = times[-1][-1]+u']'
                lyric = line.rsplit(splitter, 1)[-1]
                return [(convert_sec(mss), lyric) for mss in times]
        return []

    def OnPaint(self, event):
        self.__update(event)

    def update(self):
        """ update lyric file at main thread."""
        wx.CallAfter(self.__update)

    def __update(self, event=None):
        """ update lyric file"""
        if not self.IsShown():
            return
        dc = wx.ClientDC(self)
        if environment.userinterface.draw_double_buffered:
            dc = wx.BufferedDC(dc)
        dc.SetFont(self.font)
        dc.SetBackground(wx.Brush(self.bg))
        dc.SetPen(wx.Pen(self.bg))
        dc.SetBrush(wx.Brush(self.bg))
        dc.SetTextForeground(self.fg)
        dc.DrawRectangle(0, 0, *self.GetSize())
        x, y = self.GetPosition()
        w, h = self.GetSize()
        self.update_time()
        if self.__lyric:
            self.draw(dc, (x, y, w, h))
        else:
            if self.database.downloading.count(self.__song):
                title = u'Searching lyric...'
            else:
                title = u'Lyrics not found.'
            x = (w - dc.GetTextExtent(title)[0])/2
            y = h / 2
            dc.DrawText(title, x, y)
        self.update_msec()

    def draw(self, dc, rect):
        dc.SetPen(wx.Pen(self.hbg))
        dc.SetBrush(wx.Brush(self.hbg))

        x, y, w, h = rect
        
        # calc offset
        last_time = 0.0
        text_height = environment.userinterface.text_height
        height = text_height * 3 / 2
        current_line = -1
        break_length = text_height
        break_mux = 0.8
        break_min = 0.1

        for index, (time, line) in enumerate(self.__lyric):
            if last_time < self.time < time:
                # we draw *guess_count* times to get next line pos
                guess_count = (time-self.time-self.time_msec)/(float(self.__update_interval)/1000)
                current_line = index-1
                if guess_count>0:
                    current_diff = index*height-self.__offset
                    if current_diff < break_length:
                        if self.__last_speed:
                            add_offset = self.__last_speed * break_mux
                        else:
                            add_offset = self.__last_speed
                        if add_offset < break_min and break_min < current_diff:
                            add_offset = break_min
                            
                    else:
                        add_offset = current_diff/guess_count
                    self.__last_speed = add_offset
                    if add_offset*2 > height or abs(index*height - self.__offset) > h:
                        # too far from current pos,  jump.
                        self.__offset = index*height
                    else:
                        self.__offset = self.__offset + add_offset 
                elif guess_count >= -1:
                    # overrun
                    self.__offset = self.__offset + break_min
                    self.__last_speed = break_min
                else:
                    self.__last_speed = 0.0
                break
            else:
                last_time = time
        try:
            pos =  self.GetSize()[1] / height / 2
            for index, (time, line) in enumerate(self.__lyric):
                # do not draw line text is empty.
                if line.strip():
                    if index == current_line:
                        y = (index+pos)*height-int(self.__offset)
                        dc.DrawRectangle(0, y, self.GetSize()[0], height)
                        dc.SetTextForeground(self.hfg)
                    else:
                        dc.SetTextForeground(self.fg)
                    draw_y = (height-text_height)/2+(index+pos)*height-int(self.__offset)
                    if -height < draw_y < self.GetSize()[1]:
                        dc.DrawText(line, 12, draw_y)
        except Exception, err:
            print 'LyricView Logic Error:', err

    def OnRightClick(self, event):
        self.PopupMenu(Menu(self, self.__song))

class Menu(wx.Menu):
    """
    Lyric menu.
    """
    def __init__(self, parent, song):
        wx.Menu.__init__(self)
        self.parent = parent
        self.song = song
        items = [u'Get Info', u'Edit...', u'Download...']
        self.__items = dict([(item, wx.NewId()) for item in items])
        for item in items:
            self.Append(self.__items[item], _(item), _(item))
            func_name = item.lower().replace(' ', '_').replace('.', '')+'_item'
            self.Bind(wx.EVT_MENU, getattr(self, func_name), id=self.__items[item])

    def edit_item(self, event):
        editor = Editor(self.parent, self.parent.client, self.parent.database, self.song)
        editor.Show()

    def download_item(self, event):
        downloader = Downloader(self.parent, self.parent.client, self.song)
        downloader.Show()

    def get_info_item(self, event):
        dialog.SongInfo(self.parent, [self.song])
        
class Editor(dialog.Frame):
    """
    Lyric editor dialog.

    Supports normal text edit and timetag writer mode.
    """
    def __init__(self, parent, client, database, song):
        self.client = client
        self.parent = parent
        self.song = song
        self.db = database
        dialog.Frame.__init__(self, style=dialog.MIN_STYLE|wx.RESIZE_BORDER)
        self.SetTitle(_('Edit Lyric: %s') % song.format('%title% - %artist%'))
        toolbar_style = wx.TB_TEXT
        if environment.userinterface.toolbar_icon_horizontal:
            toolbar_style = wx.TB_HORZ_TEXT
        base = self
        if environment.userinterface.fill_window_background:
            base = wx.Panel(self, -1)
        text = wx.RadioButton(base, -1, _('Text'))
        text.Bind(wx.EVT_RADIOBUTTON, self.on_text)
        timetag = wx.RadioButton(base, -1, _('Timetag'))
        timetag.Bind(wx.EVT_RADIOBUTTON, self.on_timetag)
        self.text = wx.TextCtrl(base, -1, self.db[song], style=wx.TE_MULTILINE)
        self.text.Bind(wx.EVT_KEY_UP, self.on_keys)
        self.text.SetFocus()
        save = wx.Button(self, -1, _('Save'))
        save.Bind(wx.EVT_BUTTON, self.on_save)
        params = dict(flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL, border=3)
        sizer = wx.GridBagSizer()
        sizer.Add(text, (0, 0), **params)
        sizer.Add(timetag, (0, 1), **params)
        sizer.Add(self.text, (2, 0), (1, 4), flag=wx.EXPAND)
        sizer.Add(save, (3, 3), **params)
        sizer.AddGrowableCol(2)
        sizer.AddGrowableRow(2)
        base.SetSizer(sizer)
        if environment.userinterface.fill_window_background:
            sizer = wx.BoxSizer()
            sizer.Add(base, 1, wx.EXPAND)
            self.SetSizer(sizer)
        self.on_text(None)

    def get_current_time(self):
        """ Returns LRC formatted current time.

        Returns:
            string formatted current time.
        """
        time = self.parent.time
        msec = self.parent.time_msec
        time_text = '[%02i:%02i.%02i]' % ( time/60, time%60, int(msec*100))
        return time_text

    def replace_current_time(self):
        """ Replaces current focused line time.
        """
        time = self.get_current_time()
        # get current insertion point and line.
        lines = self.text.GetValue().split('\n')
        text_pos = self.text.GetInsertionPoint()
        line_pos = self.text.GetValue()[0:text_pos].count('\n')
        line = lines[line_pos]
        # split old time and text.
        if line.count(']') and line.startswith('['):
            old_time, line = line.split(']', 1)
        # replace time
        new_line = time + line
        lines[line_pos] = new_line
        # set time and move to next line.
        self.text.SetValue('\n'.join(lines))
        self.text.SetInsertionPoint(text_pos+len(lines[line_pos])+1)
        
    def back(self):
        """ seek back to 10 seconds.
        """
        time = self.parent.time - 10
        if time < 0:
            time = 0
        self.client.playback.seek(time)
        # updates parent mtime
        self.parent.update_time()

    def forward(self):
        """ seek forward to 10 seconds.
        """
        time = self.parent.time + 10
        self.client.playback.seek(time)
        # updates parent mtime
        self.parent.update_time()

        
    def on_keys(self, event):
        """ catch key event.

        space key -- replace focused line time.
        z     key -- back to 10 seconds.
        x     key -- forward to 10 seconds.
        """
        if not self.text.IsEditable():
            code = event.GetKeyCode()
            if code == wx.WXK_SPACE:
                self.replace_current_time()    
            elif code == ord('Z'):
                self.back()
            elif code == ord('X'):
                self.forward()
            
            
    def on_save(self, event):
        """ save event - update lyrics db.
        """
        self.db[self.song] = self.text.GetValue()

    def on_text(self, event):
        """ toolbar text button event - activates editable mode.
        """
        self.text.SetEditable(True)

    def on_timetag(self, event):
        """ toolbar timatag button event - activates timetag mode.
        """
        self.text.SetEditable(False)


class Downloader(dialog.Downloader):
    """
    Lyric Download dialog.
    """
    def __init__(self, parent, client, song):
        dialog.Downloader.__init__(self, parent, client.lyrics, song, ['title', 'artist'])
        self.SetTitle(_('Download Lyric: %s') % song.format('%title% - %artist%'))

