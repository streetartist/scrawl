from pygameGUI import Widget,PG_Error

class Player(Widget):
    """
    这是一个假装成组件的动画播放器
    用于播放帧动画并且可以重复使用
    通常用于给某些组件作为插件使用
    使用时应与widget对象处于同一组
    在删除widget对象时需要一并删除
    
    """
    def __init__(self,
                 group=None, # 所在的组，通常与widget相同
                 widget=None, # 要动画的组件
                 attr="", # 哪个image属性（字符串属性名
                 image_list=[], # 帧动画
                 speed=1, # 动画放映速度（每帧放多少张
                 ):
        super().__init__(group)
        self.widget = widget
        self.attr = attr
        self.image_list = image_list
        self.index = 0
        self.running = False
        self.speed = speed
        
    def run(self,index=0):
        "调用时，开始播放动画"
        self.running = True
        self.index = index
        
    def update(self,args,kwargs):
        if self.running:
            
            # 根据播放进度得到image
            index = int(self.index)
            if index >= len(self.image_list)-1:
                image = self.image_list[len(self.image_list)-1]
                self.index = 0
                self.running=False
            else:
                image = self.image_list[index]
                self.index += self.speed
                
            # 将widget的attr设置为image
            if hasattr(self.widget,self.attr):
                setattr(self.widget,self.attr,image)
            else:
                index1 = self.attr.find("[")
                index2 = self.attr.find("]")
                if index1 != -1 and  index2 != -1:
                    index = eval(self.attr[index1+1:index2])
                    attr=self.attr[0:index1]
                    if hasattr(self.widget,attr):
                        image_list = getattr(self.widget,attr)
                        image_list[index] = image
                        setattr(self.widget,attr,image_list)
                    else:
                        raise PG_Error(f"{self.widget}对象没有{repr(self.attr)}属性:2")

    def set_pos(self,*args,**kwargs):
        raise PG_Error("'Player对象是一个没有实体的播放器，请勿给它设置位置'")

    def get_pos(self):
        raise PG_Error("'Player对象是一个没有实体的播放器，没有位置属性")







    
