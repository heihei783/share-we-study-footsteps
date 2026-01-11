import pygame
import random
from time import sleep
from pygame.sprite import collide_rect
BG_COLOR = pygame.Color(255,255,255)
TEXT_COLOR = pygame.Color(255,0,0)
SCREEM_WIDTH = 800
SCREEN_HEIGHT = 600

class Tank:
    
    def __init__(self) -> None:
        self.images=None
        self.direction=None
        self.image=None
        self.rect=None
        self.speed=5
        self.remove=False
        self.live=True
        self.old_left=None
        self.old_top=None
    def display_tank(self)->None:
        self.image=self.images.get(self.direction)
        maingame.window.blit(self.image,self.rect)
    def move(self)->None:
        self.old_left=self.rect.left
        self.old_top=self.rect.top
        if self.direction=='U':
            if self.rect.top>0:
                self.rect.top-=self.speed
        elif self.direction=='D':
            if self.rect.top+self.rect.height<SCREEN_HEIGHT:
                self.rect.top+=self.speed
        elif self.direction=='L':
            if self.rect.left>0:
                self.rect.left-=self.speed
        elif self.direction=='R':
            if self.rect.left+self.rect.width<SCREEM_WIDTH:
                self.rect.left+=self.speed
    def shoot(self)->None:
        pass

    def tank_hit_wall(self)->bool:
        for wall in maingame.wall_list:
            if pygame.sprite.collide_rect(self,wall):
                self.rect.left=self.old_left
                self.rect.top=self.old_top

    def tank_collide_tank(self,tank)->bool:
        if pygame.sprite.collide_rect(self,tank):
            self.rect.left=self.old_left
            self.rect.top=self.old_top

class my_tank(Tank):
    def __init__(self,left:int,top:int)->None:
        super().__init__()
        self.scale_size = (60, 60)
        self.images={
            'U':pygame.transform.scale(pygame.image.load(r'./img/头像up.jpg'), self.scale_size),
            'D':pygame.transform.scale(pygame.image.load(r'./img/头像down.jpg'), self.scale_size),
            'L':pygame.transform.scale(pygame.image.load(r'./img/头像left.jpg'), self.scale_size),
            'R':pygame.transform.scale(pygame.image.load(r'./img/头像right.jpg'), self.scale_size),
        }
        self.direction='U'

        self.image=self.images.get(self.direction)
        self.rect = self.image.get_rect()
        self.rect.center = (left, top)

class enemy_tank(Tank):
    def __init__(self,left:int,top:int)->None:
        super().__init__()
        self.scale_size = (60, 60)
        self.images={
            'U':pygame.transform.scale(pygame.image.load(r'./img/冬瓜的头像up.jpg'), self.scale_size),
            'D':pygame.transform.scale(pygame.image.load(r'./img/冬瓜的头像down.jpg'), self.scale_size),
            'L':pygame.transform.scale(pygame.image.load(r'./img/冬瓜的头像left.jpg'), self.scale_size),
            'R':pygame.transform.scale(pygame.image.load(r'./img/冬瓜的头像right.jpg'), self.scale_size),
        }
        self.direction=self.ran_direction()
        self.image= self.images.get(self.direction)
        self.rect = self.image.get_rect()
        self.rect.center = (left, top)
        self.step=20
        
    def ran_direction(self)->str:
        chice=random.randint(1,4) 
        if chice==1:
            return 'U' 
        elif chice==2:
            return 'D' 
        elif chice==3:
            return 'L' 
        elif chice==4:
            return 'R' 
    
    def rand_move(self):
        if self.step<=0:
            self.direction=self.ran_direction()
            self.step=20
        else:
            self.move()
            self.step-=1
    def shoot(self)->None:
        num=random.randint(1,100)
        if num<=3:
            return bullet(self)
    
    

class bullet:
    def __init__(self,tank:Tank)->None:
        img = pygame.image.load('./img/烤鸡.png')
        self.image = pygame.transform.scale(img, (20, 20))
        # self.image.fill((255, 0, 0))
        self.direction=tank.direction
        self.rect = self.image.get_rect()
        if self.direction=='U':
            self.rect.left = tank.rect.left+tank.rect.width/2-self.rect.width/2
            self.rect.top = tank.rect.top - self.rect.height
        elif self.direction=='D':
            self.rect.left=tank.rect.left+tank.rect.width/2-self.rect.width/2
            self.rect.top=tank.rect.top+tank.rect.height
        elif self.direction=='L':
            self.rect.left = tank.rect.left - self.rect.width
            self.rect.top = tank.rect.top+tank.rect.height/2-self.rect.height/2
        elif self.direction=='R':
            self.rect.left = tank.rect.left + self.rect.width
            self.rect.top = tank.rect.top+tank.rect.height/2-self.rect.height/2
        self.speed=8
        self.live=True
    def display_bullet(self)->None:
        maingame.window.blit(self.image,self.rect)

    def move(self)->None:
        if self.direction=='U':
            if self.rect.top>0:
                self.rect.top-=self.speed
            else:
                self.live=False
        elif self.direction=='D':
            if self.rect.top+self.rect.height<SCREEN_HEIGHT:
                self.rect.top+=self.speed
            else:
                self.live=False
        elif self.direction=='L':
            if self.rect.left>0:
                self.rect.left-=self.speed
            else:
                self.live=False
        elif self.direction=='R':
            if self.rect.left+self.rect.width<SCREEM_WIDTH:
                self.rect.left+=self.speed
            else:
                self.live=False

    def hit_enemy_tank(self)->bool:
        for e_tank in maingame.enemy_tk_list:
            if collide_rect(self,e_tank):
                epl=explode(e_tank)
                maingame.explode_list.append(epl)
                self.live=False
                e_tank.live=False
    def hit_my_tank(self)->bool:
        if maingame.my_tk and maingame.my_tk.live:
            if collide_rect(self,maingame.my_tk):
                exp=explode(maingame.my_tk)
                maingame.explode_list.append(exp)
                maingame.my_tk.live=False
                self.live=False

    def hit_wall(self)->bool:
        for wall in maingame.wall_list:
            if collide_rect(self,wall):
                self.live=False
                wall.hp-=1
                if wall.hp<=0:
                    wall.live=False
            
        


class wall:
    def __init__(self,left:int,top:int):
        self.image=pygame.image.load('./img/墙壁网格.png')
        self.image = pygame.transform.scale(self.image, (60, 60))
        self.rect = self.image.get_rect()
        self.rect.center=(left,top)
        self.hp=5
        self.live=True
    def display_wall(self)->None:
        maingame.window.blit(self.image,self.rect)
    
class explode:
    def __init__(self,tank:Tank)->None:
        self.live=True
        self.image=pygame.image.load('./img/爆炸.png')
        self.image = pygame.transform.scale(self.image, (60, 60))
        self.rect = tank.rect

    

class music:
    def __init__(self,file_name:str)->None:
        pygame.mixer.init()
        pygame.mixer.music.load(file_name)
        
    def play_music(self)->None:
        pygame.mixer.music.play()


class maingame:
    window=None
    my_tk=None
    enemy_tk_list=[]
    mybullet_list=[]
    e_bullet_list=[]
    explode_list=[]
    wall_list:list[wall]=[]
    enemy_tank_num=5

    def __init__(self)->None:
        pass
    
    def display_enemy_tank(self)->None:
        for e_tank in self.enemy_tk_list:
            if e_tank.live:
                e_tank.display_tank()
                e_tank.rand_move()
                e_tank.tank_hit_wall()
                e_tank.tank_collide_tank(maingame.my_tk)
                for e_tk in self.enemy_tk_list:
                    if e_tk!=e_tank:
                        e_tank.tank_collide_tank(e_tk)
                e_bullet=e_tank.shoot()
                if e_bullet:
                    maingame.e_bullet_list.append(e_bullet)
            else:
                msc=music(r'./img/菜就多练.mp3')
                msc.play_music()
                self.enemy_tk_list.remove(e_tank)

    def display_enemy_bullet(self)->None:
        for e_bullet in maingame.e_bullet_list:
            if e_bullet.live:
                e_bullet.display_bullet()
                e_bullet.move()
                e_bullet.hit_wall()
                e_bullet.hit_my_tank()
            else:
                maingame.e_bullet_list.remove(e_bullet)
    def display_explode(self)->None:
        for exp in maingame.explode_list:
            if exp.live:
                maingame.window.blit(exp.image,exp.rect)
                exp.live=False
            else:
                maingame.explode_list.remove(exp)
    def creat_my_tank(self)->None:
            maingame.window=pygame.display.set_mode((SCREEM_WIDTH,SCREEN_HEIGHT))
            maingame.my_tk=my_tank(400,500)
    def create_wall(self)->None:
        top=200
        for i in range(3):
            for i in range(6):
                wall1=wall(i*140+40,top)
                maingame.wall_list.append(wall1)
            top+=150
            
        
        
    def display_wall_main(self)->None:
        for wall in maingame.wall_list:
            if wall.live:
                wall.display_wall()
            else:
                maingame.wall_list.remove(wall)

    def start_game(self)->None:
        pygame.init()
        self.creat_my_tank()
        pygame.display.set_caption("小混沌大战冬瓜")
        self.create_enemy_tank()
        self.create_wall()
        while True:
            sleep(0.03)
            maingame.window.fill(BG_COLOR)
            text=self.get_text_surface(f"冬瓜剩余数量{len(self.enemy_tk_list)}")
            maingame.window.blit(text,(10,10))
            #增加事件监听
            self.get_event()
            if maingame.my_tk and maingame.my_tk.live:
                if maingame.my_tk.live and maingame.my_tk:
                    maingame.my_tk.display_tank()
                else:
                    maingame.my_tk=None
            self.display_enemy_tank()
            if maingame.my_tk and maingame.my_tk.live:
                if maingame.my_tk.remove:
                    maingame.my_tk.move()
                    maingame.my_tk.tank_hit_wall()
                    for e_tank in maingame.enemy_tk_list:
                        maingame.my_tk.tank_collide_tank(e_tank)
            self.display_bullet()
            self.display_enemy_bullet()
            self.display_explode()
            self.display_wall_main()
            pygame.display.update()

    def create_enemy_tank(self)->None:
        self.enemy_top=100
        for i in range(self.enemy_tank_num):
            left = random.randint(0, SCREEM_WIDTH-100)
            e_tank = enemy_tank(left,self.enemy_top)
            self.enemy_tk_list.append(e_tank)



    def get_text_surface(self,text:str)->None:
        pygame.font.init()
        font= pygame.font.SysFont("kaiti",18)
        text_surface=font.render(text,True,TEXT_COLOR)
        return text_surface
    
    def display_bullet(self)->None:
        for my_bullet in maingame.mybullet_list:
            if my_bullet.live:
                my_bullet.display_bullet()
                my_bullet.move()
                my_bullet.hit_wall()
                my_bullet.hit_enemy_tank()
            else:
                maingame.mybullet_list.remove(my_bullet)

    def get_event(self)->None:
        event_list=pygame.event.get()
        for event in event_list:
            if event.type == pygame.KEYDOWN:
                if (not maingame.my_tk or not maingame.my_tk.live) and event.key == pygame.K_ESCAPE:
                    self.creat_my_tank()
            if event.type == pygame.QUIT:
                self.end_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if len(maingame.mybullet_list)<5:
                        my_bullet = bullet(maingame.my_tk)
                        maingame.mybullet_list.append(my_bullet)
        keys = pygame.key.get_pressed()
        if maingame.my_tk and maingame.my_tk.live:
            if keys[pygame.K_w]:
                maingame.my_tk.direction = 'U'
                maingame.my_tk.remove = True
            elif keys[pygame.K_s]:
                maingame.my_tk.direction = 'D'
                maingame.my_tk.remove = True
            elif keys[pygame.K_a]:
                maingame.my_tk.direction = 'L'
                maingame.my_tk.remove = True
            elif keys[pygame.K_d]:
                maingame.my_tk.direction = 'R'
                maingame.my_tk.remove = True
            else:
                # 没有任何方向键被按下时停止
                maingame.my_tk.remove = False
        
            
        

                
                
                
    
    def end_game(self)->None:
        print('冬瓜太逊了，游戏结束')
        exit()
        pass


if __name__=="__main__":
    maingame().start_game()

    
            
    