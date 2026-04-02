"""
PC画面でリアルタイム表示（pygame版）。

  source venv/bin/activate
  python3 main.py [mode] [preset]

  mode:
    wave     波模様（デフォルト）
    coral    反応拡散 coral
    maze     反応拡散 maze
    spots    反応拡散 spots
    waves    反応拡散 waves
    mitosis  反応拡散 mitosis

q キーまたはウィンドウを閉じると終了。
"""
import sys
import pygame

from simulation import generate_wave_field, GrayScott
from palette import blue_purple_palette
from display import upscale_rgb_array


SIM_W = 64
SIM_H = 64
SCALE = 4    # 64x64 -> 256x256
FPS   = 30
DT    = 0.05

GS_PRESETS = {'coral', 'maze', 'spots', 'waves', 'mitosis'}


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else 'wave'

    screen_w = SIM_W * SCALE
    screen_h = SIM_H * SCALE

    pygame.init()
    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption(f"Liquid Universe — {mode}")
    clock = pygame.time.Clock()

    # モードに応じてシミュレータを初期化
    gs = GrayScott(SIM_W, SIM_H, preset=mode) if mode in GS_PRESETS else None
    t  = 0.0
    running = True

    if gs:
        print(f'Gray-Scott preset: {mode}  (模様が出るまで30秒ほどかかります)')
    else:
        print('Wave field mode')

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False

        # field を更新
        if gs:
            gs.step(n=8)
            field = gs.field
        else:
            field = generate_wave_field(SIM_W, SIM_H, t)
            t += DT

        rgb_small = blue_purple_palette(field)
        rgb_large = upscale_rgb_array(rgb_small, scale=SCALE)

        surface = pygame.surfarray.make_surface(rgb_large.swapaxes(0, 1))
        screen.blit(surface, (0, 0))
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
