import pygame, sys, random
from pygame.locals import *
from pygameGUI import Widget,Group,PG_Error

class Switch(Widget):
    """
    开关
    """
    def __init__(self,
                 group=None, # 加入到哪个Group中，该组件通常是Frame
                 pos = [0,0],size=[100,50], # 位置、大小
                 active_textures = [(240,240,240),], # 接受一个元组/列表或函数，代表按钮上的图案
                 init_textures = [(250,250,250),], # 接受一个元组/列表或函数，代表按钮上的图案
                 down_textures = [(230,230,230),], # 接受一个元组/列表或函数，代表按钮上的图案
                 block = True, # 当鼠标位于上方时是否打开阻断
                 unblock=False, # 是否免疫阻断
                 mouse_button = 1, # 响应哪个按钮
                 down_commands = [None,], # 当按钮被点击时调用(按下时)
                 commands = [None,], # 当按钮被点击时调用(抬起时)
                 active_commands = [None,], # 当按钮处于鼠标下方时，反复调用
                 repeat=-1, # 长按时按照多少帧的间隔调用command
                 ):
        """初始化"""
        super().__init__(group)
        self.unblock = unblock
        self.block = block
        if not (len(active_textures)==len(init_textures)==len(down_textures)\
                ==len(active_commands)==len(down_commands)==len(commands)):
            raise PG_Error("传入的图片、回调函数可能数量不一致哦~")
        self.active_commands = active_commands
        self.down_commands = down_commands
        self.commands = commands
        self.mouse_button = mouse_button
        self.repeat,self.repeat_copy = repeat,repeat
        self.index=0
        
        # 生成图像
        self.active_images = [self.__draw_texture(image,size) for image in active_textures]
        self.init_images = [self.__draw_texture(image,size) for image in init_textures]
        self.image = self.init_images[0]
        self.down_images = [self.__draw_texture(image,size) for image in down_textures]

        # 得到矩形位置
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos

        # 判定
        self.down = False

    def update(self,args,kwargs):
        if (not Group.block_start or self.unblock) \
           and pygame.Rect(self.get_rect()).collidepoint(kwargs["pos"]):
            # 是否按下鼠标
            if not pygame.mouse.get_pressed()[self.mouse_button-1]:
                self.image = self.active_images[self.index]
                self.__replace_rect(self.rect,self.image)
                if self.active_commands[self.index]:
                    self.active_commands[self.index]()
            else:
                self.image = self.down_images[self.index]
                self.__replace_rect(self.rect,self.image)

            # 打开阻断
            if self.block == True:
                Group.block_start = True
                
            # 迭代操作
            for event in kwargs["events"]:
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == self.mouse_button:
                        self.down = True
                        if self.down_commands[self.index]:
                            self.down_commands[self.index]()
                elif event.type == MOUSEBUTTONUP:
                    if event.button == self.mouse_button and self.down:
                        self.image = self.active_images[self.index]
                        self.__replace_rect(self.rect,self.image)
                        # 长按
                        if self.repeat >= 0:
                            self.repeat = self.repeat_copy
                        if self.commands[self.index]:
                            self.commands[self.index]()
                        self.index += 1
                        if self.index > len(self.active_images)-1:
                            self.index=0
                        self.down = False
                        break
            if self.down:
                if self.repeat < 0 or (not pygame.mouse.get_pressed()[self.mouse_button-1]):
                    pass
                elif self.repeat == 0:
                    self.repeat = self.repeat_copy
                    if self.commands[self.index]:
                        self.commands[self.index]()
                    self.index += 1
                    if self.index > len(self.active_images)-1:
                        self.index=0
                else:
                    self.repeat -= 1

        else:
            # 常规状态
            self.image = self.init_images[self.index]
            self.__replace_rect(self.rect,self.image)
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
        surface.blit(self.image,[self.rect.x,self.rect.y])

    def set_image(self,state="init",size = [100,100],index=0,texture=None):
        """设置图片"""
        length = len(self.active_images)
        if index >= length-1:
            self.active_images = self.active_images+[None for i in range(index-length+1)]
            self.init_images = self.init_images+[None for i in range(index-length+1)]
            self.down_images = self.down_images+[None for i in range(index-length+1)]
            self.active_commands = self.active_commands+[None for i in range(index-length+1)]
            self.down_commands = self.down_commands+[None for i in range(index-length+1)]
            self.commands = self.commands+[None for i in range(index-length+1)]
        image = pygame.Surface(size, pygame.SRCALPHA)
        if state == "init":
            self.init_images[index] = texture(image)
        elif state == "active":
            self.active_images[index] = texture(image)
        elif state == "down":
            self.down_images[index] = texture(image)

    def pop(self,index=-1):
        """根据索引删除一列"""
        self.active_images.pop(index)
        self.init_images.pop(index)
        self.down_images.pop(index)
        self.active_command.pop(index)
        self.down_command.pop(index)
        self.command.pop(index)

    def __str__(self):
        return f"Switch"

       









        
