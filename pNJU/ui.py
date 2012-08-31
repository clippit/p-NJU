# -*- coding: utf-8 -*-
from os.path import dirname, join
import string
import wx
from wx import xrc
from userdata import Preference
from connection import ConnectionManager, ConnectionException, CaptchaException

# Resource Directory
res_path = join(dirname(dirname(__file__)), "res")


class MainApp(wx.App):
    def OnInit(self):
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

        self.icons = {
            'online': wx.Image(join(res_path, 'icon-online.png'), wx.BITMAP_TYPE_PNG),
            'offline': wx.Image(join(res_path, 'icon-offline.png'), wx.BITMAP_TYPE_PNG)
        }

        self.Bind(wx.EVT_MENU, self.OnAbout, id=self.TBMENU_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnPreference, id=self.TBMENU_PREFERENCE)
        self.Bind(wx.EVT_MENU, self.OnOnline, id=self.TBMENU_ONLINE)
        self.Bind(wx.EVT_MENU, self.OnExit, id=self.TBMENU_EXIT)

        self.pref = Preference()
        self.connection = ConnectionManager()
        self.UpdateIcon(force=True)

    def MakeIcon(self, status="offline"):
        if status not in ('online', 'offline'):
            status = 'offline'

        image = self.icons[status]
        if "wxMSW" in wx.PlatformInfo:
            image = image.Scale(16, 16)
        elif "wxGTK" in wx.PlatformInfo:
            image = image.Scale(22, 22)

        return wx.IconFromBitmap(image.ConvertToBitmap())

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.TBMENU_ABOUT, u"关于")
        menu.Append(self.TBMENU_PREFERENCE, u"设置")
        menu.AppendSeparator()
        onlineItem = menu.AppendCheckItem(self.TBMENU_ONLINE, u"连接")
        menu.Append(self.TBMENU_EXIT, u"退出")

        if self.connection.IsOnline():
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
        usernameTextCtrl = xrc.XRCCTRL(prefDialog, 'usernameTextCtrl')
        passwordTextCtrl = xrc.XRCCTRL(prefDialog, 'passwordTextCtrl')
        autoConnectCheckBox = xrc.XRCCTRL(prefDialog, 'autoConnectCheckBox')
        statisticsCheckBox = xrc.XRCCTRL(prefDialog, 'statisticsCheckBox')

        usernameTextCtrl.SetValue(self.pref.Get('username'))
        passwordTextCtrl.SetValue(self.pref.Get('password'))
        autoConnectCheckBox.SetValue(self.pref.Get('autoConnectEnabled'))
        statisticsCheckBox.SetValue(self.pref.Get('statisticsEnabled'))

        usernameTextCtrl.SetValidator(LoginValidator())
        passwordTextCtrl.SetValidator(LoginValidator())

        if prefDialog.ShowModal() == wx.ID_OK:
            username = usernameTextCtrl.GetValue()
            password = passwordTextCtrl.GetValue()
            autoConnectEnabled = autoConnectCheckBox.GetValue()
            statisticsEnabled = statisticsCheckBox.GetValue()
            self.SavePreference(username=username, password=password, autoConnectEnabled=autoConnectEnabled, statisticsEnabled=statisticsEnabled)

        prefDialog.Destroy()

    def OnOnline(self, event):
        if not self.connection.IsOnline():  # offline
            self.DoOnline()
        else:
            self.DoOffline()

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
        while True:
            try:
                if self.connection.DoOnline(self.pref.Get('username'), self.pref.Get('password'), self.GetCaptcha()):
                    if "wxMSW" in wx.PlatformInfo:
                        self.ShowBalloon("pNJU", u"登录成功")
            except CancelLoginException:
                return
            except CaptchaException:
                if "wxMSW" in wx.PlatformInfo:
                    self.ShowBalloon(u"pNJU 登录失败", u"验证码错误")
                continue
            except ConnectionException as e:
                if "wxMSW" in wx.PlatformInfo:
                    self.ShowBalloon(u"pNJU 登录失败", e.message)
                break
            except:
                raise
            else:
                break
        self.UpdateIcon()

    def DoOffline(self):
        try:
            if self.connection.DoOffline():
                if "wxMSW" in wx.PlatformInfo:
                    self.ShowBalloon("pNJU", u"下线成功")
        except ConnectionException as e:
            if "wxMSW" in wx.PlatformInfo:
                self.ShowBalloon(u"pNJU 下线失败", e.message)
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

    def UpdateIcon(self, force=False, info=None):
        if self.connection.IsOnline(force):
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
