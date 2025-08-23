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

guis = pg.Group()

w1 = pg.Window(group=guis,pos=[150,50],size=[500,400],texture=(240,130,60))
def image(image):
    image.fill((240,190,80))
    image.blit(pg.Label(text="PygameGUI - 输入框",color=(255,255,255)).image,[120,10])
    return image
title = w1.set_title(size=[500,50],texture=image)
def image(image,depth):
    image.fill((255,0,0))
    image.blit(pg.Label(text="×",color=(255,255,255),font=("sthupo",50)).image,[-2,-1])
    image1 = pygame.Surface([image.get_rect()[2],image.get_rect()[3]],pygame.SRCALPHA)
    pygame.draw.rect(image1,rect=image.get_rect(),color=(0,0,0,depth))
    image.blit(image1,[0,0])
    return image
close_button = w1.set_close_button(size=[50,50],
                                   init_texture=lambda img : image(img,0),
                                   active_texture=lambda img : image(img,50),
                                   down_texture=lambda img : image(img,100),)
close_button.set_pos("topright",[500,0])

# 输入框1外边框
def round_angle_rect(image,color,radius):
    rect = image.get_rect()
    # 底色
    pygame.draw.circle(image,color=color,center=[radius,radius],radius=radius)
    pygame.draw.circle(image,color=color,center=[radius,rect[3]-radius],radius=radius)
    pygame.draw.circle(image,color=color,center=[rect[2]-radius,rect[3]-radius],radius=radius)
    pygame.draw.circle(image,color=color,center=[rect[2]-radius,radius],radius=radius)
    pygame.draw.rect(image,color=color,rect=[radius,0,
                                             rect[2]-radius*2,rect[3]])
    pygame.draw.rect(image,color=color,rect=[0,radius,
                                             rect[2],rect[3]-radius*2])
    return image    
ef1 = pg.Frame(group = w1,size=[250,50],
               texture=lambda image : round_angle_rect(image,(255,255,255),5))
ef1.set_pos("center",[w1.rect[2]/2+50, w1.rect[3]/2-60])

# 文本信息1
l1 = pg.Label(group=w1,text="库名：",font=("stxinwei",30),color=(255,255,255))
l1.set_pos("center",[0,ef1.rect.center[1]])
l1.set_pos("right",ef1.rect.left)

# 文本框1
e1 = pg.Entry(group=ef1,texture=(255,255,255),pos=[5,5],size=[240,40])
e1.set_label(text="《PygameGUI》",font=("stsong",30),bg=(255,255,255))
e1.label.set_pos("center",[0,e1.rect[3]/2])
e1.label.set_pos("left",0)


# 输入框2外边框    
ef2 = pg.Frame(group = w1,size=[250,50],
               texture=lambda image : round_angle_rect(image,(255,255,255),5))
ef2.set_pos("center",[w1.rect[2]/2+50, w1.rect[3]/2+30])

# 文本信息2
l2 = pg.Label(group=w1,text="作者：",font=("stxinwei",30),color=(255,255,255))
l2.set_pos("center",[0,ef2.rect.center[1]])
l2.set_pos("right",ef2.rect.left)

# 文本框2
e2 = pg.Entry(group=ef2,texture=(255,255,255),pos=[5,5],size=[240,40])
e2.set_label(text="小甲鱼",font=("stxinwei",30),bg=(255,255,255))
e2.label.set_pos("center",[0,e2.rect[3]/2])
e2.label.set_pos("left",0)


# 输入框3外边框    
ef3 = pg.Frame(group = w1,size=[250,50],
               texture=lambda image : round_angle_rect(image,(255,255,255),5))
ef3.set_pos("center",[w1.rect[2]/2+50, w1.rect[3]/2+90])

# 文本信息3
l3 = pg.Label(group=w1,text="密码：",font=("stxinwei",30),color=(255,255,255))
l3.set_pos("center",[0,ef3.rect.center[1]])
l3.set_pos("right",ef3.rect.left)

# 文本框3
e3 = pg.Entry(group=ef3,texture=(255,255,255),pos=[5,5],size=[240,40],show="*")
e3.set_label(text="",font=("stsong",30),bg=(255,255,255))
e3.label.set_pos("center",[0,e3.rect[3]/2])
e3.label.set_pos("left",0)

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

        elif event.type == 1024:
            pass

    #画背景
    screen.fill(bg_color)
    for i in range(int(800/50)):
        pygame.draw.line(screen,(0,0,0),[i*800/16,0],[i*800/16,600])
    for i in range(int(600/50)):
        pygame.draw.line(screen,(0,0,0),[0,i*600/12],[800,i*600/12])
    
    # 刷新xxx
    guis.update(pos=pos,events = events)

    #画 xxxx
    guis.draw(screen)
    

    # 刷新界面
    pygame.display.update()

    

