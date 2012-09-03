# p-NJU - Assistant GUI Client of *p.nju.edu.cn*

## How to build your own version

p-NJU is built on [wxPython](http://wxpython.org/), a cross-platform GUI library with the [Python](http://www.python.org/) programming language.

My development environment is Python 2.7.3 + wxPython 2.9.4. To install the wxPython 2.9 version which is in the unstable channel:

* If you are in **Windows**, go to [download page](http://wxpython.org/download.php#unstable), download and install it.
* If you are in **Linux** and there is no such version in your software repository, go to [download page](http://wxpython.org/download.php#unstable), get the source code, apply the 2.9.4.1 patch [here](http://sourceforge.net/projects/wxpython/files/wxPython/2.9.4.0/wxPython-src-2.9.4.1.patch/download), then build wxWidgets and wxPython from scratch. There is a [build doc](http://wxpython.org/builddoc.php) FYI.
* If you are in **Mac OSX**, go to [download page](http://wxpython.org/download.php#unstable), download and install it. Specifically for Mountain Lion, please refer [this thread](http://trac.wxwidgets.org/ticket/14523#comment:4) for help.

After that, you have to install additional Python packages that p-NJU uses. It's pretty easy to do it with [pip](http://www.pip-installer.org/):

    pip install urllib3
    pip install beautifulsoup4

OK, now you can run it by `python main.py` in console window. To build executable file, you need to use [PyInstaller](http://www.pyinstaller.org/).

## How to contribute

Please fork this repository and send me pull request. Definitely you have learned how to use `git`:)

## License

This software is distributed under MIT Licence.

* * *

Copyright (C) 2012 Letian Zhang

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

* * *
