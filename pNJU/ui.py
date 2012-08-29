# -*- coding: utf-8 -*-
from os.path import dirname, join
import wx
from wx import xrc


class MainApp(wx.App):
    def OnInit(self):
        res_path = join(dirname(dirname(__file__)), "res")
        xrc.XmlResource.Get().LoadFile(join(res_path, "resources.xrc"))
        self.frame = MainFrame(None)
        return True


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        self.Init()

    def Init(self):
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
        info = wx.AboutDialogInfo()
        info.SetName('pNJU')
        info.SetVersion('0.9')
        info.SetDescription(u"南京大学校园网连接助手")
        info.SetWebSite('http://pnju.dayanjia.com')
        info.AddDeveloper('Clippit')
        wx.AboutBox(info)

    def OnPreference(self, event):
        prefDialog = xrc.XmlResource.Get().LoadDialog(None, 'prefDialog')
        if prefDialog.ShowModal() == wx.ID_OK:
            print 'ok'  # Read preferences and save
            username = xrc.XRCCTRL(prefDialog, 'usernameTextCtrl').GetValue()
            password = xrc.XRCCTRL(prefDialog, 'passwordTextCtrl').GetValue()
            autoConnectEnabled = xrc.XRCCTRL(prefDialog, 'autoConnectCheckBox').GetValue()
            statisticsEnabled = xrc.XRCCTRL(prefDialog, 'statisticsCheckBox').GetValue()
            print username, password, autoConnectEnabled, statisticsEnabled
        prefDialog.Destroy()

    def OnOnline(self, event):
        if self.online:
            print 'turn offline'
        else:
            print 'turn online'
        self.online = not self.online

    def OnExit(self, event):
        self.RemoveIcon()
        self.frame.Close()
