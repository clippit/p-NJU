__version__ = "0.2.2"

from ui import MainApp


def main():
    app = MainApp(False)
    app.MainLoop()
