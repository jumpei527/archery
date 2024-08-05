import pygame
WINDOW_WIDTH = 600
WINDOW_HIGHT = 100
FONT_PATH = "g_squarebold_free_010.ttf"
moji = "♪　みんなで歌おう　♪"
pygame.init()
text_font = pygame.font.Font (FONT_PATH, 50)
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HIGHT))
screen.fill((255, 255, 255))
text_r = text_font.render(moji, True, (255,255,255),(55,55,55))
w,h = text_r.get_size()
screen.blit(text_r, (WINDOW_WIDTH / 2 - w/2, WINDOW_HIGHT / 2 - h/2))
pygame.display.flip()
LOOP = True
while LOOP:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: LOOP = False