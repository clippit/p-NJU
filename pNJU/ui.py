# -*- coding: utf-8 -*-
from os.path import dirname, join
import sys
import string
import wx
from wx import xrc
from userdata import Preference
from connection import ConnectionManager, ConnectionException, CaptchaException, UpdateStatusException

# Resource Directory
if getattr(sys, 'frozen', None):
    basedir = sys._MEIPASS
else:
    basedir = dirname(dirname(__file__))
res_path = join(basedir, "res")


class MainApp(wx.App):
    def OnInit(self):
        xrc.XmlResource.Get().LoadFile(join(res_path, "resources.xrc"))
        self.frame = MainFrame(None, style=wx.FRAME_NO_TASKBAR)
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
        self.Show(False)

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
    TBMENU_FORCE_OFFLINE = wx.NewId()
    TBMENU_ONLINE = wx.NewId()
    TBMENU_EXIT = wx.ID_EXIT

    def __init__(self, frame):
        super(MainTaskBarIcon, self).__init__(wx.TBI_CUSTOM_STATUSITEM)
        self.frame = frame

        self.icons = {
            'online': wx.Image(join(res_path, 'icon-online.png'), wx.BITMAP_TYPE_PNG),
            'offline': wx.Image(join(res_path, 'icon-offline.png'), wx.BITMAP_TYPE_PNG)
        }

        self.Bind(wx.EVT_MENU, self.OnAbout, id=self.TBMENU_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnPreference, id=self.TBMENU_PREFERENCE)
        self.Bind(wx.EVT_MENU, self.OnForceOffline, id=self.TBMENU_FORCE_OFFLINE)
        self.Bind(wx.EVT_MENU, self.OnOnline, id=self.TBMENU_ONLINE)
        self.Bind(wx.EVT_MENU, self.OnExit, id=self.TBMENU_EXIT)

        self.pref = Preference()
        self.connection = ConnectionManager()
        self.SetIcon(self.MakeIcon('offline'), 'pNJU')
        self.UpdateIcon(force=True)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.TBMENU_ABOUT, u"关于")
        menu.Append(self.TBMENU_PREFERENCE, u"设置")
        menu.AppendSeparator()
        menu.Append(self.TBMENU_FORCE_OFFLINE, u"强制下线")
        menu.AppendSeparator()
        onlineItem = menu.AppendCheckItem(self.TBMENU_ONLINE, u"连接")
        menu.Append(self.TBMENU_EXIT, u"退出")

        if self.connection.IsOnline():
            onlineItem.Check()

        return menu

    def OnAbout(self, event):
        licence = """Copyright (c) 2012 Letian Zhang

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""

        info = wx.AboutDialogInfo()
        info.SetName('pNJU')
        info.SetVersion('0.1')
        info.SetDescription(u"南京大学校园网连接助手")
        info.SetCopyright(u'Copyright © 2012 Letian Zhang')
        info.SetWebSite('http://pnju.dayanjia.com')
        info.SetLicence(licence)
        info.AddDeveloper('Clippit')
        icon = wx.Image(join(res_path, "icon-online.png")).Scale(128, 128)
        info.SetIcon(wx.IconFromBitmap(wx.BitmapFromImage(icon)))
        wx.AboutBox(info)

    def OnPreference(self, event):
        prefDialog = xrc.XmlResource.Get().LoadDialog(None, 'prefDialog')
        usernameTextCtrl = xrc.XRCCTRL(prefDialog, 'usernameTextCtrl')
        passwordTextCtrl = xrc.XRCCTRL(prefDialog, 'passwordTextCtrl')
        autoRetryCheckBox = xrc.XRCCTRL(prefDialog, 'autoRetryCheckBox')
        autoConnectCheckBox = xrc.XRCCTRL(prefDialog, 'autoConnectCheckBox')
        statisticsCheckBox = xrc.XRCCTRL(prefDialog, 'statisticsCheckBox')

        usernameTextCtrl.SetValue(self.pref.Get('username'))
        passwordTextCtrl.SetValue(self.pref.Get('password'))
        autoRetryCheckBox.SetValue(self.pref.Get('autoRetryEnabled'))
        autoConnectCheckBox.SetValue(self.pref.Get('autoConnectEnabled'))
        statisticsCheckBox.SetValue(self.pref.Get('statisticsEnabled'))

        usernameTextCtrl.SetValidator(LoginValidator())
        passwordTextCtrl.SetValidator(LoginValidator())

        if prefDialog.ShowModal() == wx.ID_OK:
            self.SavePreference(
                username=usernameTextCtrl.GetValue(),
                password=passwordTextCtrl.GetValue(),
                autoRetryEnabled=autoRetryCheckBox.GetValue(),
                autoConnectEnabled=autoConnectCheckBox.GetValue(),
                statisticsEnabled=statisticsCheckBox.GetValue()
            )

        prefDialog.Destroy()

    def OnOnline(self, event):
        if not self.connection.IsOnline():
            # Check if username and password are set
            if not all((self.pref.Get('username'), self.pref.Get('password'))):
                wx.MessageBox(
                    u'用户名密码尚未设置。',
                    u"pNJU 错误",
                    wx.OK | wx.ICON_EXCLAMATION
                )
                return self.ProcessEvent(wx.PyCommandEvent(wx.EVT_MENU.typeId, self.TBMENU_PREFERENCE))

            if self.pref.Get('autoRetryEnabled'):
                success = self.DoOnlineAutoRetry()
            else:
                success = self.DoOnline()
            if success and self.pref.Get('statisticsEnabled', True):
                self.connection.SendOnlineStatistics()
        else:
            self.DoOffline()

    def OnForceOffline(self, event):
        confirm = wx.MessageBox(
            u"本操作将会强制清除你帐号的在线会话，可用于解决“在线数量限制”错误，可能会导致其他正在使用你的帐号上网的设备网络中断。确定是否继续？",
            u"pNJU 操作确认",
            wx.YES_NO | wx.NO_DEFAULT
        )
        if confirm == wx.YES:
            self.DoForceOffline()

    def OnExit(self, event):
        self.RemoveIcon()
        self.frame.Close()

    def SavePreference(self, *args, **kwargs):
        try:
            self.pref.Save(**kwargs)
        except Exception as e:
            wx.MessageBox(
                u"保存设置失败！\n" + e.message,
                u"错误",
                wx.OK | wx.ICON_ERROR
            )

    def DoOnline(self):
        self.UpdateIcon(info=u"工作中...")
        success = False
        while True:
            try:
                success = self.connection.DoOnline(
                    self.pref.Get('username'),
                    self.pref.Get('password'),
                    self.GetCaptcha()
                )
                if success:
                    self.Notification("pNJU", u"登录成功")
            except CancelLoginException:
                return
            except CaptchaException:
                self.Notification(u"pNJU 登录失败", u"验证码错误")
                continue
            except ConnectionException as e:
                self.Notification(u"pNJU 登录失败", e.message)
                break
            except:
                raise
            else:
                break
        self.UpdateIcon()
        return success

    def DoOnlineAutoRetry(self):
        self.UpdateIcon(info=u"工作中...")
        try:
            self.connection.GetCaptchaImage()  # In order to send our session id to server
        except ConnectionException as e:
            self.Notification(u"pNJU 操作失败，请重试", e.message)
            return False

        retry = 10
        while retry:
            try:
                if self.connection.DoOnline(self.pref.Get('username'), self.pref.Get('password'), retry % 10):
                    self.Notification("pNJU", u"登录成功")
                    self.UpdateIcon()
                    return True
            except CaptchaException:
                retry = retry - 1
                continue
            except ConnectionException as e:
                self.Notification(u"pNJU 登录失败", e.message)
                self.UpdateIcon()
                return False
            except:
                raise
        # Auto retry failed if we reach here, turn to traditional method
        return self.DoOnline()

    def DoOffline(self):
        self.UpdateIcon(info=u"工作中...")
        try:
            if self.connection.DoOffline():
                self.Notification("pNJU", u"下线成功")
        except ConnectionException as e:
            self.Notification(u"pNJU 下线失败", e.message)
        finally:
            self.UpdateIcon()

    def DoForceOffline(self):
        self.UpdateIcon(info=u"工作中...")
        try:
            if self.connection.DoForceOffline(self.pref.Get('username'), self.pref.Get('password')):
                self.Notification("pNJU", u"已清除其他连接会话")
        except ConnectionException as e:
            self.Notification(u"pNJU 强制下线失败", e.message)
        finally:
            self.UpdateIcon()

    def GetCaptcha(self):
        captchaImage = wx.BitmapFromImage(wx.ImageFromStream(self.connection.GetCaptchaImage()))
        captchaDialog = xrc.XmlResource.Get().LoadDialog(None, 'captchaDialog')
        captchaBitmap = xrc.XRCCTRL(captchaDialog, 'captchaBitmap')
        captchaBitmap.SetBitmap(captchaImage)
        captchaTextCtrl = xrc.XRCCTRL(captchaDialog, 'captchaTextCtrl')

        if captchaDialog.ShowModal() == wx.ID_OK:
            captcha = captchaTextCtrl.GetValue()
            captchaDialog.Destroy()
            if len(captcha) == 0:
                raise CancelLoginException
            else:
                return captcha
        else:
            captchaDialog.Destroy()
            raise CancelLoginException

    def MakeIcon(self, status="offline"):
        if status not in ('online', 'offline'):
            status = 'offline'

        image = self.icons[status]
        if "wxMac" in wx.PlatformInfo:
            image = image.Scale(32, 32)
        elif "wxGTK" in wx.PlatformInfo:
            image = image.Scale(22, 22)
        image = image.Scale(16, 16)  # Windows and others
        return wx.IconFromBitmap(image.ConvertToBitmap())

    def UpdateIcon(self, force=False, info=None):
        try:
            isOnline = self.connection.IsOnline(force)
        except UpdateStatusException:
            return

        if isOnline:
            status = u"在线"
            icon = 'online'
        else:
            status = u"离线"
            icon = 'offline'

        if info == None:
            tooltip = string.join(("pNJU", status), " - ")
        else:
            tooltip = string.join(("pNJU", status, info), " - ")

        self.SetIcon(self.MakeIcon(icon), tooltip)

    def Notification(self, title, content, timeout=5):
        title = unicode(title)
        content = unicode(content)
        if "wxMSW" in wx.PlatformInfo:
            self.ShowBalloon(title, content, timeout * 1000, wx.ICON_INFORMATION)
        else:
            wx.NotificationMessage(title, content).Show(timeout)


class LoginValidator(wx.PyValidator):
    def Clone(self):
        return LoginValidator()

    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()

        if len(text) == 0:
            wx.MessageBox(u"用户名和密码必须填写！", u"错误", wx.OK | wx.ICON_EXCLAMATION)
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True

    def TransferToWindow(self):
        return True  # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return True  # Prevent wxDialog from complaining.


class CancelLoginException(Exception):
    pass
