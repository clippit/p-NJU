#! /usr/bin/env python

import os
import urllib2
import cStringIO
import Image
import ImageChops

if not os.path.exists('images'):
    os.mkdir('images')

url = "http://p.nju.edu.cn/portal/img.html"

for i in range(300):
    img_file = cStringIO.StringIO(urllib2.urlopen(url).read())
    img = Image.open(img_file)
    img = img.convert('L').point(lambda p: 0 if p < 175 else 1, '1')
    bg = Image.new('1', img.size, 1)
    diff = ImageChops.difference(img, bg)
    img = img.crop(diff.getbbox())
    img.save('images/{0}.png'.format(i))
