import pygame
import random
import math
import time
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations

current_ratio = 0
stop_flag = False

class measure():
    def __init__(self) -> None:
        pass
    
    def calcurate():
        global current_ratio, stop_flag
        
        # OpenBCI Ganglionボードの設定
        params = BrainFlowInputParams()
        params.serial_port = 'COM5'  # シリアルポートを指定

        # ボードIDを指定してセッションを準備
        board = BoardShim(BoardIds.GANGLION_BOARD, params)
        board.prepare_session()

        # サンプリングレートを取得
        sampling_rate = BoardShim.get_sampling_rate(BoardIds.GANGLION_BOARD)   # sampling_late = 200

        # EEGチャネルを取得
        eeg_channels = BoardShim.get_eeg_channels(BoardIds.GANGLION_BOARD)

        # リアルタイムプロットのセットアップ
        fig, ax = plt.subplots(3, 1, sharex=True)
        xdata, alpha_ydata, beta_ydata, ratio_ydata = [], [], [], []
        alpha_ln, = ax[0].plot([], [], 'b-', animated=True, label='Alpha')
        beta_ln, = ax[1].plot([], [], 'r-', animated=True, label='Beta')
        ratio_ln, = ax[2].plot([], [], 'g-', animated=True, label='ratio')

        window_size = 5  # 移動平均のウィンドウサイズ

        # エネルギーとその比率を表示するテキスト要素
        alpha_energy_text = ax[0].text(0.02, 0.95, '', transform=ax[0].transAxes)
        beta_energy_text = ax[1].text(0.02, 0.95, '', transform=ax[1].transAxes)
        ratio_text = ax[2].text(0.02, 0.95, '', transform=ax[2].transAxes)

        def moving_average(data, window_size):
            return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

        def hard_threshold(data, threshold):
            return np.where(np.abs(data) > threshold, 0, data)

        def calculate_energy(data):
            return np.mean(data ** 2)

        def init():
            for a in ax:
                a.set_xlim(0, 50)  # 50秒間のデータを表示
                if a==ax[0] or a==ax[1]:
                    a.set_ylim(-100, 100)  # α波とβ波の値の範囲を設定
                else:
                    a.set_ylim(0, 5)  # 比率の値の範囲を設定
                a.legend(loc='upper right')  
            return alpha_ln, beta_ln, alpha_energy_text, beta_energy_text, ratio_text

        def update(frame):
            global current_ratio
            data = board.get_current_board_data(sampling_rate)  # 最新のデータを取得
            alpha_data, beta_data = [], []
            
            for channel in eeg_channels[:3]:  # 3チャネルのみを使用
                DataFilter.detrend(data[channel], DetrendOperations.LINEAR.value)
                
                # アルファ波の抽出
                alpha_channel_data = data[channel].copy()
                DataFilter.perform_bandpass(alpha_channel_data, sampling_rate, 8.0, 13.0, 2, FilterTypes.BUTTERWORTH_ZERO_PHASE.value, 0)
                alpha_channel_data = hard_threshold(alpha_channel_data, 150)
                alpha_data.append(alpha_channel_data)
                
                # ベータ波の抽出
                beta_channel_data = data[channel].copy()
                DataFilter.perform_bandpass(beta_channel_data, sampling_rate, 13.0, 30.0, 2, FilterTypes.BUTTERWORTH_ZERO_PHASE.value, 0)
                beta_channel_data = hard_threshold(beta_channel_data, 150)
                beta_data.append(beta_channel_data)
                
            alpha_mean = np.mean(alpha_data, axis=0)
            beta_mean = np.mean(beta_data, axis=0)
            
            # エネルギーの計算
            alpha_energy = calculate_energy(alpha_mean)
            beta_energy = calculate_energy(beta_mean)
            ratio = beta_energy / alpha_energy if alpha_energy != 0 else 0
            current_ratio =  ratio
            
            # テキスト要素の更新
            alpha_energy_text.set_text(f'Alpha Energy: {alpha_energy:.2f} µV²')
            beta_energy_text.set_text(f'Beta Energy: {beta_energy:.2f} µV²')
            ratio_text.set_text(f'Beta/Alpha Ratio: {ratio:.2f}')
            
            current_time = time.time() % 50  # 時間を100秒間隔でループ
            
            xdata.append(current_time)
            alpha_ydata.append(alpha_mean[0])
            beta_ydata.append(beta_mean[0])
            ratio_ydata.append(ratio)
            
            if len(xdata) > 1 and xdata[-1] < xdata[-2]:  # 100秒を超えた場合
                xdata.clear()
                alpha_ydata.clear()
                beta_ydata.clear()
                ratio_ydata.clear()
                xdata.append(current_time)
                alpha_ydata.append(alpha_mean[0])
                beta_ydata.append(beta_mean[0])
                ratio_ydata.append(ratio)
                
            if len(alpha_ydata) > window_size:
                smoothed_alpha_ydata = moving_average(alpha_ydata, window_size)
                smoothed_beta_ydata = moving_average(beta_ydata, window_size)
                smoothed_ratio_ydata = moving_average(ratio_ydata, window_size)
                
                alpha_ln.set_data(xdata[-len(smoothed_alpha_ydata):], smoothed_alpha_ydata)
                beta_ln.set_data(xdata[-len(smoothed_beta_ydata):], smoothed_beta_ydata)
                ratio_ln.set_data(xdata[-len(smoothed_ratio_ydata):], smoothed_ratio_ydata)
            else:
                alpha_ln.set_data(xdata, alpha_ydata)
                beta_ln.set_data(xdata, beta_ydata)
                ratio_ln.set_data(xdata, ratio_ydata)
                
            return alpha_ln, beta_ln, ratio_ln, alpha_energy_text, beta_energy_text, ratio_text
        # リアルタイムプロットのアニメーション
        ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=30)  # 30ミリ秒ごとに更新

        # ボードからストリーミングを開始
        board.start_stream()

        # プロットを表示
        plt.show()

        # ストリーミングを停止してセッションを終了
        board.stop_stream()
        board.release_session()

# 初期設定
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("弓矢の的あてゲーム")
# フルスクリーン
# info = pygame.display.Info()
# WIDTH, HEIGHT = info.current_w, info.current_h
# screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
# pygame.display.set_caption("弓矢の的あてゲーム")

# 色設定
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# フォント設定
font = pygame.font.Font("azukiLB.ttf", 50)

# 画像読み込み
title_image = pygame.image.load("title.png")
title_image = pygame.transform.scale(title_image, (WIDTH, HEIGHT))
background_image = pygame.image.load("background.png")
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
canvas_image = pygame.image.load("canvas.png")

# canvas_imageのサイズ設定（画面幅と高さの比率で設定）
CANVAS_WIDTH_RATIO = 0.25
CANVAS_HEIGHT_RATIO = 0.2
CANVAS_WIDTH = int(WIDTH * CANVAS_WIDTH_RATIO)
CANVAS_HEIGHT = int(HEIGHT * CANVAS_HEIGHT_RATIO)
canvas_image = pygame.transform.scale(canvas_image, (CANVAS_WIDTH, CANVAS_HEIGHT))
result_image = pygame.image.load("result.png")
result_image = pygame.transform.scale(result_image, (WIDTH, HEIGHT))

# canvas_imageの位置設定（画面中央）
canvas_rect = canvas_image.get_rect(center=(WIDTH // 2, 3 * HEIGHT // 4))

target_image = pygame.image.load("target.png")
target_image = pygame.transform.scale(target_image, (250, 250))
speed_images = [
    pygame.image.load("speed_1.png"),
    pygame.image.load("speed_2.png"),
    pygame.image.load("speed_3.png")
]
speed_images = [pygame.transform.scale(img, (WIDTH, HEIGHT)) for img in speed_images]
arrow_image_1 = pygame.image.load("arrow_1.png")
arrow_image_2 = pygame.image.load("arrow_2.png")

# 矢のパラメータ（画面サイズに対する比率で指定）
ARROW_WIDTH_RATIO = 0.5
ARROW_HEIGHT_RATIO = 0.5
ARROW_ANGLE = 45  # 矢の回転角度（度数法）

# 矢の画像を調整する関数
def adjust_arrow(width_ratio, height_ratio, angle):
    global arrow_image_1, arrow_image_2, ARROW_WIDTH, ARROW_HEIGHT
    ARROW_WIDTH = int(WIDTH * width_ratio)
    ARROW_HEIGHT = int(HEIGHT * height_ratio)
    arrow_image_1 = pygame.image.load("arrow_1.png")
    arrow_image_1 = pygame.transform.scale(arrow_image_1, (ARROW_WIDTH, ARROW_HEIGHT))
    arrow_image_1 = pygame.transform.rotate(arrow_image_1, angle)
    arrow_image_2 = pygame.image.load("arrow_2.png")
    arrow_image_2 = pygame.transform.scale(arrow_image_2, (ARROW_WIDTH, ARROW_HEIGHT))
    arrow_image_2 = pygame.transform.rotate(arrow_image_2, 48)

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
min_aim_radius = 50
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

# ゲーム状態の定数を追加
START_SCREEN = 0
PLAYING = 1
RESULT_SCREEN = 2
FINAL_RESULT_SCREEN = 3

# グローバル変数を追加
game_state = START_SCREEN
game_count = 0
total_score = 0
scores = []

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
    global aim_center_x, aim_center_y, aim_target_x, aim_target_y, current_ratio
    
    sway_radius = 30 + 20*current_ratio
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
    if progress < 0.5:
        arrow_copy = arrow_image_1.copy()
    else:
        arrow_copy = arrow_image_2.copy()
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

def draw_start_screen():
    screen.blit(title_image, (0, 0))

def draw_result_screen():
    screen.blit(result_image, (0, 0))
    score_text = font.render(f'得点: {score}点', True, BLACK)
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    instruction_text = font.render('スペースキーを押して再開', True, BLACK)
    screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT // 2 + 50))

# メインループ内で使用する関数を追加
def reset_game():
    global aim_radius, score, game_over, animation_running
    aim_radius = initial_aim_radius
    score = 0
    game_over = False
    animation_running = False

def draw_final_result_screen():
    screen.blit(result_image, (0, 0))
    total_score_text = font.render(f'合計得点: {total_score}点', True, BLACK)
    screen.blit(total_score_text, (WIDTH // 2 - total_score_text.get_width() // 2, HEIGHT // 2 - 50))
    for i, score in enumerate(scores):
        score_text = font.render(f'{i+1}回目: {score}点', True, BLACK)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + i*50))
    instruction_text = font.render('スペースキーを押して終了', True, BLACK)
    screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT - 50))

clock = pygame.time.Clock()

graph = measure
ratio_thread  =threading.Thread(target=graph.calcurate)
ratio_thread.start()

while True:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_state == START_SCREEN:
                    game_state = PLAYING
                    reset_game()
                elif game_state == PLAYING and not game_over and not animation_running:
                    hit_pos = get_random_point_in_circle((aim_center_x, aim_center_y), aim_radius)
                    score = calculate_score(hit_pos)
                    animation_running = True
                    animation_start_time = current_time
                elif game_state == PLAYING and game_over:
                    game_count += 1
                    scores.append(score)
                    total_score += score
                    if game_count < 3:
                        game_state = PLAYING
                        reset_game()
                    else:
                        game_state = FINAL_RESULT_SCREEN
                elif game_state == FINAL_RESULT_SCREEN:
                    pygame.quit()
                    exit()

    screen.fill(WHITE)

    if game_state == START_SCREEN:
        draw_start_screen()
    elif game_state == PLAYING:
        screen.fill(WHITE)
        screen.blit(background_image, (0, 0))
        screen.blit(canvas_image, canvas_rect.topleft)

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
                print(current_ratio)

            # 当たった点の描画
            if hit_pos and game_over:
                pygame.draw.circle(screen, BLUE, hit_pos, 5)
                # スコアをヒット位置の上に表示する関数
                score_text = font.render(f'得点: {score}点', True, BLUE)
                score_rect = score_text.get_rect(center=(WIDTH // 2, 30))
                screen.blit(score_text, score_rect)
            
            else:
                # スコアの表示
                score_text = font.render('集中して的を狙おう！', True, BLUE)
                score_text_rect = score_text.get_rect(center=(WIDTH // 2, 30))  # 画面の中央上側に位置
                screen.blit(score_text, score_text_rect)

            min_aim_radius = 20 + 10 * current_ratio

            # 照準の縮小（最小サイズの制限付き）
            if aim_radius > min_aim_radius and not game_over:
                aim_radius = max(aim_radius - aim_shrink_rate, min_aim_radius)
            
            # 標準の拡大
            if aim_radius < min_aim_radius and not game_over:
                aim_radius = max(aim_radius , min_aim_radius + aim_shrink_rate)

            if game_over:
                instruction_text = font.render('スペースキーを押して再開', True, BLACK)
                screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT - 50))
    elif game_state == FINAL_RESULT_SCREEN:
        draw_final_result_screen()
    pygame.display.flip()
    clock.tick(60)  # 60FPSに制限

ratio_thread.join()