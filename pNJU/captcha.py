# -*- coding: utf-8 -*-

import config


class Captcha(object):
    """Captcha manager and recognizer"""
    def __init__(self):
        super(Captcha, self).__init__()

    @classmethod
    def Recognize(cls, image):
        pass


class PortalCaptcha(Captcha):
    def __init__(self):
        super(PortalCaptcha, self).__init__()

    @classmethod
    def GetURL(cls):
        return config.IMG_URL

    @classmethod
    def GetCookieName(cls):
        return 'portalservice'

    @classmethod
    def GetName(cls):
        return 'portal'


class BrasCaptcha(Captcha):
    def __init__(self):
        super(BrasCaptcha, self).__init__()

    @classmethod
    def GetURL(cls):
        return config.BRAS_IMG_URL

    @classmethod
    def GetCookieName(cls):
        return 'selfservice'

    @classmethod
    def GetName(cls):
        return 'bras'
