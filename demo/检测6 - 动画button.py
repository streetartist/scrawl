import pygame,random
import sys
from pygame.locals import *

import pygameGUI as pg

# 颜色常量
WHITE = (255,255,255)
BLACK = (0,0,0)

size = width, height = 800,600

screen = pygame.display.set_mode(size)

pygame.display.set_caption("title")

clock = pygame.time.Clock()

delay = 60 # 延时计时器(1秒)

# 是否全屏
fullscreen = False
screen_change = False

# 背景颜色设定
bg_color = (80,80,80)

running = True

# ui=====
class Player:
    def __init__(self,image_list=[],speed=1):
        self.image_list = image_list
        self.index = 0
        self.running = False
        self.speed = speed
    def run(self,index=0):
        self.running = True
        self.index = index
    def update(self):
        if self.running:
            index = int(self.index)
            if index >= len(self.image_list)-1:
                image = self.image_list[len(self.image_list)-1]
                self.index = 0
                self.running=False
            else:
                image = self.image_list[index]
                self.index += self.speed 
            return image

guis = pg.Group()



text_img = pg.Label(text="开始游戏",color=(255,255,255),bg=None,font=("stxinwei",35)).image
def callback3():
    print("开始游戏")
    back_init.run()
def callback1():
    b.down_image=image(1)
def callback2():
    start_down.run()
    b.active_image=image(0.95)
    
b = pg.Button(group=guis,active_command=callback1,down_command=callback2,command=callback3)
def image(multiple):
    rect=text_img.get_rect()
    image = pygame.Surface([rect[2]+10,rect[3]+10])
    image.fill((100,255,100))
    pygame.draw.rect(surface=image,color=(240,240,240),rect=image.get_rect(),width=3)
    image.blit(text_img,[5,5])
    image=pygame.transform.smoothscale(image,(image.get_rect()[2]*multiple,image.get_rect()[3]*multiple))
    return image
back_init = Player(
            image_list = [image(0.96),image(0.98),image(1.01),image(1.03),image(1.01),image(0.99),image(1)],
            speed=0.5)
start_down = Player(
            image_list = [image(1),image(0.99),image(0.97),image(0.95),image(0.94),image(0.95)],
            speed=0.5)

b.init_image=image(1)
b.active_image=image(1)
b.down_image = image(1)
b.set_pos("topleft",[350,200])

# =================


while running:
    # 设定帧数
    clock.tick(60)

    # 获取鼠标位置
    pos = pygame.mouse.get_pos()

    # 延时计时器刷新
    if delay == 0:
        delay = 60

    delay -= 1

    # 检测是否全屏
    if fullscreen and screen_change:
        screen = pygame.display.set_mode(size,FULLSCREEN,HWSURFACE)
        screen_change = False
    elif screen_change:
        screen = pygame.display.set_mode(size)
        screen_change = False

    # 事件检测
    events = pygame.event.get()
    for event in events:
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        # 鼠标
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1: # 左键按下，获取鼠标位置
                pass

        # 按键按下事件
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
                
            #F11切换全屏
            if event.key == K_F11:
                fullscreen = not fullscreen
                screen_change = True

        # 按键抬起事件
        if event.type == KEYUP:
            pass


    #画背景
    screen.fill(bg_color)
    for i in range(int(800/50)):
        pygame.draw.line(screen,(0,0,0),[i*800/16,0],[i*800/16,600])
    for i in range(int(600/50)):
        pygame.draw.line(screen,(0,0,0),[0,i*600/12],[800,i*600/12])
    if back_init.running:
        b.active_image=back_init.update()
    if start_down.running:
        b.down_image=start_down.update()
    
    # 刷新xxx
    guis.update(pos=pos,events = events)

    #画 xxxx
    guis.draw(screen)
    

    # 刷新界面
    pygame.display.update()

    

