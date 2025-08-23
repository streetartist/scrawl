import pygame, sys, random
from pygame.locals import *
from pygameGUI import Group
from pygameGUI import Group,PG_Error

class Widget:
    """所有组件的基类"""
    
    def __init__(self, group=None):
        """
        获得主组
        加入主组
        
        """
        if type(group) == Group: # 是group
            self.group = group
            group.add(self)
        elif hasattr(type(group),"frame"): # 是frame 注意，或许这里与上面不同，或许是静态传参
            self.master = group
            self.group = self.master.widgets
            self.master.widgets.add(self)
        else:
            raise PG_Error("group参数错误！")
        
    

    def update(self,*args,**kwargs):
        """
        在主循环中，自动被每帧调用

        """
        pass

    def draw(self, screen):
        """绘制函数"""
        pass

    def delete(self):
        """
        在主组中删除自己
        
        """
        self.group.widgets.remove(self)

    def set_pos(self,location="center",position=[0,0]):
        """
        更灵活的设置位置

        """
        if type(position) == type or type(position) == list:
            if location == "center":
                self.rect.center = position
            elif location == "topleft":
                self.rect.topleft = position
            elif location == "topright":
                self.rect.topright = position
            elif location == "bottomleft":
                self.rect.bottomleft = position
            elif location == "bottomright":
                self.rect.bottomright = position
            else:
                raise PG_Error(f"""\n==============================
可能是location值错误:{repr(location)}
    (应是"center"、"topleft"、
    "bottomleft"、"bottomright"、
    "top"、"bottom"、"right"或"left")
或由于position值错误:{repr(position)}
    (应是list、tuple或int)""")
        elif type(position) == int:
            if location == "top":
                self.rect.top = position

            elif location == "bottom":
                self.rect.bottom = position

            elif location == "right":
                self.rect.right = position

            elif location == "left":
                self.rect.left = position
            else:
                raise PG_Error(f"""\n==============================
可能是location值错误:{repr(location)}
    (应是"center"、"topleft"、
    "bottomleft"、"bottomright"、
    "top"、"bottom"、"right"或"left")
或由于position值错误:{repr(position)}
    (应是list、tuple或int)""")
        else:
            raise PG_Error(f"""\n==============================
position值错误:{repr(position)} \n\t(应是list、tuple或int)""")

    def get_rect(self):
        """在最近的非frame组件之中的rect位置"""
        if hasattr(self, "master"):
            rect = [self.rect[0]+self.master.get_rect()[0],
                    self.rect[1]+self.master.get_rect()[1],
                    self.rect[2],
                    self.rect[3]]
            return pygame.Rect(rect)
        else:
            return self.rect
            

    def __str__(self):
        return "widget"




