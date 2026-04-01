"""
display.py - LED matrix display engine
64x64 panel x 4枚 / chain=4 / U-mapper / 128x128px
"""

import sys
import os
sys.path.append('/home/tt18/projects/rpi-rgb-led-matrix/bindings/python')

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import numpy as np

# 論理解像度（全パネル合計）
WIDTH  = 128
HEIGHT = 128

# 計算格子サイズ（描画時にWIDTH/HEIGHTへ拡大）
GRID_W = 64
GRID_H = 64


def make_options():
    options = RGBMatrixOptions()
    options.hardware_mapping    = 'adafruit-hat'
    options.rows                = 64          # 1枚のパネル高さ
    options.cols                = 64          # 1枚のパネル幅
    options.chain_length        = 4           # 直列4枚
    options.parallel            = 1
    options.pixel_mapper_config = 'U-mapper'  # 2x2に折り畳む
    options.gpio_slowdown        = 4
    options.disable_hardware_pulsing = True
    options.panel_type          = 'FM6126A'
    options.brightness          = 80
    return options


class MatrixDisplay:
    def __init__(self):
        self.matrix = RGBMatrix(options=make_options())
        self.canvas = self.matrix.CreateFrameCanvas()

    def show(self, rgb_array):
        """
        rgb_array: shape (GRID_H, GRID_W, 3) uint8
        GRID → WIDTH/HEIGHT へリサイズして表示
        """
        img = Image.fromarray(rgb_array, 'RGB')
        if img.size != (WIDTH, HEIGHT):
            img = img.resize((WIDTH, HEIGHT), Image.NEAREST)
        self.canvas.SetImage(img)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def clear(self):
        self.canvas.Clear()
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
