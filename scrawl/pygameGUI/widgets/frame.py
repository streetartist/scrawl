import pygame, sys, random
from pygame.locals import *
from pygameGUI import Group,Widget


class Frame(Widget):
    """
    Frame -> 框架结构
    各种的组件都是由它组织起来的
    内部有一个内置的组(Group)，用于管理其他组件
    """
    frame = True # 表示这是一个框架结构
    
    def __init__(self, group=None, # 组
                 pos = [0,0],size=[0,0], # 位置，大小
                 texture=(190,190,190), # 纹理
                 block=True, # 是否阻断
                 command = None, # 当位于鼠标下方时连续调用(被阻断时无效
                 unblock = False, # 是否免疫阻断
                 ):
        """初始化"""
        
        super().__init__(group)
        self.block = block
        self.unblock = unblock
        self.command=command

        # 生成图像
        self.size = self.width ,self.height = size
        self.__image = self.__draw_texture(texture,size)
        
        # 得到矩形位置
        self.rect = self.__image.get_rect()
        self.rect.x, self.rect.y = pos

        # 内置组
        self.widgets = Group(master = False)

    def __draw_texture(self,texture,size):
        """绘制纹理"""
        image = pygame.Surface(size, pygame.SRCALPHA)
        if type(texture) == tuple or type(texture) == list:
            image.fill(texture)
        else:
            image = texture(image)
        return image

    def __replace_rect(self,rect,image):
        """用于改变纹理之后刷新rect"""
        x,y = rect.center
        self.rect = image.get_rect()
        self.rect.center = x,y
        
    def update(self,args,kwargs):
        "刷新"
        for widget in self.widgets[::-1]: # 注：这里不能使用self.widgets.update() 由于万能参数的传参格式
            widget.update(args,kwargs)
        if (not Group.block_start or self.unblock) \
           and pygame.Rect(self.get_rect()).collidepoint(kwargs["pos"]):
            if self.block == True:
                Group.block_start = True
            if self.command:
                self.command()
            
    def draw(self, surface):
        "绘制"
        image = self.__image.copy()
        self.widgets.draw(image)
        surface.blit(image,[self.rect.x,self.rect.y])

    def set_image(self, size=[500,500], texture=None):
        "设置图片，注意要重新设置位置"
        image = pygame.Surface(size, pygame.SRCALPHA)
        self.__image = texture(image)
        x,y = self.rect.center
        self.rect = image.get_rect()
        self.rect.center = x,y

    def delete(self):
        for w in self.widgets:
            w.delete()
        super().delete()
            
    def __str__(self):
        return f"Frame"

    @property
    def image(self):
        return self.__image
    @image.setter
    def image(self, image):
        self.__image = image
        self.__replace_rect(self.rect,image)





