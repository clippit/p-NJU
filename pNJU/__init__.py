import wx
from ui import MainFrame


def main():
    app = wx.App(False)
    MainFrame(None)
    app.MainLoop()
