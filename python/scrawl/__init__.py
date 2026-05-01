"""Official Scrawl v2 Python package.

The public package name is ``scrawl``. The legacy ``scrawl_v2`` package
remains available as a compatibility alias.
"""

import sys
from importlib import import_module

from scrawl_v2 import *
from scrawl_v2 import __all__ as _SCROLL_V2_ALL, __version__

__all__ = list(_SCROLL_V2_ALL)

_SUBMODULES = (
    "animation",
    "audio",
    "camera",
    "compat",
    "constants",
    "engine",
    "events",
    "input_map",
    "light2d",
    "math_utils",
    "navigation",
    "node",
    "particles",
    "path2d",
    "physics",
    "resources",
    "scene",
    "signals",
    "sprite",
    "state_machine",
    "tilemap",
    "timer",
    "ui",
)

for _module_name in _SUBMODULES:
    _module = import_module(f"scrawl_v2.{_module_name}")
    sys.modules[f"{__name__}.{_module_name}"] = _module
    globals()[_module_name] = _module

del _SCROLL_V2_ALL
del _SUBMODULES
del _module
del _module_name