__version__ = "0.3"

from ui import MainApp


def main():
    app = MainApp(False)
    app.MainLoop()
