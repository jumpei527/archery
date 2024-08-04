import pygame
import random
import math

# 初期設定
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("弓矢の的あてゲーム")

# 色設定
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# フォント設定
font = pygame.font.SysFont(None, 36)

# 画像読み込み
target_image = pygame.image.load("target.png")
target_image = pygame.transform.scale(target_image, (250, 250))
speed_images = [
    pygame.image.load("speed_1.png"),
    pygame.image.load("speed_2.png"),
    pygame.image.load("speed_3.png")
]
speed_images = [pygame.transform.scale(img, (WIDTH, HEIGHT)) for img in speed_images]
arrow_image = pygame.image.load("arrow.png")

# 矢のパラメータ（画面サイズに対する比率で指定）
ARROW_WIDTH_RATIO = 0.375  # 画面幅の37.5%
ARROW_HEIGHT_RATIO = 0.333  # 画面高さの33.3%
ARROW_ANGLE = 45  # 矢の回転角度（度数法）

# 矢の画像を調整する関数
def adjust_arrow(width_ratio, height_ratio, angle):
    global arrow_image, ARROW_WIDTH, ARROW_HEIGHT
    ARROW_WIDTH = int(WIDTH * width_ratio)
    ARROW_HEIGHT = int(HEIGHT * height_ratio)
    arrow_image = pygame.image.load("arrow.png")
    arrow_image = pygame.transform.scale(arrow_image, (ARROW_WIDTH, ARROW_HEIGHT))
    arrow_image = pygame.transform.rotate(arrow_image, angle)

# 初期の矢の調整
adjust_arrow(ARROW_WIDTH_RATIO, ARROW_HEIGHT_RATIO, ARROW_ANGLE)

# 的の設定
target_rect = target_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
target_radius = target_rect.width // 2

# 得点範囲の半径
r = target_radius
score_ranges = {
    10: 0.86 * r / 5,
    7: 1.9 * r / 5,
    5: 2.95 * r / 5,
    3: 3.96 * r / 5,
    1: r
}

# ゲーム状態
initial_aim_radius = 250
aim_radius = initial_aim_radius
aim_shrink_rate = 0.5
min_aim_radius = 20
score = 0
hit_pos = None
game_over = False
animation_running = False
animation_start_time = 0
ANIMATION_DURATION = 3000  # 3秒間
FADE_OUT_DURATION = 500  # フェードアウトの時間（ミリ秒）
SPEED_IMAGE_DURATION = 100  # 各速度画像の表示時間（ミリ秒）

# 照準の揺れに関する変数
sway_radius = 30
aim_center_x, aim_center_y = target_rect.center
aim_target_x, aim_target_y = target_rect.center
sway_speed = 2

def calculate_score(hit_pos):
    distance = math.hypot(hit_pos[0] - target_rect.centerx, hit_pos[1] - target_rect.centery)
    for points, radius in score_ranges.items():
        if distance <= radius:
            return points
    return 0

def get_random_point_in_circle(center, radius):
    angle = random.uniform(0, 2 * math.pi)
    r = radius * math.sqrt(random.uniform(0, 1))
    x = center[0] + r * math.cos(angle)
    y = center[1] + r * math.sin(angle)
    return (int(x), int(y))

def update_aim_position():
    global aim_center_x, aim_center_y, aim_target_x, aim_target_y
    
    if math.hypot(aim_center_x - aim_target_x, aim_center_y - aim_target_y) < 1:
        aim_target_x, aim_target_y = get_random_point_in_circle(target_rect.center, sway_radius)
    
    dx = aim_target_x - aim_center_x
    dy = aim_target_y - aim_center_y
    distance = math.hypot(dx, dy)
    
    if distance > 0:
        aim_center_x += (dx / distance) * sway_speed
        aim_center_y += (dy / distance) * sway_speed

def draw_arrow_animation(progress):
    if progress < (ANIMATION_DURATION - FADE_OUT_DURATION) / ANIMATION_DURATION:
        # 通常のアニメーション
        alpha = 255
        # 速度画像のローテーション
        speed_image_index = int((progress * ANIMATION_DURATION) / SPEED_IMAGE_DURATION) % len(speed_images)
        speed_image = speed_images[speed_image_index]
    else:
        # フェードアウト
        fade_progress = (progress * ANIMATION_DURATION - (ANIMATION_DURATION - FADE_OUT_DURATION)) / FADE_OUT_DURATION
        alpha = int(255 * (1 - fade_progress))
        speed_image = speed_images[-1]  # フェードアウト中は最後の画像を使用

    # speed_imageのアルファ値を変更
    speed_image_copy = speed_image.copy()
    speed_image_copy.set_alpha(alpha)
    screen.blit(speed_image_copy, (0, 0))
    
    # 矢のアルファ値を変更
    arrow_copy = arrow_image.copy()
    arrow_copy.set_alpha(alpha)
    
    # 矢を中央に配置
    arrow_x = WIDTH // 2 - arrow_copy.get_width() // 2
    arrow_y = HEIGHT // 2 - arrow_copy.get_height() // 2
    screen.blit(arrow_copy, (arrow_x, arrow_y))

    # 背景を徐々に白くする
    white_overlay = pygame.Surface((WIDTH, HEIGHT))
    white_overlay.fill(WHITE)
    white_overlay.set_alpha(255 - alpha)
    screen.blit(white_overlay, (0, 0))

clock = pygame.time.Clock()

while True:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over and not animation_running:
                hit_pos = get_random_point_in_circle((aim_center_x, aim_center_y), aim_radius)
                score = calculate_score(hit_pos)
                animation_running = True
                animation_start_time = current_time
            # 矢のパラメータを調整するキー
            elif event.key == pygame.K_w:
                ARROW_HEIGHT_RATIO = min(1.0, ARROW_HEIGHT_RATIO + 0.01)
            elif event.key == pygame.K_s:
                ARROW_HEIGHT_RATIO = max(0.1, ARROW_HEIGHT_RATIO - 0.01)
            elif event.key == pygame.K_a:
                ARROW_WIDTH_RATIO = max(0.1, ARROW_WIDTH_RATIO - 0.01)
            elif event.key == pygame.K_d:
                ARROW_WIDTH_RATIO = min(1.0, ARROW_WIDTH_RATIO + 0.01)
            elif event.key == pygame.K_q:
                ARROW_ANGLE = (ARROW_ANGLE + 15) % 360
            elif event.key == pygame.K_e:
                ARROW_ANGLE = (ARROW_ANGLE - 15) % 360
            
            # 矢の調整を適用
            adjust_arrow(ARROW_WIDTH_RATIO, ARROW_HEIGHT_RATIO, ARROW_ANGLE)

    screen.fill(WHITE)

    if animation_running:
        animation_progress = (current_time - animation_start_time) / ANIMATION_DURATION
        if animation_progress >= 1:
            animation_running = False
            game_over = True
        else:
            draw_arrow_animation(animation_progress)
    else:
        # 的の描画
        screen.blit(target_image, target_rect)

        # 照準の位置更新と描画
        if aim_radius > 0 and not game_over:
            update_aim_position()
            pygame.draw.circle(screen, BLACK, (int(aim_center_x), int(aim_center_y)), int(aim_radius), 2)

        # 当たった点の描画
        if hit_pos and game_over:
            pygame.draw.circle(screen, BLUE, hit_pos, 5)

        # スコアの表示
        score_text = font.render(f'Score: {score}', True, BLACK)
        screen.blit(score_text, (10, 10))

        # 照準の縮小（最小サイズの制限付き）
        if aim_radius > min_aim_radius and not game_over:
            aim_radius = max(aim_radius - aim_shrink_rate, min_aim_radius)

    pygame.display.flip()
    clock.tick(60)  # 60FPSに制限