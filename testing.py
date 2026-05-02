# -*- coding: utf-8 -*-
"""
厕所惊魂 - 主菜单/启动界面
功能：
  1. 圆形视野扩散动画
  2. 提供读取存档、新建存档、游戏设置、退出等功能
  3. 管理 settings.csjh 配置文件（声音、Ctrl/Alt 操作模式）
  4. 当读取存档时，退出本界面并载入主游戏模块（test.py）
"""

import pygame
from math import sqrt

# ===================== Pygame 初始化 =====================
pygame.init()
canvas = pygame.display.set_mode((1000, 500))
font_name = pygame.font.match_font('KaiTi')
pygame.display.set_caption("厕所惊魂")
button_rect = pygame.Rect(10, 100, 40, 20)  # 按钮的矩形区域
button_color = (255, 255, 255)  # 按钮的颜色（RGB值）
text_color = (0, 0, 0)  # 文本的颜色（RGB值）
button_font = pygame.font.Font('arial.ttf', 11)  # 文本使用的字体和字号
button_text = button_font.render("Button", True, text_color)  # 渲染文本

# ===================== 图像加载函数 =====================
def loadPng(name):
    """加载 images/ 目录下的 PNG 图片"""
    return pygame.image.load('images/' + name + '.png')

# 预加载所需图像
air = loadPng('air')
p = loadPng('p')
floor_img = loadPng('floor')   # 原变量 floor，为避免与类名冲突改为 floor_img

# ===================== 读取设置文件 =====================
with open('settings.csjh', encoding='utf-8') as f:
    sound_enabled = int(f.readline())   # 原 sound，声音开关（1 开 / 0 关）
    ctrl_toggle_mode = int(f.readline())# 原 ctrl，1 为点击切换疾跑，0 为按住疾跑
    alt_toggle_mode = int(f.readline()) # 原 alt，1 为点击切换潜行，0 为按住潜行

# ===================== 地板类（用于背景绘制） =====================
class Floor:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def paint(self):
        """在绝对坐标处绘制地板图块"""
        canvas.blit(floor_img, (self.x, self.y))

# ===================== 地板生成 =====================
canvas.fill((255, 255, 255))
floors = []

def createFloor(x, y):
    floors.append(Floor(x, y))

def setup():
    """生成覆盖窗口的地板网格"""
    global walls  # 原代码有这行，但菜单中未使用 walls，保留以防兼容性
    walls = []
    for i in range(0, 1020, 20):
        for j in range(0, 520, 20):
            createFloor(i, j)

setup()

# ===================== 动画控制变量 =====================
circle_radius = 5          # 原 x，视野圆圈半径，逐渐增大
font_size_scale = 1        # 原 y，字体大小缩放因子，逐渐增大

# ===================== 主循环 =====================
while True:
    pygame.time.Clock().tick(100)
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
        # 退出时保存设置
        with open('settings.csjh', 'w', encoding='utf-8') as f:
            f.write(str(int(sound_enabled)) + '\n')
            f.write(str(int(ctrl_toggle_mode)) + '\n')
            f.write(str(int(alt_toggle_mode)) + '\n')
        pygame.quit()
        break

    canvas.fill((100, 100, 100))  # 背景灰色

    # 绘制视野范围内的地板（形成圆形扩散效果）
    for floor_tile in floors:
        if sqrt((floor_tile.x - 500) ** 2 + (floor_tile.y - 250) ** 2) < circle_radius * 2:
            floor_tile.paint()

    # 当视野半径足够大时显示主菜单
    if circle_radius > 350:
        # 字体大小渐变
        if font_size_scale < 50:
            font_size_scale += 0.5

        keys = pygame.key.get_pressed()
        # 根据缩放因子创建两种大小的字体
        current_font = pygame.font.Font(font_name, int(font_size_scale))
        big_font = pygame.font.Font(font_name, int(font_size_scale * 4))

        # -------------------- 读取存档 --------------------
        if keys[pygame.K_r] and font_size_scale >= 50:
            try:
                # 检查存档文件是否存在
                with open('savings.csjh', encoding='utf-8') as f:
                    content = f.read()
                # 存档存在，播放退出动画并跳转主游戏
                while True:
                    pygame.time.Clock().tick(20)
                    if circle_radius < 0:
                        break
                    if circle_radius < 15:
                        canvas.blit(p, (500, 250))
                    pygame.event.poll()
                    canvas.fill((100 + (350 - circle_radius) * 0.4,
                                 100 + (350 - circle_radius) * 0.4,
                                 100 + (350 - circle_radius) * 0.4))
                    for floor_tile in floors:
                        if sqrt((floor_tile.x - 500) ** 2 + (floor_tile.y - 250) ** 2) < circle_radius * 2:
                            floor_tile.paint()
                    circle_radius -= 5
                    pygame.display.update()
                canvas.blit(p, (500, 250))
                pygame.display.update()
                pygame.quit()
                import test   # 载入主游戏模块
                break
            except FileNotFoundError:
                # 没有存档
                font = pygame.font.Font(font_name, 200)
                font_surface = font.render('你没有存档', True, (255, 0, 0))
                canvas.blit(font_surface, (0, 100))
                font = pygame.font.Font(font_name, 50)
                font_surface = font.render('X', True, (255, 0, 0))
                canvas.blit(font_surface, (900, 400))
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

        # -------------------- 新建/重建存档 --------------------
        elif keys[pygame.K_n] and font_size_scale >= 50:
            while keys[pygame.K_n]:
                event = pygame.event.poll()
                keys = pygame.key.get_pressed()
                if not keys[pygame.K_n]:
                    break
            # 确认界面
            font = pygame.font.Font(font_name, 75)
            font_surface = font.render('确定吗？现有存档将被覆盖！', True, (255, 0, 0))
            canvas.blit(font_surface, (0, 100))
            font = pygame.font.Font(font_name, 50)
            font_surface = font.render('Y:确定', True, (255, 0, 0))
            canvas.blit(font_surface, (200, 200))
            font_surface = font.render('N:取消', True, (255, 0, 0))
            canvas.blit(font_surface, (600, 200))
            font_surface = font.render('X', True, (255, 0, 0))
            canvas.blit(font_surface, (900, 400))
            pygame.display.update()
            while True:
                pygame.time.Clock().tick(60)
                event = pygame.event.poll()
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                keys = pygame.key.get_pressed()
                if keys[pygame.K_x]:   # 取消
                    while keys[pygame.K_x]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not keys[pygame.K_x]:
                            break
                    break
                if keys[pygame.K_n]:   # 取消
                    while keys[pygame.K_n]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not keys[pygame.K_n]:
                            break
                    break
                if keys[pygame.K_y]:   # 确认新建
                    while keys[pygame.K_y]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not keys[pygame.K_y]:
                            break
                    # 写入初始存档
                    with open('savings.csjh', 'w', encoding='utf-8') as f:
                        f.write('10\n')           # 视野半径
                        f.write('1\n1\n')         # skip_fall_check, game_state
                        f.write('500\n100\n0\n0\n3\n0\n10000\n1000\n')  # 玩家数据
                        f.write('0\n0\n')         # sprint_mode, slow_mode
                        f.write('0\n5\n')         # npc_patrol_x, npc_patrol_y

                        # 地板坐标（20~2000）
                        for i in range(20, 2020, 20):
                            for j in range(20, 2020, 20):
                                f.write(str(i) + ' ')
                        f.write('\n')
                        for i in range(20, 2020, 20):
                            for j in range(20, 2020, 20):
                                f.write(str(j) + ' ')
                        f.write('\n')

                        # 墙壁坐标（外边框）
                        for i in range(0, 2040, 20):
                            f.write(str(i) + ' ')  # 上边
                            f.write(str(i) + ' ')  # 下边
                        for j in range(20, 2020, 20):
                            f.write('0 ')          # 左边
                            f.write('2020 ')       # 右边
                            if j != 500 and j != 520:
                                f.write('1000 ')   # 中间墙（留门洞）
                        f.write('\n')
                        for i in range(0, 2040, 20):
                            f.write('0 ')          # y 坐标对应上边
                            f.write('2020 ')       # y 坐标对应下边
                        for j in range(20, 2020, 20):
                            f.write(str(j) + ' ')  # y 坐标对应左边
                            f.write(str(j) + ' ')  # y 坐标对应右边
                            if j != 500 and j != 520:
                                f.write(str(j) + ' ') # 中间墙 y 坐标
                        f.write('\n')

                        # 岩石坐标（这里为空）
                        f.write('\n')
                        f.write('\n')

                        # NPC 坐标及对话
                        f.write('500\n')
                        f.write('500\n')
                        f.write('1500\n')
                        f.write('1000\n')
                        f.write('非常感谢您参与测试！（高兴地转圈圈）\n')
                        f.write('有什么问题可以艾特或者私信阿布说哦~他人很好哒\n')
                        f.write('阿布的QQ号是19999021，手机号是15601902159\n')
                        f.write('在此向你献上最美好的祝福！\n')
                        f.write('————阿布的朋友\n')

                        # 纸条坐标及内容
                        f.write('500\n')
                        f.write('1000\n')
                        f.write('-1\n')
                        f.write('非常感谢您参与《厕所惊魂》的开发测试！\n')
                        f.write('有什么问题可以艾特或者私信我说哈\n')
                        f.write('我的QQ号是19999021哈\n')
                        f.write('在此向你献上最美好的祝福！\n')
                        f.write('————阿布\n')
                        f.write(str(pygame.K_f) + '\n')  # 拾取键
                        f.write('0\n')                   # 背包槽位

                        # 门坐标及配对
                        f.write('1000\n')
                        f.write('500\n')
                        f.write('1000\n')
                        f.write('520\n')
                        f.write('1\n')   # 目标 x
                        f.write('2\n')   # 目标 y
                    break

        # -------------------- 设置 --------------------
        elif keys[pygame.K_s] and font_size_scale >= 50:
            while keys[pygame.K_s]:
                event = pygame.event.poll()
                keys = pygame.key.get_pressed()
                if not keys[pygame.K_s]:
                    break
            # 绘制设置界面框架
            font = pygame.font.Font(font_name, 75)
            font_surface = font.render('S:声音' + ('开' if sound_enabled else '关'), True, (255, 0, 0))
            canvas.blit(font_surface, (0, 0))
            font_surface = font.render('C:' + ('点击' if ctrl_toggle_mode else '按住') + '疾跑', True, (255, 0, 0))
            canvas.blit(font_surface, (0, 100))
            font_surface = font.render('A:' + ('点击' if alt_toggle_mode else '按住') + '潜行', True, (255, 0, 0))
            canvas.blit(font_surface, (0, 200))
            # 占位空白
            font_surface = font.render('', True, (255, 0, 0))
            canvas.blit(font_surface, (0, 300))
            canvas.blit(font_surface, (500, 0))
            canvas.blit(font_surface, (500, 100))
            canvas.blit(font_surface, (500, 200))
            canvas.blit(font_surface, (500, 300))
            font = pygame.font.Font(font_name, 50)
            font_surface = font.render('X', True, (255, 0, 0))
            canvas.blit(font_surface, (900, 400))
            pygame.display.update()

            font = pygame.font.Font(font_name, 75)
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
                    # 保存设置并退出设置界面
                    with open('settings.csjh', 'w', encoding='utf-8') as f:
                        f.write(str(int(sound_enabled)) + '\n')
                        f.write(str(int(ctrl_toggle_mode)) + '\n')
                        f.write(str(int(alt_toggle_mode)) + '\n')
                    break
                if keys[pygame.K_s]:
                    while keys[pygame.K_s]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not keys[pygame.K_s]:
                            break
                    sound_enabled = not sound_enabled
                    # 刷新声音选项显示
                    for tile in floors:
                        if 0 <= tile.x < 500 and 0 <= tile.y < 100:
                            tile.paint()
                    font_surface = font.render('S:声音' + ('开' if sound_enabled else '关'), True, (255, 0, 0))
                    canvas.blit(font_surface, (0, 0))
                    pygame.display.update()
                if keys[pygame.K_c]:
                    while keys[pygame.K_c]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not keys[pygame.K_c]:
                            break
                    ctrl_toggle_mode = not ctrl_toggle_mode
                    for tile in floors:
                        if 0 <= tile.x < 500 and 100 <= tile.y < 200:
                            tile.paint()
                    font_surface = font.render('C:' + ('点击' if ctrl_toggle_mode else '按住') + '疾跑', True, (255, 0, 0))
                    canvas.blit(font_surface, (0, 100))
                    pygame.display.update()
                if keys[pygame.K_a]:
                    while keys[pygame.K_a]:
                        event = pygame.event.poll()
                        keys = pygame.key.get_pressed()
                        if not keys[pygame.K_a]:
                            break
                    alt_toggle_mode = not alt_toggle_mode
                    for tile in floors:
                        if 0 <= tile.x < 500 and tile.y > 200 and tile.y < 300:
                            tile.paint()
                    font_surface = font.render('A:' + ('点击' if alt_toggle_mode else '按住') + '潜行', True, (255, 0, 0))
                    canvas.blit(font_surface, (0, 200))
                    pygame.display.update()

        # -------------------- 退出 --------------------
        elif keys[pygame.K_c] and font_size_scale >= 50:
            pygame.quit()
            break

        # -------------------- 主菜单文字 --------------------
        else:
            # 根据是否有存档显示不同的文字
            font_surface = current_font.render('R:读取存档', True, (font_size_scale * 3, 0, 0))
            canvas.blit(font_surface, (10, font_size_scale / 5))
            try:
                with open('savings.csjh', encoding='utf-8') as f:
                    f.read()
                font_surface = current_font.render('N:重建存档', True, (font_size_scale * 3, 0, 0))
                canvas.blit(font_surface, (10, font_size_scale * 1.5))
            except FileNotFoundError:
                font_surface = current_font.render('N:新建存档', True, (font_size_scale * 3, 0, 0))
                canvas.blit(font_surface, (10, font_size_scale * 1.5))
            font_surface = current_font.render('S:设置', True, (font_size_scale * 3, 0, 0))
            canvas.blit(font_surface, (10, font_size_scale * 2.8))
            font_surface = current_font.render('C:退出', True, (font_size_scale * 3, 0, 0))
            canvas.blit(font_surface, (10, font_size_scale * 4.1))
            # 游戏标题
            font_surface = big_font.render('厕所', True, (font_size_scale * 2, 0, 0))
            canvas.blit(font_surface, (300, font_size_scale * 5 - 220))
            font_surface = big_font.render('惊魂', True, (font_size_scale * 2, 0, 0))
            canvas.blit(font_surface, (500, font_size_scale * 5 - 20))
            font_surface = current_font.render('Powered by Gorabbit', True, (font_size_scale, font_size_scale, font_size_scale))
            canvas.blit(font_surface, (500, font_size_scale * 9))

    else:
        # 视野半径未达到350时，不断增大（扩散动画）
        circle_radius += circle_radius / 100

    pygame.draw.rect(canvas, button_color, button_rect)
    canvas.blit(button_text, (button_rect.centerx - button_text.get_width() // 2,
                              button_rect.centery - button_text.get_height() // 2))

    pygame.display.update()