# -*- coding: utf-8 -*-
import urllib3
import socket
import re
import cStringIO
import random
import string
from bs4 import BeautifulSoup
import config


class ConnectionManager(object):
    def __init__(self):
        super(ConnectionManager, self).__init__()
        self.handler = ConnectionHandler(self)
        self.handlerTable = {
            u'登录成功!': self.handler.OnlineSuccessful,
            u'E010 您输入的密码无效!': self.handler.PasswordInvalid,
            u'验证码错误!': self.handler.CaptchaInvalid,
            u'E002 您的登录数已达最大并发登录数!': self.handler.InfoSimultaneity,
            u'您已登录!': self.handler.AlreadyOnline,
            u'请重新获取IP地址!': self.handler.IpNotAllowed,
            u'下线成功': self.handler.OfflineSuccessful,
            u'您已下线!': self.handler.AlreadyOffline,
            u'错误!请稍后再试!': self.handler.ServerError,
            'Session Expires': self.handler.SessionExpire
        }

        self.online = False
        self.session = self.GenerateSession()
        self.portalHeaders = {
            'User-Agent': config.USER_AGENT,
            'Cookie': "portalservice={0}".format(self.session)
        }
        self.brasHeaders = {
            'User-Agent': config.USER_AGENT,
            'Cookie': "selfservice={0}".format(self.session)
        }
        self.portalConnectionPool = urllib3.connectionpool.connection_from_url(config.URL)
        self.brasConnectionPool = urllib3.connectionpool.connection_from_url(config.BRAS_LOGIN_URL)
        self.serviceConnectionPool = urllib3.connectionpool.connection_from_url(config.LOGIN_STATS_URL)

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
        page = self.portalConnectionPool.request_encode_body(
            'POST',
            config.URL,
            postdata,
            headers=self.portalHeaders,
            encode_multipart=False
        )
        return self.HandleResponse(page.data.decode('utf-8'))

    def DoOffline(self):
        page = self.portalConnectionPool.request_encode_body(
            'POST',
            config.URL,
            {'action': 'disconnect'},
            headers=self.portalHeaders,
            encode_multipart=False
        )
        return self.HandleResponse(page.data.decode('utf-8'))

    def DoForceOffline(self, username, password):
        loginPage = self.brasConnectionPool.request_encode_body(
            'POST',
            config.BRAS_LOGIN_URL,
            {
                'login_username': username,
                'login_password': password,
                'action': 'login'
            },
            headers=self.brasHeaders,
            encode_multipart=False
        )
        if len(loginPage.data) > 100:
            raise ConnectionException(u"自助服务系统登录失败，用户名密码不正确？")

        onlineListPage = self.brasConnectionPool.request(
            'GET',
            config.BRAS_URL,
            {'action': 'online'},
            headers=self.brasHeaders
        )
        soup = BeautifulSoup(onlineListPage.data.decode('utf-8'), "html.parser")
        onlineInfo = soup.find_all(id=re.compile('^line(\d+)$'))
        for info in onlineInfo:
            sid = info['id'][4:]
            response = self.brasConnectionPool.request(
                'GET',
                config.BRAS_URL,
                {
                    'action': 'disconnect',
                    'id': sid
                },
                headers=self.brasHeaders
            )
            if u'下线成功' not in response.data.decode('utf-8'):
                raise ConnectionException("操作未成功，请至 http://bras.nju.edu.cn 手动尝试")
        return True

    def HandleResponse(self, r):
        match = re.search(ur"alert\('([^']+)'\);", r)
        if match is None:
            error = 'Session Expires'
        else:
            error = match.group(1)
        if error in self.handlerTable:
            return self.handlerTable[error]()
        else:
            raise ConnectionException(u"未知错误：" + error)

    def GetCaptchaImage(self):
        try:
            image = self.portalConnectionPool.request('GET', config.IMG_URL, headers=self.portalHeaders)
            output = cStringIO.StringIO(image.data)
            return output
        except Exception as e:
            raise ConnectionException(e.message)

    def GenerateSession(self):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(26))

    def UpdateStatus(self):
        try:
            page = self.portalConnectionPool.request('GET', config.URL, timeout=3, headers=self.portalHeaders)
            html = page.data.decode('utf-8')
            if u'在线时长' in html:
                self.online = True
            else:
                self.online = False
            return self.online
        except (urllib3.exceptions.HTTPError, socket.timeout):
            raise UpdateStatusException

    def SendOnlineStatistics(self):
        try:
            page = self.portalConnectionPool.request('GET', config.URL, headers=self.portalHeaders)
            soup = BeautifulSoup(page.data.decode('utf-8'), "html.parser")
            profile = soup.table.table.find_all("td")
            studentId = profile[5].text.encode('utf-8')
            loginTime = profile[6].text.encode('utf-8')
            ip = profile[8].text.encode('utf-8')
            location = profile[9].text.encode('utf-8')
            postdata = {
                'student_id': studentId,
                'login_time': loginTime,
                'ip': ip,
                'location': location
            }
            self.serviceConnectionPool.request_encode_body(
                'POST',
                config.LOGIN_STATS_URL,
                postdata,
                encode_multipart=False
            )
        except:
            pass


class ConnectionHandler(object):
    def __init__(self, manager):
        super(ConnectionHandler, self).__init__()
        self.manager = manager

    def OnlineSuccessful(self):
        self.manager.online = True
        return True

    def PasswordInvalid(self):
        raise ConnectionException(u"用户名或密码错误，请至设置窗口修改")

    def CaptchaInvalid(self):
        raise CaptchaException

    def InfoSimultaneity(self):
        raise ConnectionException(u"同一帐号已在别处登录，请使用强制下线功能")

    def AlreadyOnline(self):
        self.manager.online = True
        raise ConnectionException(u"已经处于在线状态")

    def IpNotAllowed(self):
        raise ConnectionException(u"IP不在允许登录范围内")

    def OfflineSuccessful(self):
        self.manager.online = False
        return True

    def AlreadyOffline(self):
        self.manager.online = False
        raise ConnectionException(u"已经处于离线状态")

    def ServerError(self):
        raise ConnectionException(u"服务器太忙，无法响应你的请求")

    def SessionExpire(self):
        self.manager.session = self.manager.GenerateSession()
        raise ConnectionException(u"会话超时，请重试")


class ConnectionException(Exception):
    pass


class CaptchaException(ConnectionException):
    pass


class UpdateStatusException(ConnectionException):
    pass
