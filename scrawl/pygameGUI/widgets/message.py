import pygame, sys, random
from pygame.locals import *
from pygameGUI import Widget


class Message(Widget):
    """
    单行文本
    """
    def __init__(self,
                 group=None, # 加入到哪个Group中，该组件通常是Frame
                 pos = [0,0], # 位置
                 text="""...文本...""", # 文本 
                 font=("arialms",25), # 字体字号
                 color=[0,0,0], # 前景色（字体颜色）
                 bg=None, # 背景色
                 alpha=255, # 不透明度
                 bold = False, # 加粗
                 italic = False, # 斜体
                 underline = False, # 下划线
                 antialias=True, # 抗锯齿
                 width=0, # 限定文本宽度
                 align = "left", # 文本对其方向
                 ):
        """初始化"""
        if group:
            super().__init__(group=group)
        self.__text = text
        self.__font = font
        self.__antialias = antialias
        self.__color = color
        self.__background = bg
        self.__alpha = alpha
        self.__italic = italic
        self.__bold = bold
        self.__underline = underline
        self.width = width
        self.align = align
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
        image_list = []
        line_text = ""

        # 设置字体字形
        self.__set_style(self.__font,self.__bold,self.__italic,self.__underline)
        # 多行
        for word in self.text:
            if self.__style.size(line_text)[0] <= self.width or self.width <= 0:

                if word == "\n": # 手动换行符
                    image_list.append(self.__style.render(line_text,self.__antialias,self.__color,self.__background))
                    line_text = ""
                else: # 将word添加到line_word中
                    line_text += word
            elif not self.width <= 0: # 自动换行
                last_word = line_text[-1]
                line_text = line_text[0:-1]
                image_list.append(self.__style.render(line_text,self.__antialias,self.__color,self.__background))
                line_text = ""
                line_text += last_word
                line_text += word
        if line_text: # 最后一次自动换行的剩余
            image_list.append(self.__style.render(line_text,self.__antialias,self.__color,self.__background))
            
        # 生成透明image
        height = self.__style.get_height()
        if self.width <= 0:
            width = max([image.get_rect()[2] for image in image_list])
        else:
            width = self.width
        height = height * len(image_list)
        self.__image = pygame.Surface([width,height], pygame.SRCALPHA)

        # 填充文本
        for image in image_list:
            if self.align == "left":
                self.__image.blit(image,[0,
                                         image_list.index(image)*self.__style.get_height()])
                
            elif self.align == "right":
                self.__image.blit(image,[self.width-image.get_rect()[2],
                                         image_list.index(image)*self.__style.get_height()])
                
            elif self.align == "center":
                self.__image.blit(image,[(self.width-image.get_rect()[2])/2,
                                          image_list.index(image)*self.__style.get_height()])



        #self.__image = self.__style.render(self.__text,self.__antialias,self.__color,self.__background)
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
        # 生成image
        self.__render_image()
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

        
    @property  # text
    def text(self):
        return self.__text
    @text.setter
    def text(self,value):
        self.__text = value
        # 生成image
        self.__render_image()
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # font
    def font(self):
        return self.__font
    @font.setter
    def font(self,value):
        self.__font = value
        # 生成image
        self.__render_image()
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # color
    def color(self):
        return self.__color
    @color.setter
    def color(self,value):
        self.__color = value
        # 生成image
        self.__render_image()

    @property # background
    def bg(self):
        return self.__background
    @bg.setter
    def bg(self,value):
        self.__background = value
        # 生成image
        self.__render_image()

    @property # alpha
    def alpha(self):
        return self.__alpha
    @alpha.setter
    def alpha(self,value):
        self.__alpha = value
        # 生成image
        self.__render_image()

    @property # bold
    def bold(self):
        return self.__bold
    @bold.setter
    def bold(self,value):
        self.__bold = value
        # 生成image
        self.__render_image()
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # italic
    def italic(self):
        return self.__italic
    @italic.setter
    def italic(self,value):
        self.__italic = value
        # 生成image
        self.__render_image()
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # underline
    def underline(self):
        return self.__underline
    @underline.setter
    def underline(self,value):
        self.__underline = value
        # 生成image
        self.__render_image()
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # antialias
    def antialias(self):
        return self.__antialias
    @antialias.setter
    def antialias(self,value):
        self.__antialias = value
        # 生成image
        self.__render_image()
        # 刷新rect
        self.__replace_rect(self.rect,self.__image)

    @property # image
    def image(self):
        return self.__image


