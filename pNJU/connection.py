# -*- coding: utf-8 -*-
import urllib3
import re
import cStringIO
import random
import string
from datetime import date
from bs4 import BeautifulSoup
from . import __version__
import config


class ConnectionManager(object):
    def __init__(self):
        super(ConnectionManager, self).__init__()
        self.handler = ConnectionHandler(self)
        self.handlerTable = {
            #u'登录成功!': self.handler.OnlineSuccessful,
            u'E012 未发现此用户!': self.handler.PasswordInvalid,
            u'E010 您输入的密码无效!': self.handler.PasswordInvalid,
            u'验证码错误!': self.handler.CaptchaInvalid,
            u'验证码不正确!': self.handler.CaptchaInvalid,
            u'E002 您的登录数已达最大并发登录数!': self.handler.InfoSimultaneity,
            u'您已登录!': self.handler.AlreadyOnline,
            u'请重新获取IP地址!': self.handler.IpNotAllowed,
            u'下线成功!': self.handler.OfflineSuccessful,
            u'您已下线!': self.handler.AlreadyOffline,
            u'错误!请稍后再试!': self.handler.ServerError,
            #'Session Expires': self.handler.SessionExpire
        }

        self.hasCheckedNewVersion = False
        self.online = False
        self.session = self.GenerateSession()
        self.portalHeaders = {
            'User-Agent': config.USER_AGENT,
            'Referer': config.URL
        }
        # For debug, use `urllib3.poolmanager.proxy_from_url`
        self.portalConnectionPool = urllib3.connectionpool.connection_from_url(config.URL, timeout=config.CONNECTION_TIMEOUT)
        self.brasConnectionPool = urllib3.connectionpool.connection_from_url(config.BRAS_LOGIN_URL, timeout=config.CONNECTION_TIMEOUT)
        self.serviceConnectionPool = urllib3.connectionpool.connection_from_url(config.LOGIN_STATS_URL, timeout=config.CONNECTION_TIMEOUT)

        self.poolTable = {
            'portal': self.portalConnectionPool,
            'bras': self.brasConnectionPool,
            'service': self.serviceConnectionPool
        }

    def IsOnline(self, force=False):
        return self.UpdateStatus() if force else self.online

    def DoOnline(self, username, password, captcha):
        postdata = {
            'action': 'login',
            'url': 'http://p.nju.edu.cn',
            'p_login': 'p_login',
            'username': username,
            'password': password,
            'code': captcha
        }
        try:
            login_page = self.portalConnectionPool.request_encode_body(
                'POST',
                config.URL,
                postdata,
                headers=self.portalHeaders,
                encode_multipart=False
            )
        except Exception as e:
            self.handler.ConnectionError(e)

        if self.HandleResponse(login_page.data.decode('utf-8')) is None:
            try:
                html = self.portalConnectionPool.request('GET', config.URL, headers=self.portalHeaders).data.decode('utf-8')
            except Exception as e:
                self.handler.ConnectionError(e)
            if u'注销' in html:  # Login Successfully
                return self.handler.OnlineSuccessful()
            else:
                return self.HandleResponse(html)  # Other situations
        else:
            raise ConnectionException(u'未知错误')  # Should not be here

    def DoOffline(self):
        postdata = {
            'action': 'logout',
            'p_logout': 'p_logout'
        }
        try:
            page = self.portalConnectionPool.request_encode_body(
                'POST',
                config.URL,
                postdata,
                headers=self.portalHeaders,
                encode_multipart=False
            )
        except Exception as e:
            self.handler.ConnectionError(e)
        return self.HandleResponse(page.data.decode('utf-8'))

    def DoForceOffline(self, username, password, captcha):
        headers = {
            'User-Agent': config.USER_AGENT,
            'Cookie': "selfservice={0}".format(self.session)
        }
        try:
            loginPage = self.brasConnectionPool.request_encode_body(
                'POST',
                config.BRAS_LOGIN_URL,
                {
                    'login_username': username,
                    'login_password': password,
                    'code': captcha,
                    'action': 'login'
                },
                headers=headers,
                encode_multipart=False
            )
            if self.HandleResponse(loginPage.data.decode('utf-8')[:64]) is None:
                onlineListPage = self.brasConnectionPool.request(
                    'GET',
                    config.BRAS_URL,
                    {'action': 'online'},
                    headers=headers
                )
        except Exception as e:
            self.handler.ConnectionError(e)

        soup = BeautifulSoup(onlineListPage.data.decode('utf-8'), "html.parser")
        onlineInfo = soup.find_all(id=re.compile('^line(\d+)$'))
        for info in onlineInfo:
            sid = info['id'][4:]
            try:
                response = self.brasConnectionPool.request(
                    'GET',
                    config.BRAS_URL,
                    {
                        'action': 'disconnect',
                        'id': sid
                    },
                    headers=headers
                )
            except Exception as e:
                self.handler.ConnectionError(e)
            if u'下线成功' not in response.data.decode('utf-8'):
                raise ConnectionException("操作未成功，请至 http://bras.nju.edu.cn 手动尝试")
        self.online = False
        return True

    def HandleResponse(self, r):
        match = re.search(ur"alert\('([^']+)'\);", r)
        if match is None:
            return None
        else:
            error = match.group(1)
        if error in self.handlerTable:
            return self.handlerTable[error]()
        else:
            raise ConnectionException(u"未知错误：" + error)

    def GetCaptchaImage(self, captchaType):
        headers = {
            'User-Agent': config.USER_AGENT,
            'Cookie': '{0}={1}'.format(captchaType.GetCookieName(), self.session)
        }
        try:
            image = self.poolTable[captchaType.GetName()].request('GET', captchaType.GetURL(), headers=headers)
            output = cStringIO.StringIO(image.data)
            return output
        except Exception as e:
            self.handler.ConnectionError(e)

    def GenerateSession(self):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(26))

    def UpdateStatus(self):
        try:
            page = self.portalConnectionPool.request('GET', config.URL, timeout=3, headers=self.portalHeaders)
            html = page.data.decode('utf-8')
            if u'注销' in html:
                self.online = True
            else:
                self.online = False
            return self.online
        except Exception:
            raise UpdateStatusException

    def SendOnlineStatistics(self):
        try:
            page = self.portalConnectionPool.request('GET', config.URL, headers=self.portalHeaders)
            soup = BeautifulSoup(page.data.decode('utf-8'), "html.parser")
            profile = soup.table.find_all("td")
            studentId = profile[5].text.encode('utf-8')
            loginTime = '%s-%s' % (date.today().year, profile[6].text.encode('utf-8'), )
            ip = profile[7].text.encode('utf-8')
            mac = profile[8].text.encode('utf-8')
            location = profile[9].text.encode('utf-8')
            postdata = {
                'student_id': studentId,
                'login_time': loginTime,
                'ip': ip,
                'mac': mac,
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

    def CheckNewVersion(self):
        if self.hasCheckedNewVersion:
            return None
        new = None
        try:
            remote = self.serviceConnectionPool.request('GET', config.CHECK_VERSION_URL)
            if remote.status != 200:
                raise
            remoteVersion = remote.data.strip()
            if cmp(remoteVersion.split('.'), __version__.split('.')) > 0:
                new = remoteVersion
            self.hasCheckedNewVersion = True
        except:
            pass
        return new


class ConnectionHandler(object):
    def __init__(self, manager):
        super(ConnectionHandler, self).__init__()
        self.manager = manager
        self.connectionErrorMessage = {
            urllib3.exceptions.TimeoutError: u"超时，请检查网络"
        }

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

    def ConnectionError(self, e):
        if isinstance(e, ConnectionException):
            raise e
        elif type(e) in self.connectionErrorMessage:
            raise ConnectionException(self.connectionErrorMessage[type(e)])
        else:
            raise ConnectionException(e.__str__())

    # def SessionExpire(self):
    #     self.manager.session = self.manager.GenerateSession()
    #     raise ConnectionException(u"会话超时，请重试")


class ConnectionException(Exception):
    pass


class CaptchaException(ConnectionException):
    pass


class UpdateStatusException(ConnectionException):
    pass
