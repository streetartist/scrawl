import pygame, sys, random
from pygame.locals import *
from pygameGUI import Widget


class Label(Widget):
    """
    单行文本
    """
    def __init__(self,
                 group=None, # 加入到哪个Group中，该组件通常是Frame
                 pos = [0,0], # 位置
                 text="...文本...", # 文本 
                 font=("arialms",25), # 字体字号
                 color=[0,0,0], # 前景色（字体颜色）
                 bg=None, # 背景色
                 alpha=255, # 不透明度
                 bold = False, # 加粗
                 italic = False, # 斜体
                 underline = False, # 下划线
                 antialias=True, # 抗锯齿
                 ):
        """初始化"""
        if group:
            super().__init__(group)
        self.__text = text
        self.__font = font
        self.__antialias = antialias
        self.__color = color
        self.__background = bg
        self.__alpha = alpha
        self.__italic = italic
        self.__bold = bold
        self.__underline = underline
        #self.__style = "样式"

        #生成image
        self.__render_image()
        
        # 得到矩形位置
        self.rect = self.__image.get_rect()
        self.rect.x, self.rect.y = pos
        
    def draw(self, surface):
        """绘制"""
        surface.blit(self.__image,[self.rect.x,self.rect.y])

    def __replace_rect(self,rect,image):
        """用于改变纹理之后刷新rect"""
        x,y = rect.center
        self.rect = image.get_rect()
        self.rect.center = x,y

    def __set_style(self,font,bold,italic,underline):
        """设置字体字形"""
        # 生成字体对象
        try:
            self.__style = pygame.font.Font(font[0],font[1])
        except:
            self.__style = pygame.font.SysFont(font[0],font[1],bold,italic)

        # 下划线 如果字体没有加粗/斜体，强行加粗/倾斜  
        self.__style.set_underline(underline)
        if not self.__style.get_bold():
            self.__style.set_bold(bold)
        if not self.__style.get_italic():
            self.__style.set_italic(italic)

    def __render_image(self):
        """生成图片"""
        # 绘制
        self.__set_style(self.__font,self.__bold,self.__italic,self.__underline)

        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)
        
            
    def __str__(self):
        return f"Label : {self.__text}"

    def set(self, **kwargs):
        """在需要同时修改多个属性时，相比“xx=xx”该方法效率更高"""
        for key in kwargs:
            if key == "text":
                self.__text = kwargs["text"]
            elif key == "font":
                self.__font = kwargs["font"]
            elif key == "color":
                self.__color = kwargs["color"]
            elif key == "bg":
                self.__background = kwargs["bg"]
            elif key == "bold":
                self.__bold = kwargs["bold"]
            elif key == "italic":
                self.__italic = kwargs["italic"]
            elif key == "underline":
                self.__underline = kwargs["underline"]
            elif key == "antialias":
                self.__antialias = kwargs["antialias"]
        self.__set_style(self.__font,self.__bold,self.__italic,self.__underline)
        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

        
    @property  # text
    def text(self):
        return self.__text
    @text.setter
    def text(self,value):
        self.__text = value
        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # font
    def font(self):
        return self.__font
    @font.setter
    def font(self,value):
        self.__font = value
        self.__set_style(self.__font,self.__bold,self.__italic,self.__underline)
        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # color
    def color(self):
        return self.__color
    @color.setter
    def color(self,value):
        self.__color = value
        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)

    @property # background
    def bg(self):
        return self.__background
    @bg.setter
    def bg(self,value):
        self.__background = value
        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)

    @property # alpha
    def alpha(self):
        return self.__alpha
    @alpha.setter
    def alpha(self,value):
        self.__alpha = value
        # 生成image
        self.__image.set_alpha(self.__alpha)

    @property # bold
    def bold(self):
        return self.__bold
    @bold.setter
    def bold(self,value):
        self.__bold = value
        self.__set_style(self.__font,self.__bold,self.__italic,self.__underline)
        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # italic
    def italic(self):
        return self.__italic
    @italic.setter
    def italic(self,value):
        self.__italic = value
        self.__set_style(self.__font,self.__bold,self.__italic,self.__underline)
        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # underline
    def underline(self):
        return self.__underline
    @underline.setter
    def underline(self,value):
        self.__underline = value
        self.__set_style(self.__font,self.__bold,self.__italic,self.__underline)
        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # antialias
    def antialias(self):
        return self.__antialias
    @antialias.setter
    def antialias(self,value):
        self.__antialias = value
        self.__set_style(self.__font,self.__bold,self.__italic,self.__underline)
        # 生成image
        self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
        self.__image.set_alpha(self.__alpha)
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # image
    def image(self):
        return self.__image

    @property # style
    def style(self):
        return self.__style


    
