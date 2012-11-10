# -*- coding: utf-8 -*-

import config


class Captcha(object):
    """Captcha manager and recognizer"""
    def __init__(self):
        super(Captcha, self).__init__()

    @classmethod
    def Recognize(cls, img):
        boundary = cls.Split(img)
        for b in boundary:
            print b

    @classmethod
    def Split(cls, img):
        """
        This method return the boundary of every digit in captcha image
        in format (left, upper, right, lower) which can be used for cropping.
        """
        pix = img.load()

        # vertical cut
        vertical = []
        foundLetter = False
        for x in range(img.size[0]):
            inLetter = False
            for y in range(img.size[1]):
                if pix[x, y] == 0:
                    inLetter = True
                    break
            if not foundLetter and inLetter:
                foundLetter = True
                start = x
            if foundLetter and not inLetter:
                foundLetter = False
                end = x
                vertical.append((start, end))

        # horizontal cut
        def _findFistLine(pix, y_range, x_start, x_end):
            for y in y_range:
                for x in range(x_start, x_end):
                    if pix[x, y] == 0:
                        return y

        horizontal = []
        for i in vertical:
            start = _findFistLine(pix, range(img.size[1]), *i)
            end = _findFistLine(pix, reversed(range(img.size[1])), *i)
            horizontal.append((start, end))

        return [(vertical[i][0], horizontal[i][0], vertical[i][1], horizontal[i][1] + 1) for i in range(len(vertical))]


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
