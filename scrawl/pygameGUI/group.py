import pygame, sys, random
from pygame.locals import *
from pygameGUI.error import PG_Error

class Group:
    """组"""
    block_start = False # 表示当前是否处于阻断状态
    
    def __init__(self, master = True):
        self.widgets = [] # 存放所有的组件
        self.index = 0  # 用于迭代记录
        self.master = master

    def add(self, widget):
        """用于添加组件，非外部调用"""
        if widget not in self.widgets:
            self.widgets.append(widget)

    def clear(self):
        """清空组中的组件"""
        self.widgets.clear()

    def update(self,*args,**kwargs):
        """关闭阻断"""
        if self.master:
            self._block_stop()
        """依次调用组件的update 并传入参数"""
        for widget in self.widgets[::-1]:
            widget.update(args,kwargs)

    def draw(self,screen):
        """依次绘制组件"""
        for widget in self.widgets:
            widget.draw(screen)

    def _block_stop(self):
        if self.widgets:
            type(self).block_start = False
            
            
    def __str__(self):
        """返回自生类名"""
        str_widgets = [str(widget) for widget in self.widgets]
        return str(str_widgets)

    def __iter__(self):
        """
        这是个迭代器
            
        """
        return self

    def __next__(self):
        """迭代"""
        if self.index >= len(self.widgets):
            self.index = 0
            raise StopIteration
        else:
            self.index += 1
        return self.widgets[self.index-1]

    def __getitem__(self, index):
        return self.widgets[index]

    def __delitem__(self,index):
        del self.widgets[index]

