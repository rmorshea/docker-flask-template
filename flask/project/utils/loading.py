import os
import types
import pkgutil
import inspect
import importlib.util
from flask import Blueprint


def load_blueprints(app, include):
    for bp in iter_blueprints(include):
        app.register_blueprint(bp)


def iter_blueprints(include):
    if include.startswith('.'):
        include = _calling_frame().f_globals['__name__'] + include
    for module in _iter_packages(include):
        for k, v in vars(module).items():
            if isinstance(v, Blueprint):
                yield v


def _iter_packages(include):
    spec = importlib.util.find_spec(include)
    if spec is None:
        raise ImportError("Could not find module spec for '%s'." % include)
    yield spec.loader.load_module()
    search_paths = list(map(
        lambda s: os.path.join(os.getcwd(), s),
        spec.submodule_search_locations
    ))
    for finder, name, ispkg in pkgutil.walk_packages(search_paths):
        if ispkg:
            fullname = include + '.' + name
            yield from _iter_packages(fullname)


def _calling_frame():
    frame = inspect.currentframe()
    while frame.f_globals['__name__'] == __name__:
        frame = frame.f_back
    return frame
