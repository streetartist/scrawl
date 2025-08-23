import pygame, sys, random
from pygame.locals import *
from pygameGUI import Widget,Group


class Button(Widget):
    """
    按钮
    """
    def __init__(self,
                 group=None, # 加入到哪个Group中，该组件通常是Frame
                 pos = [0,0],size=[100,50], # 位置、大小
                 active_texture = (240,240,240), # 接受一个元组/列表或函数，代表按钮上的图案
                 init_texture = (250,250,250), # 接受一个元组/列表或函数，代表按钮上的图案
                 down_texture = (230,230,230), # 接受一个元组/列表或函数，代表按钮上的图案
                 block = True, # 当鼠标位于上方时是否打开阻断
                 unblock=False, # 是否免疫阻断
                 mouse_button = 1, # 响应哪个按钮
                 down_command = None, # 当按钮被点击时调用(按下时)
                 command = None, # 当按钮被点击时调用(抬起时)
                 active_command = None, # 当按钮处于鼠标下方时，反复调用
                 repeat=-1, # 长按时按照多少帧的间隔调用command
                 ):
        """初始化"""
        
        super().__init__(group)
        self.unblock = unblock
        self.block = block
        self.active_command = active_command
        self.down_command = down_command
        self.command = command
        self.mouse_button = mouse_button
        self.repeat,self.repeat_copy = repeat,repeat

        # 生成图像
        self.width ,self.height = size
        self.active_image = self.__draw_texture(active_texture,size)
        self.__image = self.__init_image = self.__draw_texture(init_texture,size)
        self.down_image = self.__draw_texture(down_texture,size)
        
        # 得到矩形位置
        self.rect = self.__image.get_rect()
        self.rect.x, self.rect.y = pos

        # 判定
        self.down = False
        
    def update(self,args,kwargs):
        if (not Group.block_start or self.unblock) \
           and pygame.Rect(self.get_rect()).collidepoint(kwargs["pos"]):
            # 是否按下鼠标
            if not pygame.mouse.get_pressed()[self.mouse_button-1]:
                self.__image = self.active_image
                self.__replace_rect(self.rect,self.__image)
                if self.active_command:
                    self.active_command()
            else:
                self.__image = self.down_image
                self.__replace_rect(self.rect,self.__image)
                
            # 打开阻断
            if self.block == True:
                Group.block_start = True
                
            # 迭代操作
            for event in kwargs["events"]:
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == self.mouse_button:
                        self.down = True
                        if self.down_command:
                            self.down_command()
                elif event.type == MOUSEBUTTONUP:
                    if event.button == self.mouse_button and self.down:
                        self.__image = self.active_image
                        self.__replace_rect(self.rect,self.__image)
                        # 长按
                        if self.repeat >= 0: # 防止松开重复调用
                            self.repeat = self.repeat_copy
                        if self.command:
                            self.command()
                        self.down = False
                        break
            if self.down:
                if self.repeat < 0 or (not pygame.mouse.get_pressed()[self.mouse_button-1]):
                    pass
                elif self.repeat == 0:
                    self.repeat = self.repeat_copy
                    self.command()
                else:
                    self.repeat -= 1

        else:
            # 常规状态
            self.__image = self.__init_image
            self.__replace_rect(self.rect,self.__image)
            for event in kwargs["events"]:
                if event.type == MOUSEBUTTONUP:
                    if event.button == self.mouse_button and self.down:
                        self.down = False
            
                
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
    
    def draw(self, surface):
        """绘制"""
        surface.blit(self.__image,[self.rect.x,self.rect.y])

    def set_image(self,state="init",size = [100,100],texture=None):
        """设置图片"""
        image = pygame.Surface(size, pygame.SRCALPHA)
        if state == "init":
            self.__init_image = texture(image)
        elif state == "active":
            self.active_image = texture(image)
        elif state == "down":
            self.down_image = texture(image)
            
    def __str__(self):
        return F"Button"

    @property  # init_image
    def init_image(self):
        return self.__init_image
    @init_image.setter
    def init_image(self,image):
        self.__init_image = image
        self.__image=self.__init_image
        self.__replace_rect(self.rect,image)

    
