import sys
import pygame
import random
from time import sleep
from pygame.sprite import collide_rect

# 常量设置
BG_COLOR = pygame.Color(255, 255, 255)
TEXT_COLOR = pygame.Color(255, 0, 0)
WHITE = pygame.Color(255, 255, 255)
BLACK = pygame.Color(0, 0, 0)
GOLD = pygame.Color(255, 215, 0) # 胜利文字颜色
SCREEM_WIDTH = 800
SCREEN_HEIGHT = 600

class Tank:
    def __init__(self) -> None:
        self.images = None
        self.direction = 'U'
        self.image = None
        self.rect = None
        self.speed = 5
        self.remove = False
        self.live = True
        self.old_left = None
        self.old_top = None

    def display_tank(self) -> None:
        self.image = self.images.get(self.direction)
        maingame.window.blit(self.image, self.rect)

    def move(self) -> None:
        self.old_left = self.rect.left
        self.old_top = self.rect.top
        
        if self.direction == 'U':
            if self.rect.top > 0: self.rect.top -= self.speed
        elif self.direction == 'D':
            if self.rect.top + self.rect.height < SCREEN_HEIGHT: self.rect.top += self.speed
        elif self.direction == 'L':
            if self.rect.left > 0: self.rect.left -= self.speed
        elif self.direction == 'R':
            if self.rect.left + self.rect.width < SCREEM_WIDTH: self.rect.left += self.speed

    def tank_hit_wall(self) -> None:
        for wall_obj in maingame.wall_list:
            if collide_rect(self, wall_obj):
                self.rect.left = self.old_left
                self.rect.top = self.old_top

    def tank_collide_tank(self, target_tank) -> None:
        if target_tank and target_tank != self:
            if collide_rect(self, target_tank):
                self.rect.left = self.old_left
                self.rect.top = self.old_top

class my_tank(Tank):
    def __init__(self, left: int, top: int) -> None:
        super().__init__()
        self.scale_size = (60, 60)
        self.images = {
            'U': pygame.transform.scale(pygame.image.load(r'./img/头像up.jpg'), self.scale_size),
            'D': pygame.transform.scale(pygame.image.load(r'./img/头像down.jpg'), self.scale_size),
            'L': pygame.transform.scale(pygame.image.load(r'./img/头像left.jpg'), self.scale_size),
            'R': pygame.transform.scale(pygame.image.load(r'./img/头像right.jpg'), self.scale_size),
        }
        self.direction = 'U'
        self.image = self.images.get(self.direction)
        self.rect = self.image.get_rect()
        self.rect.center = (left, top)

class enemy_tank(Tank):
    def __init__(self, left: int, top: int) -> None:
        super().__init__()
        self.scale_size = (60, 60)
        self.images = {
            'U': pygame.transform.scale(pygame.image.load(r'./img/冬瓜的头像up.jpg'), self.scale_size),
            'D': pygame.transform.scale(pygame.image.load(r'./img/冬瓜的头像down.jpg'), self.scale_size),
            'L': pygame.transform.scale(pygame.image.load(r'./img/冬瓜的头像left.jpg'), self.scale_size),
            'R': pygame.transform.scale(pygame.image.load(r'./img/冬瓜的头像right.jpg'), self.scale_size),
        }
        self.direction = self.ran_direction()
        self.image = self.images.get(self.direction)
        self.rect = self.image.get_rect()
        self.rect.center = (left, top)
        self.step = 20

    def ran_direction(self) -> str:
        return random.choice(['U', 'D', 'L', 'R'])

    def rand_move(self):
        if self.step <= 0:
            self.direction = self.ran_direction()
            self.step = 20
        else:
            self.move()
            self.step -= 1

    def shoot(self):
        if random.randint(1, 100) <= 3:
            return bullet(self)

class bullet:
    def __init__(self, tank: Tank) -> None:
        img = pygame.image.load('./img/烤鸡.png')
        self.image = pygame.transform.scale(img, (20, 20))
        self.direction = tank.direction
        self.rect = self.image.get_rect()
        if self.direction == 'U':
            self.rect.left = tank.rect.left + tank.rect.width/2 - self.rect.width/2
            self.rect.top = tank.rect.top - self.rect.height
        elif self.direction == 'D':
            self.rect.left = tank.rect.left + tank.rect.width/2 - self.rect.width/2
            self.rect.top = tank.rect.top + tank.rect.height
        elif self.direction == 'L':
            self.rect.left = tank.rect.left - self.rect.width
            self.rect.top = tank.rect.top + tank.rect.height/2 - self.rect.height/2
        elif self.direction == 'R':
            self.rect.left = tank.rect.left + tank.rect.width
            self.rect.top = tank.rect.top + tank.rect.height/2 - self.rect.height/2
        self.speed = 8
        self.live = True

    def display_bullet(self) -> None:
        maingame.window.blit(self.image, self.rect)

    def move(self) -> None:
        if self.direction == 'U': self.rect.top -= self.speed
        elif self.direction == 'D': self.rect.top += self.speed
        elif self.direction == 'L': self.rect.left -= self.speed
        elif self.direction == 'R': self.rect.left += self.speed
        if not (0 <= self.rect.top <= SCREEN_HEIGHT and 0 <= self.rect.left <= SCREEM_WIDTH):
            self.live = False

    def hit_enemy_tank(self):
        for e_tank in maingame.enemy_tk_list:
            if collide_rect(self, e_tank):
                maingame.explode_list.append(explode(e_tank))
                self.live = False
                e_tank.live = False

    def hit_my_tank(self):
        if maingame.my_tk and maingame.my_tk.live:
            if collide_rect(self, maingame.my_tk):
                # 产生爆炸，但不在这里播放音效
                maingame.explode_list.append(explode(maingame.my_tk))
                maingame.my_tk.live = False
                self.live = False

    def hit_wall(self):
        for wall_obj in maingame.wall_list:
            if collide_rect(self, wall_obj):
                self.live = False
                wall_obj.hp -= 1
                if wall_obj.hp <= 0: wall_obj.live = False

class wall:
    def __init__(self, left: int, top: int):
        self.image = pygame.image.load('./img/墙壁网格.png')
        self.image = pygame.transform.scale(self.image, (60, 60))
        self.rect = self.image.get_rect()
        self.rect.center = (left, top)
        self.hp = 5
        self.live = True

    def display_wall(self) -> None:
        maingame.window.blit(self.image, self.rect)

class explode:
    def __init__(self, tank: Tank) -> None:
        self.live = True
        self.image = pygame.image.load('./img/爆炸.png')
        self.image = pygame.transform.scale(self.image, (60, 60))
        self.rect = tank.rect

class music:
    def __init__(self, file_name: str) -> None:
        pygame.mixer.init()
        pygame.mixer.music.load(file_name)
    def play_music(self) -> None:
        pygame.mixer.music.play()

class maingame:
    window = None
    my_tk = None
    enemy_tk_list = []
    mybullet_list = []
    e_bullet_list = []
    explode_list = []
    wall_list: list[wall] = []
    enemy_tank_num = 5
    game_state = 'start' # 状态: start, playing, gameover, win

    def display_enemy_tank(self) -> None:
        for e_tank in self.enemy_tk_list[:]:
            if e_tank.live:
                e_tank.display_tank()
                e_tank.rand_move()
                e_tank.tank_hit_wall()
                e_tank.tank_collide_tank(maingame.my_tk)
                for other in self.enemy_tk_list: e_tank.tank_collide_tank(other)
                e_bullet = e_tank.shoot()
                if e_bullet: maingame.e_bullet_list.append(e_bullet)
            else:
                # 只有敌人死的时候放音效
                music(r'./img/菜就多练.mp3').play_music()
                self.enemy_tk_list.remove(e_tank)

    def display_enemy_bullet(self) -> None:
        for e_bullet in maingame.e_bullet_list[:]:
            if e_bullet.live:
                e_bullet.display_bullet()
                e_bullet.move()
                e_bullet.hit_wall()
                e_bullet.hit_my_tank()
            else: maingame.e_bullet_list.remove(e_bullet)

    def display_bullet(self) -> None:
        for my_bullet in maingame.mybullet_list[:]:
            if my_bullet.live:
                my_bullet.display_bullet()
                my_bullet.move()
                my_bullet.hit_wall()
                my_bullet.hit_enemy_tank()
            else:
                maingame.mybullet_list.remove(my_bullet)

    def display_explode(self) -> None:
        for exp in maingame.explode_list[:]:
            if exp.live:
                maingame.window.blit(exp.image, exp.rect)
                exp.live = False
            else: maingame.explode_list.remove(exp)

    def creat_my_tank(self) -> None:
        maingame.my_tk = my_tank(400, 500)

    def create_wall(self) -> None:
        maingame.wall_list.clear()
        top = 200
        for _ in range(3):
            for i in range(6):
                maingame.wall_list.append(wall(i * 140 + 50, top))
            top += 150

    def get_text_surface(self, text: str, size=18, color=TEXT_COLOR):
        pygame.font.init()
        font = pygame.font.SysFont("kaiti", size)
        return font.render(text, True, color)

    def draw_start_screen(self):
        maingame.window.fill(BLACK)
        title = self.get_text_surface("小混沌大战冬瓜", 45, WHITE)
        hint_start = self.get_text_surface("按 ENTER 开始游戏", 25, WHITE)
        hint_move = self.get_text_surface("操作说明：", 20, TEXT_COLOR)
        hint_keys = self.get_text_surface("W A S D 控制移动", 18, WHITE)
        hint_shoot = self.get_text_surface("SPACE (空格) 发射炮弹", 18, WHITE)
        maingame.window.blit(title, (SCREEM_WIDTH/2 - 160, 150))
        maingame.window.blit(hint_start, (SCREEM_WIDTH/2 - 110, 280))
        maingame.window.blit(hint_move, (SCREEM_WIDTH/2 - 50, 380))
        maingame.window.blit(hint_keys, (SCREEM_WIDTH/2 - 80, 420))
        maingame.window.blit(hint_shoot, (SCREEM_WIDTH/2 - 95, 450))

    def draw_game_over(self):
        maingame.window.fill(BLACK)
        tip = self.get_text_surface("NO！！我不服凑冬瓜，我要再战！！！", 35, TEXT_COLOR)
        hint = self.get_text_surface("(按 ESC 重新开始)", 25, WHITE)
        maingame.window.blit(tip, (SCREEM_WIDTH/2 - 250, SCREEN_HEIGHT/2 - 50))
        maingame.window.blit(hint, (SCREEM_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 50))

    def draw_win_screen(self):
        """绘制胜利界面"""
        maingame.window.fill(BLACK)
        tip = self.get_text_surface("凑冬瓜真是太逊了，哈哈哈", 40, GOLD)
        hint = self.get_text_surface("(按 ESC 再虐一轮)", 25, WHITE)
        maingame.window.blit(tip, (SCREEM_WIDTH/2 - 240, SCREEN_HEIGHT/2 - 50))
        maingame.window.blit(hint, (SCREEM_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 50))

    def start_game(self) -> None:
        pygame.init()
        maingame.window = pygame.display.set_mode((SCREEM_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("小混沌大战冬瓜")
        self.creat_my_tank()
        self.create_enemy_tank()
        self.create_wall()

        while True:
            sleep(0.03)
            maingame.window.fill(BG_COLOR)
            self.get_event()

            if maingame.game_state == 'start':
                self.draw_start_screen()
            
            elif maingame.game_state == 'playing':
                text = self.get_text_surface(f"冬瓜剩余数量 {len(self.enemy_tk_list)}")
                maingame.window.blit(text, (10, 10))
                
                # 胜利判定：如果敌方坦克列表空了
                if len(self.enemy_tk_list) == 0:
                    maingame.game_state = 'win'

                if maingame.my_tk and maingame.my_tk.live:
                    maingame.my_tk.display_tank()
                    if maingame.my_tk.remove:
                        maingame.my_tk.move()
                        maingame.my_tk.tank_hit_wall()
                        for e in self.enemy_tk_list: maingame.my_tk.tank_collide_tank(e)
                else: 
                    maingame.game_state = 'gameover'
                
                self.display_enemy_tank()
                self.display_bullet()
                self.display_enemy_bullet()
                self.display_explode()
                
                for wall_obj in maingame.wall_list[:]:
                    if wall_obj.live: wall_obj.display_wall()
                    else: maingame.wall_list.remove(wall_obj)
            
            elif maingame.game_state == 'gameover':
                self.draw_game_over()
            
            elif maingame.game_state == 'win':
                self.draw_win_screen()
            
            pygame.display.update()

    def create_enemy_tank(self) -> None:
        self.enemy_tk_list.clear()
        for _ in range(self.enemy_tank_num):
            left = random.randint(50, SCREEM_WIDTH - 50)
            self.enemy_tk_list.append(enemy_tank(left, 100))

    def get_event(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.KEYDOWN:
                if maingame.game_state == 'start' and event.key == pygame.K_RETURN:
                    maingame.game_state = 'playing'
                # 在死亡或胜利界面按 ESC 都可以重开
                if (maingame.game_state == 'gameover' or maingame.game_state == 'win') and event.key == pygame.K_ESCAPE:
                    maingame.mybullet_list.clear() # 清空之前的子弹
                    maingame.e_bullet_list.clear()
                    self.creat_my_tank()
                    self.create_enemy_tank()
                    self.create_wall()
                    maingame.game_state = 'playing'
                
                if maingame.game_state == 'playing' and maingame.my_tk and maingame.my_tk.live:
                    if event.key == pygame.K_SPACE and len(maingame.mybullet_list) < 5:
                        maingame.mybullet_list.append(bullet(maingame.my_tk))

        keys = pygame.key.get_pressed()
        if maingame.game_state == 'playing' and maingame.my_tk and maingame.my_tk.live:
            if keys[pygame.K_w]: maingame.my_tk.direction = 'U'; maingame.my_tk.remove = True
            elif keys[pygame.K_s]: maingame.my_tk.direction = 'D'; maingame.my_tk.remove = True
            elif keys[pygame.K_a]: maingame.my_tk.direction = 'L'; maingame.my_tk.remove = True
            elif keys[pygame.K_d]: maingame.my_tk.direction = 'R'; maingame.my_tk.remove = True
            else: maingame.my_tk.remove = False

if __name__ == "__main__":
    maingame().start_game()