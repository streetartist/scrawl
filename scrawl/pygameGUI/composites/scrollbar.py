import pygame, sys, random
from pygame.locals import *
from pygameGUI import Group,Widget,Frame,Button,Slider,PG_Error


class Scrollbar(Widget):
    """
    Scrollbar -> 滑条组件
    进阶的frame,能比frame更加轻松的生成滑条
    内部有一个内置的组(Group)，用于管理其他组件
    """
    frame = True # 表示这是一个框架结构
    
    def __init__(self, group=None, # 组
                 pos = [0,0],size=[0,0], # 位置，大小
                 texture=(190,190,190), # 纹理
                 block=True, # 是否阻断
                 command = None, # 当位于鼠标下方时连续调用(被阻断时无效
                 unblock = False, # 是否免疫阻断
                 orient = [False,True]
                 ):
        """初始化"""
        
        super().__init__(group)
        self.block = block
        self.unblock = unblock
        self.command=command
        self.orient = orient
        self.slider=None

        # 生成图像
        self.size = self.width ,self.height = size
        self.__image = self.__draw_texture(texture,size)
        
        # 得到矩形位置
        self.rect = self.__image.get_rect()
        self.rect.x, self.rect.y = pos

        # 内置组
        self.widgets = Group(master = False)

        # 滑块回正算法(是否溢出
        self.spill = None
        
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

    def check_slider_pos(self):
        """检测滑块是否超出范围，如果超出，就返回到最近边界位置"""
        #  溢出
        if self.spill is None:
            pass
        elif self.spill:
            self_rect=self.get_rect()
            slider_rect = self.slider.get_rect()
            if self.orient[0]:
                if slider_rect.center[0] < self_rect[0]:
                    self.slider.rect[0] = self_rect[0] - slider_rect[2]/2 - (slider_rect[0]-self.slider.rect[0])
                elif slider_rect.center[0] > self_rect[0] + self_rect[2]:
                    self.slider.rect[0] = self_rect[0] + self_rect[2] - slider_rect[2]/2 - (slider_rect[0]-self.slider.rect[0]) 
            if self.orient[1]:
                if slider_rect.center[1] < self_rect[1]:
                    self.slider.rect[1] = self_rect[1] - slider_rect[3]/2 - (slider_rect[1]-self.slider.rect[1])
                elif slider_rect.center[1] > self_rect[1] + self_rect[3]:
                    self.slider.rect[1] = self_rect[1] + self_rect[3] - slider_rect[3]/2 - (slider_rect[1]-self.slider.rect[1])
        # 不溢出
        else:
            if self.orient[0]:
                if self.slider.rect[0] < 0:
                    self.slider.rect[0] = 0
                elif self.slider.rect[0] + self.slider.rect[2] > self.rect[2]:
                    self.slider.rect[0] = self.rect[2] - self.slider.rect[2]
            if self.orient[1]:
                if self.slider.rect[1] < 0:
                    self.slider.rect[1] = 0
                elif self.slider.rect[1] + self.slider.rect[3] > self.rect[3]:
                    self.slider.rect[1] = self.rect[3] - self.slider.rect[3]
        
    def update(self,args,kwargs):
        "刷新"
        for widget in self.widgets[::-1]: # 注：这里不能使用self.widgets.update() 由于万能参数的传参格式
            widget.update(args,kwargs)

        self.check_slider_pos()

        # 阻断
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

    def set_slider(self,
                   group=False, # 加入到哪个Group中，该组件通常是Frame
                   pos = [0,0],size=[100,50], # 位置、大小
                   active_texture = (240,240,240), # 接受一个元组/列表或函数，代表按钮上的图案
                   init_texture = (250,250,250),# 接受一个元组/列表或函数，代表按钮上的图案
                   down_texture = (230,230,230),# 接受一个元组/列表或函数，代表按钮上的图案
                   block = True, # 当鼠标位于上方时是否打开阻断
                   unblock=False, # 是否免疫阻断
                   mouse_button = 1, # 响应哪个按钮
                   down_command = None, # 当按钮被点击时调用(按下时)
                   command = None, # 当按钮被点击时调用(抬起时)
                   active_command = None, # 当按钮处于鼠标下方时，反复调用
                   orient=[False,True], # 允许的移动方向[x, y]
                   repeat = 1,
                   ):
        if group == False:
            group = self
        self.orient = orient
        if command:
            c = command
            def command():
                self.check_slider_pos()
                c()
        else:
            def command():
                self.check_slider_pos()
        self.slider = Slider(group=group,
                             pos = pos, size=size,
                             active_texture = active_texture,
                             init_texture = init_texture,
                             down_texture = down_texture,
                             unblock = unblock,
                             mouse_button = mouse_button,
                             down_command = down_command,
                             command = command,
                             active_command = active_command,
                             block=block,
                             orient=orient,
                             repeat = repeat,)
        if hasattr(self.slider,"master") and self.slider.master == self:
            self.spill = False
        else:
            self.spill = True
        return self.slider

    def get_percent(self):
        """返回一个百分比(一个小于1大于0的浮点数)"""
        if self.spill is None:
            raise PG_Error("请先实例化滑块部件!")
        # 溢出
        elif self.spill:
            self_rect=self.get_rect()
            slider_rect = self.slider.get_rect()
            if self.orient[0] and self.orient[1]: # xy双向
                x = (slider_rect.center[0] - self_rect[0]) / self_rect[2]
                y = (slider_rect.center[1] - self_rect[1]) / self_rect[3]
                if slider_rect.center[0] < self_rect[0]:
                    x = 0
                elif slider_rect.center[0] > self_rect[0] + self_rect[2]:
                    x = 1
                if slider_rect.center[1] < self_rect[1]:
                    y = 0
                elif slider_rect.center[1] > self_rect[1] + self_rect[3]:
                    y = 1
                return (x, y)
            elif self.orient[0]: # x 方向
                if slider_rect.center[0] < self_rect[0]:
                    x = 0
                elif slider_rect.center[0] > self_rect[0] + self_rect[2]:
                    x = 1
                else:
                    x = (slider_rect.center[0] - self_rect[0]) / self_rect[2]
                return x
            elif self.orient[1]: # y 方向
                if slider_rect.center[1] < self_rect[1]:
                    y = 0
                elif slider_rect.center[1] > self_rect[1] + self_rect[3]:
                    y = 1
                else:
                    y = (slider_rect.center[1] - self_rect[1]) / self_rect[3]
                return y
            
        # 不溢出
        else:
            if self.orient[0] and self.orient[1]:
                x = self.slider.rect.left / (self.rect[2] - self.slider.rect[2])
                y = self.slider.rect.top / (self.rect[3] - self.slider.rect[3])
                if self.slider.rect[0] < 0:
                    x = 0
                elif self.slider.rect[0] + self.slider.rect[2] > self.rect[2]:
                    x = 1
                if self.slider.rect[1] < 0:
                    y = 0
                elif self.slider.rect[1] + self.slider.rect[3] > self.rect[3]:
                    y = 1
                return (x, y)
            elif self.orient[0]:
                if self.slider.rect[0] < 0:
                    x = 0
                elif self.slider.rect[0] + self.slider.rect[2] > self.rect[2]:
                    x = 1
                else:
                    x = self.slider.rect.left / (self.rect[2] - self.slider.rect[2])
                return x
            elif self.orient[1]:
                if self.slider.rect[1] < 0:
                    y = 0
                elif self.slider.rect[1] + self.slider.rect[3] > self.rect[3]:
                    y = 1
                else:
                    y = self.slider.rect.top / (self.rect[3] - self.slider.rect[3])
                return y

    def set_percent(self,percent=None):
        """接受两个0-1之间的小数，自动修改滑块至滑条上的对应位置"""
        if self.spill is None:
            raise PG_Error("请先实例化滑块部件!")
        # 溢出
        elif self.spill:
            self_rect=self.get_rect()
            slider_rect = self.slider.get_rect()
            if self.orient[0] and self.orient[1]: # xy双向
                self.slider.rect[0] = round(self_rect[0]+self_rect[2]*percent-self.slider.rect[2]/2\
                                      +(self.slider.rect[0]-slider_rect[0]))
                self.slider.rect[1] = round(self_rect[1]+self_rect[3]*percent-self.slider.rect[3]/2\
                                      +(self.slider.rect[1]-slider_rect[1]))
            elif self.orient[0]: # x 方向
                self.slider.rect[0] = round(self_rect[0]+self_rect[2]*percent-self.slider.rect[2]/2\
                                      +(self.slider.rect[0]-slider_rect[0]))
            elif self.orient[1]: # y 方向
                self.slider.rect[1] = round(self_rect[1]+self_rect[3]*percent-self.slider.rect[3]/2\
                                      +(self.slider.rect[1]-slider_rect[1]))
        
        # 不溢出
        else:
            if self.orient[0] and self.orient[1]:
                x = self.slider.rect.left / (self.rect[2] - self.slider.rect[2])
                y = self.slider.rect.top / (self.rect[3] - self.slider.rect[3])
                if self.slider.rect[0] < 0:
                    x = 0
                elif self.slider.rect[0] + self.slider.rect[2] > self.rect[2]:
                    x = 1
                if self.slider.rect[1] < 0:
                    y = 0
                elif self.slider.rect[1] + self.slider.rect[3] > self.rect[3]:
                    y = 1
                return (x, y)
            elif self.orient[0]:
                self.slider.rect[0] = round((self.rect[2]-self.slider.rect[2])*percent)
                
            elif self.orient[1]:
               self.slider.rect[1] = round((self.rect[3]-self.slider.rect[3])*percent)
        self.check_slider_pos()

    
    def delete(self):
        for w in self.widgets:
            w.delete()
        self.slider.delete()
        super().delete()
            
    def __str__(self):
        return f"Scrollbar"

    @property
    def image(self):
        return self.__image
    @image.setter
    def image(self, image):
        self.__image = image
        self.__replace_rect(self.rect,image)





