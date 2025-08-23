import pygame, sys, random
from pygame.locals import *
from pygameGUI import Group,Frame,Widget,Button


class Window(Widget):
    """
    Window -> 窗口组件
    进阶的frame ，能比frame更加轻松的生成窗口的效果
    内部有一个内置的组(Group)，用于管理其他组件
    """
    frame = True # 表示这是一个框架结构
    
    def __init__(self, group=None,  # 组
                 pos = [20,20],size=[200,400], # 位置，大小
                 texture=(190,190,190), # 纹理
                 block=False, # 是否阻断
                 unblock = False, # 是否免疫阻断
                 command = None, # 当位于鼠标下方时连续调用
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

        self.title = None # 标题，按下可拖动窗口，后续set
        self.close_button = None # 用于关闭的按钮，
        self.move = False # 滑块是否正在移动
        self.last_rect = []  # 鼠标按下时，储存自身位置数据
        self.mouse_pos = [] # 鼠标按下时，储存鼠标位置数据

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

        # 迭代组件
        for widget in self.widgets[::-1]: #  # 注：这里不能使用self.widgets.update() 由于万能参数的传参格式
            widget.update(args,kwargs)

        if self.move: # 长按
            self.rect.center = self.last_rect.center[0]+ kwargs["pos"][0] - self.mouse_pos[0], self.rect.center[1]
            self.rect.center =  self.rect.center[0], self.last_rect.center[1]+ kwargs["pos"][1] - self.mouse_pos[1]
            self.mouse_pos = kwargs["pos"]
            self.last_rect = self.rect

            if not pygame.mouse.get_pressed()[0]: # 左键松开
                 self.move = False
            

        if  (not Group.block_start or self.unblock) \
           and pygame.Rect(self.get_rect()).collidepoint(kwargs["pos"]):
            if not self.title is None:
                if pygame.Rect(self.title.get_rect()).collidepoint(kwargs["pos"]):
                    # 检测事件
                    for event in kwargs["events"]:
                        if event.type == MOUSEBUTTONDOWN:
                            if event.button == 1:
                                self.mouse_pos = kwargs["pos"]
                                self.last_rect = self.rect
                                self.move = True
                                break
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

    def set_title(self,
                  group=False, # 组
                  pos = [0,0],size=[0,0], # 位置，大小
                  texture=(190,190,190), # 纹理
                  block=False, # 是否阻断
                  unblock = False, # 是否免疫阻断
                  command = None, # 当位于鼠标下方时连续调用（打开阻断
                  ):
        """输入参数，返回一个frame对象"""
        if group == False:
            group = self
        self.title = Frame(group=group,
                           pos = pos,size=size, 
                           texture = texture,
                           command = command,
                           block = block,
                           unblock=unblock,
                           )
        return self.title

    def set_close_button(self,
                         group = False, # 组 
                         pos = [0,0],size=[100,50], # 位置、大小
                         active_texture = (240,240,240), # 接受一个元组/列表或函数，代表按钮上的图案
                         init_texture = (250,250,250),# 接受一个元组/列表或函数，代表按钮上的图案
                         down_texture = (230,230,230),# 接受一个元组/列表或函数，代表按钮上的图案
                         unblock=False, # 是否免疫阻断
                         mouse_button = 1, # 响应哪个按钮
                         down_command = None, # 当按钮被点击时调用(按下时)
                         command = None, # 当按钮被点击时调用(抬起时)
                         active_command = None, # 当按钮处于鼠标下方时，反复调用
                         block=True, # 是否阻断
                         ):
        """注 command这里的禁止再次修改，否则会失去关闭窗口的能力，需要再修改后的command中重新加入"""
        func=command
        def command(func):
            if func:
                func()
            self.delete()
        if group == False:
            group = self
        self.close_button = Button(group=group,
                                   pos = pos, size=size,
                                   active_texture = active_texture,
                                   init_texture = init_texture,
                                   down_texture = down_texture,
                                   unblock = unblock,
                                   mouse_button = mouse_button,
                                   down_command = down_command,
                                   command = lambda : command(func),
                                   active_command = active_command,
                                   block=block,)
        return self.close_button

    def delete(self):
        self.title.delete()
        self.close_button.delete()
        for w in self.widgets:
            w.delete()
        super().delete()
                         
            
    def __str__(self):
        return f"Window"

    @property
    def image(self):
        return self.__image
    @image.setter
    def image(self, image):
        self.__image = image
        self.__replace_rect(self.rect,image)






