from importlib.metadata import version

from packaging.version import Version

try:
    __version__ = version("haruka-bot")
except Exception:
    __version__='dev'
VERSION = Version(__version__)
