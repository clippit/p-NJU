# -*- coding: utf-8 -*-
from userdata import Session
from contextlib import closing
import cookielib
import urllib2
import re
import config


class ConnectionManager(object):
    INFO_SESSION_ERROR = 0
    INFO_OFFLINE_SUCCESSFUL = 200
    INFO_ALREADY_OFFLINE = 201
    infoTable = {
        u'下线成功': INFO_OFFLINE_SUCCESSFUL,
        u'您已下线!': INFO_ALREADY_OFFLINE,
    }

    def __init__(self):
        super(ConnectionManager, self).__init__()
        self.session = Session()
        self.online = False

    def IsOnline(self):
        return self.online

    def DoOnline(self):
        self.online = True

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
        else:
            raise ConnectionException(u"未知错误")

    def ParseResponse(self, r):
        match = re.search(ur"alert\('([^']+)'\);", r)
        if match is None:
            return self.INFO_SESSION_ERROR
        return self.infoTable[match.group(1)]


class ConnectionException(Exception):
    def __init__(self, *args, **kwargs):
        super(ConnectionException, self).__init__(*args, **kwargs)
