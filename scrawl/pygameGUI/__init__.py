import pygame, sys, random,os
from pygame.locals import *

# init
pygame.init()
os.environ["SDL_IME_SHOW_UI"] = "1"

# 报错
from .error import PG_Error

# 组
from .group import Group

# 组件
from .widgets.widget import Widget
from .widgets.frame import Frame
from .widgets.button import Button
from .widgets.slider import Slider
from .widgets.switch import Switch
from .widgets.label import Label
from .widgets.message import Message

# 复合组件
from .composites.window import Window
from .composites.scrollbar import Scrollbar
from .composites.entry import Entry

# 特效
from .effects.player import Player




















