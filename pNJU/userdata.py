# -*- coding: utf-8 -*-
import os
import sys
import ConfigParser
import cPickle
import config


class Preference(object):

    fields = {
        'username': 'username',
        'password': 'password',
        'autoConnectEnabled': 'auto_connect',
        'statisticsEnabled': 'statistics'
    }

    def __init__(self):
        super(Preference, self).__init__()
        self.filename = os.path.join(FindDirectory(), config.PREFERENCE_FILENAME)
        self.forceRefresh = True

    def Save(self, *args, **kwargs):
        if not all(key in kwargs for key in self.fields):
            raise KeyError("Preference must contain necessary fields.")

        pref = ConfigParser.ConfigParser()
        pref.add_section('login')
        pref.set('login', self.fields['username'], kwargs['username'])
        pref.set('login', self.fields['password'], EncryptPassword(kwargs['password']))
        pref.add_section('options')
        pref.set('options', self.fields['autoConnectEnabled'], kwargs['autoConnectEnabled'])
        pref.set('options', self.fields['statisticsEnabled'], kwargs['statisticsEnabled'])

        with open(self.filename, 'w+b') as output:
            pref.write(output)

        self.forceRefresh = True

    def Get(self, name, default=None):
        if not hasattr(self, 'pref') or self.forceRefresh:
            self.pref = self.ReadFile()
        if name in self.pref:
            return self.pref[name]
        else:
            return default

    def ReadFile(self):
        defaults = dict(
            username="",
            password="",
            autoConnectEnabled=False,
            statisticsEnabled=True,
        )
        try:
            pref = ConfigParser.ConfigParser(defaults)
            pref.read(self.filename)
            return dict(
                username=pref.get('login', self.fields['username']),
                password=DecryptPassword(pref.get('login', self.fields['password'])),
                autoConnectEnabled=pref.getboolean('options', self.fields['autoConnectEnabled']),
                statisticsEnabled=pref.getboolean('options', self.fields['statisticsEnabled']),
            )
            self.forceRefresh = False
        except Exception:
            return defaults


class Session(object):
    def __init__(self):
        super(Session, self).__init__()
        self.filename = os.path.join(FindDirectory(), config.SESSION_FILENAME)
        self.cookie = None
        self.captcha = None

    def Save(self, cookie=None, captcha=None):
        if cookie:
            self.cookie = cookie
        if captcha:
            self.captcha = captcha

        data = {"cookie": self.cookie, "captcha": self.captcha}
        try:
            with open(self.filename, 'w+b') as output:
                cPickle.dump(data, output)
        except:
            pass

    def Load(self, force=False):
        if not all((self.cookie, self.captcha)):
            force = True

        if force:
            try:
                with open(self.filename, 'rb') as input:
                    data = cPickle.load(input)
                    self.cookie = data['cookie']
                    self.captcha = data['captcha']
            except:
                return None, None

        return self.cookie, self.captcha


def FindDirectory():
    if sys.platform.startswith("win"):
        directory = os.path.join(os.environ['APPDATA'], config.APP_NAME)
    elif sys.platform == 'darwin':
        directory = os.path.join(os.path.expanduser('~/Library/Application Support/'), config.APP_NAME)
    else:
        directory = os.path.join(os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config")), config.APP_NAME)

    if not os.path.exists(directory):
        os.makedirs(directory)

    return directory


def EncryptPassword(toBeEncrypted):
    return toBeEncrypted.encode('base64').encode('rot13')


def DecryptPassword(toBeDecrypted):
    return toBeDecrypted.decode('rot13').decode('base64')
