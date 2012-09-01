# -*- coding: utf-8 -*-
from contextlib import closing
from urllib import urlencode
import urllib2
import re
import cStringIO
import random
import string
import config


class ConnectionManager(object):
    INFO_SESSION_ERROR = 0
    INFO_ONLINE_SUCCESSFUL = 100
    INFO_PASSWORF_INVALID = 101
    INFO_CAPTCHA_INVALID = 102
    INFO_SIMULTANEITY = 103
    INFO_ALREADY_ONLINE = 104
    INFO_OFFLINE_SUCCESSFUL = 200
    INFO_ALREADY_OFFLINE = 201
    INFO_SERVER_ERROR = 301
    infoTable = {
        u'登录成功!': INFO_ONLINE_SUCCESSFUL,
        u'E010 您输入的密码无效!': INFO_PASSWORF_INVALID,
        u'验证码错误!': INFO_CAPTCHA_INVALID,
        u'E002 您的登录数已达最大并发登录数!': INFO_SIMULTANEITY,
        u'您已登录!': INFO_ALREADY_ONLINE,
        u'下线成功': INFO_OFFLINE_SUCCESSFUL,
        u'您已下线!': INFO_ALREADY_OFFLINE,
        u'错误!请稍后再试!': INFO_SERVER_ERROR
    }

    def __init__(self):
        super(ConnectionManager, self).__init__()
        self.online = False
        self.session = self.GenerateSession()

    def IsOnline(self, force=False):
        return self.UpdateStatus() if force else self.online

    def DoOnline(self, username, password, captcha):
        postdata = {
            'action': 'login',
            'url': 'http://p.nju.edu.cn',
            'p_login': 'p_login',
            'login_username': username,
            'login_password': password,
            'login_code': captcha
        }
        request = urllib2.Request(config.URL, urlencode(postdata))
        request.add_header('User-Agent', config.USER_AGENT)
        request.add_header('Cookie', "portalservice={0}".format(self.session))
        try:
            with closing(urllib2.urlopen(request)) as page:
                response = self.ParseResponse(page.read().decode('utf-8'))
        except Exception as e:
            raise ConnectionException(e.message)

        if response == self.INFO_ONLINE_SUCCESSFUL:
            self.online = True
            return True
        elif response == self.INFO_PASSWORF_INVALID:
            raise ConnectionException(u"用户名或密码错误，请至设置窗口修改")
        elif response == self.INFO_CAPTCHA_INVALID:
            raise CaptchaException
        elif response == self.INFO_SIMULTANEITY:
            raise ConnectionException(u"同一帐号已在别处登录，请至http://bras.nju.edu.cn手动下线")
        elif response == self.INFO_ALREADY_ONLINE:
            self.online = True
            raise ConnectionException(u"已经处于在线状态")
        elif response == self.INFO_SESSION_ERROR:
            self.session = self.GenerateSession()
            raise ConnectionException(u"会话超时，请重试")
        elif response == self.INFO_SERVER_ERROR:
            raise ConnectionException(u"服务器太忙，无法响应你的请求")
        else:
            raise ConnectionException(response)

    def DoOffline(self):
        request = urllib2.Request(config.URL, "action=disconnect")
        request.add_header('User-Agent', config.USER_AGENT)
        try:
            with closing(urllib2.urlopen(request)) as page:
                response = self.ParseResponse(page.read().decode('utf-8'))
        except Exception as e:
            raise ConnectionException(e.message)

        if response == self.INFO_OFFLINE_SUCCESSFUL:
            self.online = False
            return True
        elif response == self.INFO_ALREADY_OFFLINE:
            self.online = False
            raise ConnectionException(u"已经处于离线状态")
        elif response == self.INFO_SERVER_ERROR:
            raise ConnectionException(u"服务器太忙，无法响应你的请求")
        else:
            raise ConnectionException(response)

    def ParseResponse(self, r):
        match = re.search(ur"alert\('([^']+)'\);", r)
        if match is None:
            return self.INFO_SESSION_ERROR
        error = match.group(1)
        if error in self.infoTable:
            return self.infoTable[error]
        else:
            return u"未知错误：" + error

    def GetCaptchaImage(self):
        request = urllib2.Request(config.IMG_URL)
        request.add_header('User-Agent', config.USER_AGENT)
        request.add_header('Cookie', "portalservice={0}".format(self.session))
        try:
            with closing(urllib2.urlopen(request)) as image:
                response = image.read()
            output = cStringIO.StringIO(response)
            return output
        except Exception as e:
            raise ConnectionException(e.message)

    def GenerateSession(self):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(26))

    def UpdateStatus(self):
        try:
            with closing(urllib2.urlopen(config.URL)) as page:
                html = page.read().decode('utf-8')
            if u'在线时长' in html:
                self.online = True
            else:
                self.online = False
            return self.online
        except urllib2.URLError:
            raise ConnectionException(u'获取在线信息失败')


class ConnectionException(Exception):
    pass


class CaptchaException(ConnectionException):
    pass
