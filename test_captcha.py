#! /usr/bin/env python

import os
import urllib3
import cStringIO
from pNJU.captcha import Captcha

os.makedirs('test/original')
for i in range(10):
    os.makedirs('test/{0}'.format(i))

http = urllib3.PoolManager()
url = "http://p.nju.edu.cn/portal/img.html"
suites = 5000

for i in range(suites):
    img_file = cStringIO.StringIO(http.request('GET', url).data)
    img = Captcha.PreProcess(img_file)
    img.save('test/original/{0}.png'.format(i))
    boundary = Captcha.Split(img)
    result = []
    for j, b in enumerate(boundary):
        digit = img.crop(b)
        guess = Captcha.GuessDigit(digit)
        digit.save('test/{0}/{1}.png'.format(guess, i * 4 + j))
