#!/usr/bin/env python3
"""
main.py - Step1 動作確認
テストパターンを順番に表示してパネル配置・解像度・色を確認する

使い方:
  sudo python3 main.py [パターン番号]
    0: sine_wave (デフォルト)
    1: radial_pulse
    2: interference
"""

import sys
import time
import signal

from display import MatrixDisplay
from patterns import sine_wave, radial_pulse, interference

PATTERNS = [sine_wave, radial_pulse, interference]
PATTERN_NAMES = ['sine_wave', 'radial_pulse', 'interference']

running = True

def handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)


def main():
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    idx = idx % len(PATTERNS)
    pattern_fn = PATTERNS[idx]

    print(f'Pattern: {PATTERN_NAMES[idx]}')
    print('Ctrl+C to stop')

    disp = MatrixDisplay()
    t0 = time.time()

    frame = 0
    while running:
        t = time.time() - t0
        rgb = pattern_fn(t)
        disp.show(rgb)
        frame += 1

        # FPS表示（50フレームごと）
        if frame % 50 == 0:
            fps = frame / t if t > 0 else 0
            print(f'  t={t:.1f}s  fps={fps:.1f}', end='\r')

    disp.clear()
    print('\nStopped.')


if __name__ == '__main__':
    main()
