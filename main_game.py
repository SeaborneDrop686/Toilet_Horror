# -*- coding: utf-8 -*-
import pygame
from math import sqrt

# ===================== 全局状态变量 =====================
skip_fall_check = 0  # 原 checking，为0时正常检查坠落（即站在非地面上会死亡）
seen_obstacles = []  # 原 saw，用于视野遮挡计算的障碍物列表
view_radius = 10  # 原 num

NORMAL = 1
END = 2
RESTART = 3
game_state = NORMAL  # 原 state，1:正常运行 2:游戏结束 3:重启游戏

# NPC巡逻偏移量
npc_patrol_x = 0  # 原 n0x
npc_patrol_y = 0  # 原 n0y

# 冲刺/潜行状态
sprint_mode: bool = False  # 原 CTRL，1为冲刺
slow_mode: bool = False  # 原 ALT，1为慢走/定身

# 游戏对象列表（用于保存/加载）
walls = []
rocks = []
floors = []
npcs = []
notes = []  # 原 papers
doors = []
linked_doors = []  # 原 ds

# ===================== 初始化 Pygame =====================
pygame.init()
canvas = pygame.display.set_mode((1750, 750))
font_name = pygame.font.match_font("KaiTi")
bigFont = pygame.font.Font(font_name, 250)
font = pygame.font.Font(font_name, 20)
pygame.display.set_caption("厕所惊魂")

# ===================== 读取设置文件 =====================
with open("settings.csjh", encoding="utf-8") as f:
    sound_enabled = int(f.readline())  # 声音开关（未使用）

    # 原 ctrl，1表示Ctrl是切换模式，0表示按住
    ctrl_toggle_mode = int(f.readline())
    # 原 alt，1表示Alt是切换模式，0表示按住
    alt_toggle_mode = int(f.readline())


# ===================== 图像加载函数 =====================
def load_png(name) -> pygame.Surface:
    """加载 images/ 目录下的png图片"""
    return pygame.image.load("assets/textures/" + name + ".png")


# 预加载所有图像资源
air = load_png("air")
p = load_png("p")
npc = load_png("npc")
npc1 = load_png("npc1")
npc2 = load_png("npc2")
npc3 = load_png("npc3")
npc4 = load_png("npc4")
npc5 = load_png("npc5")
paper = load_png("paper")
paper1 = load_png("paper1")
paper2 = load_png("paper2")
paper3 = load_png("paper3")
paper4 = load_png("paper4")
paper5 = load_png("paper5")
floor = load_png("floor")
wall = load_png("wall")
floor1 = load_png("floor1")
wall1 = load_png("wall1")
floor2 = load_png("floor2")
wall2 = load_png("wall2")
floor3 = load_png("floor3")
wall3 = load_png("wall3")
floor4 = load_png("floor4")
wall4 = load_png("wall4")
floor5 = load_png("floor5")
wall5 = load_png("wall5")
rock = load_png("rock")
door = load_png("door")
rock1 = load_png("rock1")
door1 = load_png("door1")
rock2 = load_png("rock2")
door2 = load_png("door2")
rock3 = load_png("rock3")
door3 = load_png("door3")
rock4 = load_png("rock4")
door4 = load_png("door4")
rock5 = load_png("rock5")
door5 = load_png("door5")
f = load_png("f")  # 用于残留影子的默认图像（看上去像地板/空）
white = load_png("white")
rline = load_png("rline")  # 红色血条线段
bline = load_png("bline")  # 蓝色耐力条线段


def say(s, y):
    """在屏幕左侧显示对话文字"""
    font_surface = font.render(s, True, "black")
    canvas.blit(font_surface, (100, y * 30 + 50))


# ===================== 基础实体类（包含多级LOD绘制和视线检测） =====================
class BaseEntity:  # 原 al
    """所有可绘制对象的基类，提供5级细节绘制和视线遮挡检测"""

    def paint(self, x, y):
        canvas.blit(self.img, (self.x - x + 875, self.y - y + 375))

    def paint1(self, x, y):
        canvas.blit(self.img1, (self.x - x + 875, self.y - y + 375))

    def paint2(self, x, y):
        canvas.blit(self.img2, (self.x - x + 875, self.y - y + 375))

    def paint3(self, x, y):
        canvas.blit(self.img3, (self.x - x + 875, self.y - y + 375))

    def paint4(self, x, y):
        canvas.blit(self.img4, (self.x - x + 875, self.y - y + 375))

    def paint5(self, x, y):
        canvas.blit(self.img5, (self.x - x + 875, self.y - y + 375))

    def f(self, x, y):
        """绘制残留影子（完全离开视野后的残留）"""
        canvas.blit(self.img_residual, (self.x - x + 875, self.y - y + 375))

    def seen(self, x, y, obstacles):
        """
        检测从玩家位置(x,y)到实体自身是否被障碍物列表obstacles遮挡。
        返回 1 表示可见，0 表示被遮挡。
        """
        # 复杂的几何计算，判断是否有障碍物挡在玩家与实体之间
        for i in obstacles:
            if (
                i.x >= x
                and i.y <= y
                and self.y < i.y
                and self.x > i.x
                and i.x - x != 10
                and x - i.x != 10
                and i.x - x != 30
                and x - i.x != 30
                and self.y + 10
                >= (i.y - y - 10) / (i.x - x + 10) * (self.x + 10)
                + y
                + 10
                - (x + 10) * (i.y - y - 10) / (i.x - x + 10)
                and self.y + 10
                <= (i.y + 20 - y - 10) / (i.x + 20 - x + 10) * (self.x + 10)
                + y
                + 10
                - (x + 10) * (i.y + 20 - y - 10) / (i.x + 20 - x + 10)
            ):
                return 0
            if (
                i.x <= x
                and i.y >= y
                and self.y > i.y
                and self.x < i.x
                and i.x - x != 10
                and x - i.x != 10
                and i.x - x != 30
                and x - i.x != 30
                and self.y + 10
                >= (i.y - y - 10) / (i.x - x + 10) * (self.x + 10)
                + y
                + 10
                - (x + 10) * (i.y - y - 10) / (i.x - x + 10)
                and self.y + 10
                <= (i.y + 20 - y - 10) / (i.x + 20 - x + 10) * (self.x + 10)
                + y
                + 10
                - (x + 10) * (i.y + 20 - y - 10) / (i.x + 20 - x + 10)
            ):
                return 0
            if (
                i.x >= x
                and i.y >= y
                and self.y > i.y
                and self.x > i.x
                and i.x - x != 10
                and x - i.x != 10
                and i.x - x != 30
                and x - i.x != 30
                and self.y + 10
                >= (i.y - y - 10) / (i.x + 20 - x + 10) * (self.x + 10)
                + y
                + 10
                - (x + 10) * (i.y - y - 10) / (i.x + 20 - x + 10)
                and self.y + 10
                <= (i.y + 20 - y - 10) / (i.x - x + 10) * (self.x + 10)
                + y
                + 10
                - (x + 10) * (i.y + 20 - y - 10) / (i.x - x + 10)
            ):
                return 0
            if (
                i.x <= x
                and i.y <= y
                and self.y < i.y
                and self.x < i.x
                and i.x - x != 10
                and x - i.x != 10
                and i.x - x != 30
                and x - i.x != 30
                and self.y + 10
                <= (i.y + 20 - y - 10) / (i.x - x + 10) * (self.x + 10)
                + y
                + 10
                - (x + 10) * (i.y + 20 - y - 10) / (i.x - x + 10)
                and self.y + 10
                >= (i.y - y - 10) / (i.x + 20 - x + 10) * (self.x + 10)
                + y
                + 10
                - (x + 10) * (i.y - y - 10) / (i.x + 20 - x + 10)
            ):
                return 0
        return 1


# ===================== 玩家类 =====================
class Player:  # 原 Person
    def __init__(self):
        self.x = 500
        self.y = 100
        self.vel_x = 0  # 原 xs
        self.vel_y = 0  # 原 ys
        self.speed = 3  # 基础速度
        self.inventory_count = 0  # 原 i，背包中物品数量
        self.inventory = []  # 原 l，背包物品列表
        self.health = 10000  # 原 live，生命值
        self.stamina = 1000  # 原 strong，耐力值

    def paint(self):
        """绘制玩家及状态栏"""
        canvas.blit(p, (875, 375))
        font_surface = font.render("live", True, "red")
        canvas.blit(font_surface, (1500, 20))
        font_surface = font.render(str(self.health), True, "red")
        canvas.blit(font_surface, (1500, 60))
        for i in range(int(self.health / 20)):
            canvas.blit(rline, (1500, 100 + i))
        font_surface = font.render("strength", True, "blue")
        canvas.blit(font_surface, (1600, 20))
        font_surface = font.render(str(self.stamina), True, "blue")
        canvas.blit(font_surface, (1600, 60))
        for i in range(int(self.stamina / 2)):
            canvas.blit(bline, (1600, 100 + i))

    def move_left(self):
        self.vel_x = -self.speed
        if self.speed == 7:
            self.stamina -= 3

    def move_right(self):
        self.vel_x = self.speed
        if self.speed == 7:
            self.stamina -= 3

    def move_up(self):
        self.vel_y = -self.speed
        if self.speed == 7:
            self.stamina -= 3

    def move_down(self):
        self.vel_y = self.speed
        if self.speed == 7:
            self.stamina -= 3

    def move(self):
        """更新位置，应用摩擦力，自然恢复耐力"""
        self.x += self.vel_x
        self.y += self.vel_y
        # 摩擦力减速
        if self.vel_x < 0:
            self.vel_x += 0.2
        if self.vel_x > 0:
            self.vel_x -= 0.2
        if self.vel_y < 0:
            self.vel_y += 0.2
        if self.vel_y > 0:
            self.vel_y -= 0.2
        if -0.2 < self.vel_x < 0.2:
            self.vel_x = 0
        if -0.2 < self.vel_y < 0.2:
            self.vel_y = 0
        # 耐力恢复
        if self.vel_x == 0 and self.vel_y == 0:
            self.stamina += 2
        else:
            self.stamina += 1

    def resolve_collisions(self, obstacles):
        """处理与障碍物及关闭的门的碰撞，并检查是否站在地面上"""
        global game_state
        # 碰撞推开
        for i in obstacles:
            if (
                i.x <= self.x + 22
                and i.x >= self.x - 22
                and i.y <= self.y + 22 + self.speed
                and i.y >= self.y + 18
            ):
                self.y = i.y - 22 - self.speed
            if (
                i.x <= self.x + 22 + self.speed
                and i.x >= self.x + 18
                and i.y <= self.y + 22
                and i.y >= self.y - 22
            ):
                self.x = i.x - 22 - self.speed
            if (
                i.x <= self.x - 18
                and i.x >= self.x - 22 - self.speed
                and i.y <= self.y + 22
                and i.y >= self.y - 22
            ):
                self.x = i.x + 22 + self.speed
            if (
                i.x <= self.x + 22
                and i.x >= self.x - 22
                and i.y >= self.y - 22 - self.speed
                and i.y <= self.y - 18
            ):
                self.y = i.y + 22 + self.speed
        # 对打开的门也推开（门关闭时不挡路？原逻辑如此，可能是为了防止卡住）
        for i in doors:
            if i.open:
                if (
                    i.x <= self.x + 22
                    and i.x >= self.x - 22
                    and i.y <= self.y + 22 + self.speed
                    and i.y >= self.y + 18
                ):
                    self.y = i.y - 22 - self.speed
                if (
                    i.x <= self.x + 22 + self.speed
                    and i.x >= self.x + 18
                    and i.y <= self.y + 22
                    and i.y >= self.y - 22
                ):
                    self.x = i.x - 22 - self.speed
                if (
                    i.x <= self.x - 18
                    and i.x >= self.x - 22 - self.speed
                    and i.y <= self.y + 22
                    and i.y >= self.y - 22
                ):
                    self.x = i.x + 22 + self.speed
                if (
                    i.x <= self.x + 22
                    and i.x >= self.x - 22
                    and i.y >= self.y - 22 - self.speed
                    and i.y <= self.y - 18
                ):
                    self.y = i.y + 22 + self.speed
        # 检查是否站在地面上
        on_floor = False
        for fl in floors:
            if (
                fl.x <= self.x + 20
                and fl.x >= self.x - 20
                and fl.y <= self.y + 20
                and fl.y >= self.y - 20
            ):
                on_floor = True
                break
        if not on_floor and not skip_fall_check:
            game_state = 2  # 坠落死亡

        # 属性上限与下限
        if self.stamina > 1000:
            self.stamina = 1000
        if self.stamina < 0:
            self.stamina = 0
        if self.health > 10000:
            self.health = 10000
        if self.health < 0:
            self.health = 0
        if self.health == 0:
            game_state = 2


# ===================== NPC 类 =====================
class NPC(BaseEntity):
    def __init__(
        self,
        x,
        y,
        dialogue1,
        dialogue2="",
        dialogue3="",
        dialogue4="",
        dialogue5="",
    ):
        self.x = x
        self.y = y
        self.saved_x = x  # 记录初始位置（用于残留影子绘制）
        self.saved_y = y
        self.linger_far = 0  # 原 view，远端残留计时器
        self.linger_mid = 0  # 原 fview，中距离残留计时器
        self.linger_close = 0  # 原 nview，近距离残留计时器
        self.dialogue = (
            dialogue1,
            dialogue2,
            dialogue3,
            dialogue4,
            dialogue5,
        )  # 对话内容
        # 图像
        self.img = npc
        self.img1 = npc1
        self.img2 = npc2
        self.img3 = npc3
        self.img4 = npc4
        self.img5 = npc5
        self.img_residual = p

    def paint(self, x, y):
        canvas.blit(self.img, (self.x - x + 875, self.y - y + 375))
        self.saved_x = self.x
        self.saved_y = self.y

    def paint1(self, x, y):
        canvas.blit(self.img1, (self.x - x + 875, self.y - y + 375))
        self.saved_x = self.x
        self.saved_y = self.y

    def paint2(self, x, y):
        canvas.blit(self.img2, (self.x - x + 875, self.y - y + 375))
        self.saved_x = self.x
        self.saved_y = self.y

    def paint3(self, x, y):
        canvas.blit(self.img3, (self.x - x + 875, self.y - y + 375))
        self.saved_x = self.x
        self.saved_y = self.y

    def paint4(self, x, y):
        canvas.blit(
            self.img4, (self.saved_x - x + 875, self.saved_y - y + 375)
        )

    def paint5(self, x, y):
        canvas.blit(
            self.img5, (self.saved_x - x + 875, self.saved_y - y + 375)
        )

    def f(self, x, y):
        canvas.blit(
            self.img_residual, (self.saved_x - x + 875, self.saved_y - y + 375)
        )

    def move_left(self, n):
        self.x -= n

    def move_right(self, n):
        self.x += n

    def move_up(self, n):
        self.y -= n

    def move_down(self, n):
        self.y += n

    def check_interact(self, px, py):
        """检查玩家是否在附近并按F键对话"""
        global player
        if sqrt((self.x - px) ** 2 + (self.y - py) ** 2) < 100:
            font_surface = font.render("F", True, "black")
            canvas.blit(font_surface, (self.x - px + 880, self.y - py + 375))
            keys = pygame.key.get_pressed()
            if keys[pygame.K_f]:
                while keys[pygame.K_f]:
                    event = pygame.event.poll()
                    keys = pygame.key.get_pressed()
                    if not keys[pygame.K_f]:
                        break
                # 显示对话
                canvas.blit(white, (20, 20))
                say(self.dialogue[0], 0)
                say(self.dialogue[1], 1)
                say(self.dialogue[2], 2)
                say(self.dialogue[3], 3)
                say(self.dialogue[4], 4)
                font_surface = font.render("X", True, "red")
                canvas.blit(font_surface, (1510, 160))
                pygame.display.update()
                while True:
                    pygame.time.Clock().tick(60)
                    event = pygame.event.poll()
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_x]:
                        while keys[pygame.K_x]:
                            event = pygame.event.poll()
                            keys = pygame.key.get_pressed()
                            if not keys[pygame.K_x]:
                                break
                        break


# ===================== 可拾取物品（纸条）类 =====================
class Note(BaseEntity):  # 原 Paper
    def __init__(
        self,
        x,
        y,
        text1,
        text2="",
        text3="",
        text4="",
        text5="",
        pickup_key=pygame.K_f,
        inventory_slot=0,
    ):
        self.x = x
        self.y = y
        self.linger_far = 0
        self.linger_mid = 0
        self.linger_close = 0
        self.text = (text1, text2, text3, text4, text5)  # 纸条内容
        self.pickup_key = pickup_key  # 原 k，拾取按键
        self.inventory_slot = (
            inventory_slot  # 原 fn，0表示在地上，>0表示在背包中的序号
        )
        # 图像
        self.img = paper
        self.img1 = paper1
        self.img2 = paper2
        self.img3 = paper3
        self.img4 = paper4
        self.img5 = paper5
        self.img_residual = p

    def paint(self, x, y):
        if not self.inventory_slot:
            canvas.blit(paper, (self.x - x + 875, self.y - y + 375))
        else:
            canvas.blit(paper, (self.inventory_slot * 30 + 1250, 50))

    def paint1(self, x, y):
        if not self.inventory_slot:
            canvas.blit(paper1, (self.x - x + 875, self.y - y + 375))
        else:
            canvas.blit(paper, (self.inventory_slot * 30 + 1250, 50))

    def paint2(self, x, y):
        if not self.inventory_slot:
            canvas.blit(paper2, (self.x - x + 875, self.y - y + 375))
        else:
            canvas.blit(paper, (self.inventory_slot * 30 + 1250, 50))

    def paint3(self, x, y):
        if not self.inventory_slot:
            canvas.blit(paper3, (self.x - x + 875, self.y - y + 375))
        else:
            canvas.blit(paper, (self.inventory_slot * 30 + 1250, 50))

    def paint4(self, x, y):
        if not self.inventory_slot:
            canvas.blit(paper4, (self.x - x + 875, self.y - y + 375))
        else:
            canvas.blit(paper, (self.inventory_slot * 30 + 1250, 50))

    def paint5(self, x, y):
        if not self.inventory_slot:
            canvas.blit(paper5, (self.x - x + 875, self.y - y + 375))
        else:
            canvas.blit(paper, (self.inventory_slot * 30 + 1250, 50))

    def f(self, x, y):
        if not self.inventory_slot:
            canvas.blit(p, (self.x - x + 875, self.y - y + 375))
        else:
            canvas.blit(paper, (self.inventory_slot * 30 + 1250, 50))
            self.linger_far += 1

    def check_interact(self, px, py):
        """拾取/丢弃/阅读纸条的交互"""
        global player
        if not self.inventory_slot:
            # 在地上的纸条
            if sqrt((self.x - px) ** 2 + (self.y - py) ** 2) < 100:
                font_surface = font.render("F", True, "white")
                canvas.blit(
                    font_surface, (self.x - px + 880, self.y - py + 375)
                )
            else:
                return
        else:
            # 在背包中，显示序号
            font_surface = font.render(str(self.inventory_slot), True, "white")
            canvas.blit(font_surface, (self.inventory_slot * 30 + 1255, 50))

        keys = pygame.key.get_pressed()
        if keys[self.pickup_key]:
            while keys[self.pickup_key]:
                event = pygame.event.poll()
                keys = pygame.key.get_pressed()
                if not keys[self.pickup_key]:
                    break
            # 显示纸条内容
            canvas.blit(white, (20, 20))
            say(self.text[0], 0)
            say(self.text[1], 1)
            say(self.text[2], 2)
            say(self.text[3], 3)
            say(self.text[4], 4)
            font_surface = font.render("Q:丢弃", True, "red")
            canvas.blit(font_surface, (1500, 150))
            font_surface = font.render("X:留下", True, "red")
            canvas.blit(font_surface, (1500, 175))
            pygame.display.update()
            while True:
                pygame.time.Clock().tick(60)
                event = pygame.event.poll()
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                keys = pygame.key.get_pressed()
                if keys[pygame.K_x]:
                    # 拾取到背包
                    if player.inventory_count < 9:
                        if not self.inventory_slot:
                            self.inventory_slot = player.inventory_count + 1
                            player.inventory_count += 1
                            player.inventory.append(self)
                            self.pickup_key = (
                                48 + self.inventory_slot
                            )  # 数字键
                        while keys[pygame.K_x]:
                            event = pygame.event.poll()
                            keys = pygame.key.get_pressed()
                            if not keys[pygame.K_x]:
                                break
                        break
                    else:
                        font_surface = font.render(
                            "无法拾起，请检查背包", True, "red"
                        )
                        canvas.blit(font_surface, (1500, 200))
                        pygame.display.update()
                if keys[pygame.K_q]:
                    # 丢弃
                    if self.inventory_slot:
                        player.inventory.pop(self.inventory_slot - 1)
                        player.inventory_count -= 1
                        self.inventory_slot = 0
                        self.pickup_key = pygame.K_f
                        self.x = player.x
                        self.y = player.y
                    while keys[pygame.K_q]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not keys[pygame.K_q]:
                            break
                    break


# ===================== 门（传送门）类 =====================
class Door(BaseEntity):
    def __init__(self, x, y, dest_x, dest_y, linked_door):
        self.x = x
        self.y = y
        self.dest_x = dest_x  # 原 xn
        self.dest_y = dest_y  # 原 yn
        self.linger_far = 0
        self.linger_mid = 0
        self.linger_close = 0
        self.open = True
        self.linked_door = linked_door  # 原 d，配对的门对象
        self.img = door
        self.img1 = door1
        self.img2 = door2
        self.img3 = door3
        self.img4 = door4
        self.img5 = door5
        self.img_residual = f

    def paint(self, x, y):
        if self.open:
            canvas.blit(door, (self.x - x + 875, self.y - y + 375))

    def paint1(self, x, y):
        if self.open:
            canvas.blit(door1, (self.x - x + 875, self.y - y + 375))

    def paint2(self, x, y):
        if self.open:
            canvas.blit(door2, (self.x - x + 875, self.y - y + 375))

    def paint3(self, x, y):
        if self.open:
            canvas.blit(door3, (self.x - x + 875, self.y - y + 375))

    def paint4(self, x, y):
        if self.open:
            canvas.blit(door4, (self.x - x + 875, self.y - y + 375))

    def paint5(self, x, y):
        if self.open:
            canvas.blit(door5, (self.x - x + 875, self.y - y + 375))

    def f(self, x, y):
        canvas.blit(f, (self.x - x + 875, self.y - y + 375))

    def check_interact(self, px, py):
        """开关门"""
        global player
        if sqrt((self.x - px) ** 2 + (self.y - py) ** 2) < 75:
            font_surface = font.render("F", True, "white")
            canvas.blit(font_surface, (self.x - px + 880, self.y - py + 375))
            keys = pygame.key.get_pressed()
            if keys[pygame.K_f]:
                while keys[pygame.K_f]:
                    pygame.event.poll()
                    keys = pygame.key.get_pressed()
                    if not keys[pygame.K_f]:
                        break
                self.open = not self.open
                self.linked_door.open = not self.linked_door.open


# ===================== 门的另一端（连接门）类 =====================
class LinkedDoor(BaseEntity):  # 原 D
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.linger_far = 0
        self.linger_mid = 0
        self.linger_close = 0
        self.open = True
        self.img = door
        self.img1 = door1
        self.img2 = door2
        self.img3 = door3
        self.img4 = door4
        self.img5 = door5
        self.img_residual = f

    def paint(self, x, y):
        if self.open:
            canvas.blit(door, (self.x - x + 875, self.y - y + 375))

    def paint1(self, x, y):
        if self.open:
            canvas.blit(door1, (self.x - x + 875, self.y - y + 375))

    def paint2(self, x, y):
        if self.open:
            canvas.blit(door2, (self.x - x + 875, self.y - y + 375))

    def paint3(self, x, y):
        if self.open:
            canvas.blit(door3, (self.x - x + 875, self.y - y + 375))

    def paint4(self, x, y):
        if self.open:
            canvas.blit(door4, (self.x - x + 875, self.y - y + 375))

    def paint5(self, x, y):
        if self.open:
            canvas.blit(door5, (self.x - x + 875, self.y - y + 375))

    def f(self, x, y):
        canvas.blit(f, (self.x - x + 875, self.y - y + 375))


# ===================== 地板、墙壁、岩石类（只用于绘制和碰撞） =====================
class Floor(BaseEntity):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.linger_far = 0
        self.linger_mid = 0
        self.linger_close = 0
        self.img = floor
        self.img1 = floor1
        self.img2 = floor2
        self.img3 = floor3
        self.img4 = floor4
        self.img5 = floor5
        self.img_residual = f


class Wall(BaseEntity):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.linger_far = 0
        self.linger_mid = 0
        self.linger_close = 0
        self.img = wall
        self.img1 = wall1
        self.img2 = wall2
        self.img3 = wall3
        self.img4 = wall4
        self.img5 = wall5
        self.img_residual = f


class Rock(BaseEntity):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.linger_far = 0
        self.linger_mid = 0
        self.linger_close = 0
        self.img = rock
        self.img1 = rock1
        self.img2 = rock2
        self.img3 = rock3
        self.img4 = rock4
        self.img5 = rock5
        self.img_residual = f


# ===================== 绘制函数 =====================
def draw_entity(entity):  # 原 paint(i)
    """根据实体与玩家的距离，选择不同细节等级绘制，并管理残留影子"""
    dist = sqrt((entity.x - player.x) ** 2 + (entity.y - player.y) ** 2)
    if dist < view_radius and entity.seen(player.x, player.y, seen_obstacles):
        if dist < view_radius / 6:
            entity.linger_close += 5
            entity.linger_mid += 5
        elif dist < view_radius * 2 / 3:
            entity.linger_mid += 10
            entity.linger_far += 5
        elif dist < view_radius:
            entity.linger_far += 10

        # 根据距离选择paint等级
        if dist < view_radius / 6:
            entity.paint(player.x, player.y)
        elif dist < view_radius * 5 / 24:
            entity.paint1(player.x, player.y)
        elif dist < view_radius * 2 / 3:
            entity.paint2(player.x, player.y)
        elif dist < view_radius:
            entity.paint3(player.x, player.y)
        elif entity.linger_close > 0:
            entity.paint4(player.x, player.y)
            entity.linger_close -= 1
        elif entity.linger_mid > 0:
            entity.paint5(player.x, player.y)
            entity.linger_mid -= 1
        elif entity.linger_far > 0:
            entity.f(player.x, player.y)
            entity.linger_far -= 1
    else:
        # 不在视野内时递减残留计时器
        if entity.linger_close > 0:
            entity.paint4(player.x, player.y)
            entity.linger_close -= 1
        elif entity.linger_mid > 0:
            entity.paint5(player.x, player.y)
            entity.linger_mid -= 1
        elif entity.linger_far > 0:
            entity.f(player.x, player.y)
            entity.linger_far -= 1


# ===================== 玩家实例 =====================
player = Player()


# ===================== 创建辅助函数 =====================
def createWall(x, y):
    walls.append(Wall(x, y))


def createRock(x, y):
    rocks.append(Rock(x, y))


def createFloor(x, y):
    floors.append(Floor(x, y))


def createNPC(x, y, s, s1="", s2="", s3="", s4=""):
    npcs.append(NPC(x, y, s, s1, s2, s3, s4))


def createPaper(x, y, s, s1="", s2="", s3="", s4="", k=pygame.K_f, fn=0):
    notes.append(Note(x, y, s, s1, s2, s3, s4, k, fn))


def createDoor(x, y, xn, yn, linked):
    doors.append(Door(x, y, xn, yn, linked))


def createLinkedDoor(x, y):
    """创建一个连接门并返回其对象，用于与Door配对"""
    linked_doors.append(LinkedDoor(x, y))
    return linked_doors[-1]


# ===================== 存档加载函数 =====================
def setup():
    """从savings.csjh读取游戏存档"""
    global skip_fall_check, game_state, walls, rocks, floors, npcs, notes, doors
    global npc_patrol_x, npc_patrol_y, sprint_mode, slow_mode, view_radius, linked_doors
    walls = []
    rocks = []
    floors = []
    npcs = []
    notes = []
    doors = []
    linked_doors = []
    with open("savings.csjh", encoding="utf-8") as f:
        view_radius = int(f.readline())
        skip_fall_check = int(f.readline())
        game_state = int(f.readline())
        player.x = int(f.readline())
        player.y = int(f.readline())
        player.vel_x = int(f.readline())
        player.vel_y = int(f.readline())
        player.speed = int(f.readline())
        player.inventory_count = int(f.readline())
        player.health = int(f.readline())
        player.stamina = int(f.readline())
        sprint_mode = bool(f.readline())
        slow_mode = bool(f.readline())
        npc_patrol_x = int(f.readline())
        npc_patrol_y = int(f.readline())

        # 读取地板
        x_list = f.readline().split()
        y_list = f.readline().split()
        for i in range(len(x_list)):
            createFloor(int(x_list[i]), int(y_list[i]))
        # 读取墙壁
        x_list = f.readline().split()
        y_list = f.readline().split()
        for i in range(len(x_list)):
            createWall(int(x_list[i]), int(y_list[i]))
        # 读取岩石
        x_list = f.readline().split()
        y_list = f.readline().split()
        for i in range(len(x_list)):
            createRock(int(x_list[i]), int(y_list[i]))
        # 读取NPC
        x_list = f.readline().split()
        y_list = f.readline().split()
        for i in range(len(x_list)):
            d1 = f.readline().strip()
            d2 = f.readline().strip()
            d3 = f.readline().strip()
            d4 = f.readline().strip()
            d5 = f.readline().strip()
            createNPC(int(x_list[i]), int(y_list[i]), d1, d2, d3, d4, d5)
        # 读取纸条
        x_list = f.readline().split()
        y_list = f.readline().split()
        slot_list = f.readline().split()
        for i in range(len(x_list)):
            t1 = f.readline().strip()
            t2 = f.readline().strip()
            t3 = f.readline().strip()
            t4 = f.readline().strip()
            t5 = f.readline().strip()
            createPaper(int(x_list[i]), int(y_list[i]), t1, t2, t3, t4, t5)
            slot = int(slot_list[i])
            if slot >= 0:
                player.inventory.append(notes[-1])
                notes[-1].inventory_slot = slot + 1
                notes[-1].pickup_key = 48 + slot + 1
                player.inventory_count += 1
        # 读取门和连接门
        x_list = f.readline().split()
        y_list = f.readline().split()
        xd_list = f.readline().split()
        yd_list = f.readline().split()
        for i in range(len(x_list)):
            dx = int(f.readline())
            dy = int(f.readline())
            ld = createLinkedDoor(int(xd_list[i]), int(yd_list[i]))
            createDoor(int(x_list[i]), int(y_list[i]), dx, dy, ld)


def save():
    """将游戏状态保存到savings.csjh"""
    with open("savings.csjh", "w", encoding="utf-8") as f:
        f.write(str(int(view_radius)) + "\n")
        f.write(str(int(skip_fall_check)) + "\n")
        f.write(str(int(game_state)) + "\n")
        f.write(str(int(player.x)) + "\n")
        f.write(str(int(player.y)) + "\n")
        f.write(str(int(player.vel_x)) + "\n")
        f.write(str(int(player.vel_y)) + "\n")
        f.write(str(int(player.speed)) + "\n")
        f.write(str(int(player.inventory_count)) + "\n")
        f.write(str(int(player.health)) + "\n")
        f.write(str(int(player.stamina)) + "\n")
        f.write(str(int(sprint_mode)) + "\n")
        f.write(str(int(slow_mode)) + "\n")
        f.write(str(int(npc_patrol_x)) + "\n")
        f.write(str(int(npc_patrol_y)) + "\n")

        # 地板坐标
        for fl in floors:
            f.write(str(fl.x) + " ")
        f.write("\n")
        for fl in floors:
            f.write(str(fl.y) + " ")
        f.write("\n")
        # 墙壁坐标
        for w in walls:
            f.write(str(w.x) + " ")
        f.write("\n")
        for w in walls:
            f.write(str(w.y) + " ")
        f.write("\n")
        # 岩石坐标
        for r in rocks:
            f.write(str(r.x) + " ")
        f.write("\n")
        for r in rocks:
            f.write(str(r.y) + " ")
        f.write("\n")
        # NPC坐标及对话
        for n in npcs:
            f.write(str(int(n.x)) + " ")
        f.write("\n")
        for n in npcs:
            f.write(str(int(n.y)) + " ")
        f.write("\n")
        for n in npcs:
            f.write(str(n.dialogue[0]))
            f.write(str(n.dialogue[1]))
            f.write(str(n.dialogue[2]))
            f.write(str(n.dialogue[3]))
            f.write(str(n.dialogue[4]))
        # 纸条坐标及背包状态
        for nt in notes:
            f.write(str(int(nt.x)) + " ")
        f.write("\n")
        for nt in notes:
            f.write(str(int(nt.y)) + " ")
        f.write("\n")
        for nt in notes:
            written = False
            for idx, item in enumerate(player.inventory):
                if item == nt:
                    f.write(str(idx) + " ")
                    written = True
                    break
            if not written:
                f.write("-1 ")
        f.write("\n")
        for nt in notes:
            f.write(str(nt.text[0]))
            f.write(str(nt.text[1]))
            f.write(str(nt.text[2]))
            f.write(str(nt.text[3]))
            f.write(str(nt.text[4]))
            f.write(str(int(nt.pickup_key)))
            f.write(str(nt.inventory_slot))
        f.write("\n")
        # 门坐标及配对
        for dr in doors:
            f.write(str(int(dr.x)) + " ")
        f.write("\n")
        for dr in doors:
            f.write(str(int(dr.y)) + " ")
        f.write("\n")
        for dr in doors:
            f.write(str(int(dr.linked_door.x)) + " ")
        f.write("\n")
        for dr in doors:
            f.write(str(int(dr.linked_door.y)) + " ")
        f.write("\n")
        for dr in doors:
            f.write(str(dr.dest_x))
            f.write(str(dr.dest_y))
        f.write("\n")


# ===================== 初始加载存档 =====================
setup()

# ===================== 主游戏循环 =====================
while True:
    pygame.time.Clock().tick(100)
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
        save()
        pygame.quit()
        break

    if game_state == 1:  # 正常游戏
        # 视野逐渐扩大
        if view_radius < 300:
            view_radius += view_radius / 50

        # NPC自动巡逻移动
        npc_patrol_x += 0.1
        npc_patrol_y -= 0.1
        if npc_patrol_x >= 10:
            npc_patrol_x = -10
        if npc_patrol_y <= -10:
            npc_patrol_y = 10

        canvas.fill((255, 255, 255))
        keys = pygame.key.get_pressed()

        # ESC菜单
        if keys[pygame.K_ESCAPE]:
            while keys[pygame.K_ESCAPE]:
                event = pygame.event.poll()
                keys = pygame.key.get_pressed()
                if not keys[pygame.K_ESCAPE]:
                    break
            # 绘制背景
            for i in range(40):
                for j in range(150):
                    canvas.blit(floor, (j * 20, i * 20))
                    if j % 15 == 0:
                        pygame.display.update()
            while True:
                event = pygame.event.poll()
                if event.type == pygame.QUIT:
                    save()
                    pygame.quit()
                    break
                keys = pygame.key.get_pressed()
                if keys[pygame.K_s]:  # 保存
                    while keys[pygame.K_s]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not keys[pygame.K_s]:
                            break
                    save()
                    canvas.fill((255, 255, 255))
                    pygame.display.update()
                    # 动画效果
                    for i in range(40):
                        for j in range(150):
                            canvas.blit(floor, ((150 - j) * 20, (40 - i) * 20))
                            if j % 15 == 0:
                                pygame.display.update()
                    break
                if keys[pygame.K_c]:  # 退出游戏
                    while keys[pygame.K_c]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not keys[pygame.K_c]:
                            break
                    save()
                    canvas.fill((255, 255, 255))
                    pygame.display.update()
                    for i in range(40):
                        for j in range(150):
                            canvas.blit(floor, ((150 - j) * 20, (40 - i) * 20))
                            if j % 15 == 0:
                                pygame.display.update()
                    pygame.quit()
                    break
                if keys[pygame.K_ESCAPE] or keys[pygame.K_x]:  # 返回游戏
                    while keys[pygame.K_ESCAPE] or keys[pygame.K_x]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not (keys[pygame.K_ESCAPE] or keys[pygame.K_x]):
                            break
                    break
                # 菜单界面
                for i in range(40):
                    for j in range(150):
                        canvas.blit(floor, (j * 20, i * 20))
                font_surface = pygame.font.Font(font_name, 50).render(
                    "S:保存游戏", True, (255, 0, 0)
                )
                canvas.blit(font_surface, (10, 7))
                font_surface = pygame.font.Font(font_name, 50).render(
                    "C:退出游戏", True, (255, 0, 0)
                )
                canvas.blit(font_surface, (10, 70))
                font_surface = pygame.font.Font(font_name, 50).render(
                    "X", True, (255, 0, 0)
                )
                canvas.blit(font_surface, (1700, 700))
                pygame.display.update()

        # 冲刺/慢走切换
        if sprint_mode and player.stamina:
            player.speed = 7
        else:
            player.speed = 4
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            if ctrl_toggle_mode:  # 切换模式
                while keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                    event = pygame.event.poll()
                    keys = pygame.key.get_pressed()
                    if not (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                        break
                sprint_mode = not sprint_mode
            else:
                sprint_mode = 1
        elif not ctrl_toggle_mode:
            sprint_mode = 0

        if keys[pygame.K_LALT] or keys[pygame.K_RALT]:
            if alt_toggle_mode:
                while keys[pygame.K_LALT] or keys[pygame.K_RALT]:
                    event = pygame.event.poll()
                    keys = pygame.key.get_pressed()
                    if not (keys[pygame.K_LALT] or keys[pygame.K_RALT]):
                        break
                slow_mode = not slow_mode
            else:
                slow_mode = 1
        elif not alt_toggle_mode:
            slow_mode = 0

        if slow_mode:
            player.vel_x = 0
            player.vel_y = 0
            player.speed = 2

        # 方向输入
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            player.move_left()
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            player.move_right()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            player.move_up()
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            player.move_down()
        if keys[pygame.K_r]:
            game_state = 3  # 重启

        # 绘制所有物体
        for fl in floors:
            draw_entity(fl)
        seen_obstacles = []
        for rk in rocks:
            draw_entity(rk)
            if sqrt(
                (rk.x - player.x) ** 2 + (rk.y - player.y) ** 2
            ) < view_radius and rk.seen(player.x, player.y, seen_obstacles):
                seen_obstacles.append(rk)
        for wl in walls:
            draw_entity(wl)
            if sqrt(
                (wl.x - player.x) ** 2 + (wl.y - player.y) ** 2
            ) < view_radius and wl.seen(player.x, player.y, seen_obstacles):
                seen_obstacles.append(wl)
        for dr in doors + linked_doors:
            draw_entity(dr)
            if (
                dr.open
                and sqrt((dr.x - player.x) ** 2 + (dr.y - player.y) ** 2)
                < view_radius
                and dr.seen(player.x, player.y, seen_obstacles)
            ):
                seen_obstacles.append(dr)
        for nt in notes:
            draw_entity(nt)
        for np in npcs:
            draw_entity(np)

        # NPC 移动（简单来回巡逻）
        npcs[0].move_right(abs(npc_patrol_x) - 5)
        npcs[0].move_up(abs(npc_patrol_y) - 5)

        # 玩家移动和碰撞
        player.move()
        player.resolve_collisions(walls + rocks + npcs)
        player.paint()

        # 显示坐标
        font_surface = font.render(
            "X:" + str(player.x) + ",Y=" + str(player.y), True, "red"
        )
        canvas.blit(font_surface, (20, 20))

        # 交互检查
        for nt in notes:
            nt.check_interact(player.x, player.y)
        for np in npcs:
            np.check_interact(player.x, player.y)
        for dr in doors:
            dr.check_interact(player.x, player.y)

        pygame.display.update()

    elif game_state == 2:  # 游戏结束
        font_surface = bigFont.render("Game over", True, "red")
        canvas.blit(font_surface, (250, 30))
        font_surface = font.render("'c' for exit", True, "red")
        canvas.blit(font_surface, (800, 450))
        font_surface = font.render("'r' for again", True, "red")
        canvas.blit(font_surface, (800, 550))
        pygame.display.update()
        event = pygame.event.poll()
        if event.type == pygame.QUIT:
            pygame.quit()
            break
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            game_state = 3
        if keys[pygame.K_c]:
            pygame.quit()
            break

    elif game_state == 3:  # 重启游戏
        player = Player()
        game_state = 1
        view_radius = 0
        setup()
