# -*- coding: utf-8 -*-
import wx


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        self.InitUI()

    def InitUI(self):
        self.SetSize((300, 200))
        self.SetTitle('pNJU')
        self.SetTaskBarIcon()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def SetTaskBarIcon(self):
        if not wx.TaskBarIcon.IsAvailable():
            wx.MessageBox(
                'There appears to be no system tray support in your current environment. This app may not work correctly.',
                "pNJU Warning",
                wx.OK | wx.ICON_EXCLAMATION
            )
        self.tbicon = MainTaskBarIcon(self)

    def OnClose(self, event):
        if self.tbicon is not None:
            self.tbicon.Destroy()
        self.Destroy()


class MainTaskBarIcon(wx.TaskBarIcon):
    TBMENU_ABOUT = wx.ID_ABOUT
    TBMENU_PREFERENCE = wx.ID_PREFERENCES
    TBMENU_ONLINE = wx.NewId()
    TBMENU_EXIT = wx.ID_EXIT

    def __init__(self, frame):
        super(MainTaskBarIcon, self).__init__(wx.TBI_CUSTOM_STATUSITEM)
        self.frame = frame
        self.SetIcon(self.MakeIcon(), u'pNJU测试')

        self.Bind(wx.EVT_MENU, self.OnAbout, id=self.TBMENU_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnPreference, id=self.TBMENU_PREFERENCE)
        self.Bind(wx.EVT_MENU, self.OnOnline, id=self.TBMENU_ONLINE)
        self.Bind(wx.EVT_MENU, self.OnExit, id=self.TBMENU_EXIT)

        self.online = False

    def MakeIcon(self):
        bmp = wx.EmptyBitmap(16, 16)
        dc = wx.MemoryDC(bmp)
        dc.SetBrush(wx.RED_BRUSH)
        dc.Clear()
        dc.SelectObject(wx.NullBitmap)

        testicon = wx.EmptyIcon()
        testicon.CopyFromBitmap(bmp)
        return testicon

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.TBMENU_ABOUT, u"关于")
        menu.Append(self.TBMENU_PREFERENCE, u"设置")
        menu.AppendSeparator()
        onlineItem = menu.AppendCheckItem(self.TBMENU_ONLINE, u"连接")
        menu.Append(self.TBMENU_EXIT, u"退出")

        if self.online:
            onlineItem.Check()

        return menu

    def OnAbout(self, event):
        print "about"

    def OnPreference(self, event):
        print "preference"

    def OnOnline(self, event):
        if self.online:
            print 'turn offline'
        else:
            print 'turn online'
        self.online = not self.online

    def OnExit(self, event):
        self.RemoveIcon()
        self.frame.Close()
