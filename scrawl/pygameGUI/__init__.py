import pygame, sys, random,os
from pygame.locals import *

# init
pygame.init()
os.environ["SDL_IME_SHOW_UI"] = "1"

# 报错
from pygameGUI.error import PG_Error

# 组
from pygameGUI.group import Group

# 组件
from pygameGUI.widgets.widget import Widget
from pygameGUI.widgets.frame import Frame
from pygameGUI.widgets.button import Button
from pygameGUI.widgets.slider import Slider
from pygameGUI.widgets.switch import Switch
from pygameGUI.widgets.label import Label
from pygameGUI.widgets.message import Message

# 复合组件
from pygameGUI.composites.window import Window
from pygameGUI.composites.scrollbar import Scrollbar
from pygameGUI.composites.entry import Entry

# 特效
from pygameGUI.effects.player import Player




















