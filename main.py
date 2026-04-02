#!/usr/bin/env python3
"""
main.py

使い方:
  sudo python3 main.py [モード] [オプション]

  モード:
    0: sine_wave      正弦波（テストパターン）
    1: radial_pulse   放射パルス
    2: interference   干渉模様
    3: reaction       反応拡散 Gray-Scott（デフォルト）

  反応拡散プリセット（モード3のみ）:
    sudo python3 main.py 3 coral    斑点・コーラル
    sudo python3 main.py 3 maze     迷路状
    sudo python3 main.py 3 spots    増殖する島
    sudo python3 main.py 3 waves    うねる縞
    sudo python3 main.py 3 mitosis  分裂
"""

import sys
import time
import signal

from display import MatrixDisplay, WIDTH, HEIGHT
from patterns import sine_wave, radial_pulse, interference
from reaction import GrayScott

running = True

def handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)


def run_pattern(disp, pattern_fn):
    t0 = time.time()
    frame = 0
    while running:
        t = time.time() - t0
        rgb = pattern_fn(t, WIDTH, HEIGHT)
        disp.show(rgb)
        frame += 1
        if frame % 50 == 0:
            fps = frame / t if t > 0 else 0
            print(f'  t={t:.1f}s  fps={fps:.1f}', end='\r')


def run_reaction(disp, preset='coral'):
    gs = GrayScott(width=WIDTH, height=HEIGHT, preset=preset)
    print(f'Preset: {preset}  (模様が出るまで30秒ほどかかります)')
    frame = 0
    t0 = time.time()
    while running:
        gs.step(n=8)
        rgb = gs.to_rgb()
        disp.show(rgb)
        frame += 1
        if frame % 30 == 0:
            t = time.time() - t0
            fps = frame / t if t > 0 else 0
            print(f'  frame={frame}  fps={fps:.1f}', end='\r')


def main():
    mode = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    disp = MatrixDisplay()

    if mode == 0:
        print('Pattern: sine_wave')
        run_pattern(disp, sine_wave)
    elif mode == 1:
        print('Pattern: radial_pulse')
        run_pattern(disp, radial_pulse)
    elif mode == 2:
        print('Pattern: interference')
        run_pattern(disp, interference)
    elif mode == 3:
        preset = sys.argv[2] if len(sys.argv) > 2 else 'coral'
        run_reaction(disp, preset)
    else:
        print(f'Unknown mode: {mode}')

    disp.clear()
    print('\nStopped.')


if __name__ == '__main__':
    main()
