import importlib.metadata

try:
    __version__ = importlib.metadata.version("podapp")
except importlib.metadata.PackageNotFoundError:
    __version__ = "development"
