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
        info = wx.AboutDialogInfo()
        info.SetName('pNJU')
        info.SetVersion('0.9')
        info.SetDescription(u"南京大学校园网连接助手")
        info.SetWebSite('http://pnju.dayanjia.com')
        info.AddDeveloper('Clippit')
        wx.AboutBox(info)

    def OnPreference(self, event):
        prefDialog = PreferenceDialog(None)
        prefDialog.ShowModal()
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


class PreferenceDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        super(PreferenceDialog, self).__init__(*args, **kwargs)

        self.InitUI()
        self.SetSize((250, 200))
        self.SetTitle(u"偏好设置")

    def InitUI(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        panel = wx.Panel(self)
        prefSizer = wx.BoxSizer(wx.VERTICAL)

        usernameBox = wx.BoxSizer(wx.HORIZONTAL)
        usernameBox.Add(wx.StaticText(panel, label=u'用户名', style=wx.ALIGN_RIGHT))
        usernameBox.Add(wx.TextCtrl(panel), border=5)
        prefSizer.Add(usernameBox)

        passwordBox = wx.BoxSizer(wx.HORIZONTAL)
        passwordBox.Add(wx.StaticText(panel, label=u'密码', style=wx.ALIGN_RIGHT))
        passwordBox.Add(wx.TextCtrl(panel), flag=wx.TE_PASSWORD, border=5)
        prefSizer.Add(passwordBox)

        autoConnectCheckBox = wx.CheckBox(panel, label=u'在校园网内自动连接（暂未实现）')
        prefSizer.Add(autoConnectCheckBox)

        statisticCheckBox = wx.CheckBox(panel, label=u'帮助改善本程序')
        prefSizer.Add(statisticCheckBox)

        panel.SetSizer(prefSizer)

        btnSizer = wx.StdDialogButtonSizer()

        okButton = wx.Button(self, wx.ID_OK, u"确定")
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL, u"取消")
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()

        sizer.Add(panel, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.Add(btnSizer, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
        self.SetSizer(sizer)
