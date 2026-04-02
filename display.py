"""
display.py - LED matrix display engine

配線: Z字 chain 0→1→2→3
物理配置:
  [Chain0: 左上][Chain1: 右上]
  [Chain2: 左下][Chain3: 右下]

ライブラリにはmapperを使わず、256×64の横並びとして渡す。
show()内で128×128の画像を4象限に分解してチェーン順に配置する。
→ パネル境界で完全にシームレスになる。
"""

import sys
sys.path.append('/home/tt18/projects/rpi-rgb-led-matrix/bindings/python')

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import numpy as np

# シミュレーション・表示の論理解像度
WIDTH  = 128
HEIGHT = 128

# 計算格子サイズ
GRID_W = 64
GRID_H = 64

# キャンバス実寸（chain=4 × cols=64 × rows=64）
_CANVAS_W = 256
_CANVAS_H = 64


def make_options():
    options = RGBMatrixOptions()
    options.hardware_mapping         = 'adafruit-hat'
    options.rows                     = 64   # 1枚の高さ
    options.cols                     = 64   # 1枚の幅
    options.chain_length             = 4    # 直列4枚
    options.parallel                 = 1
    options.pixel_mapper_config      = ''   # mapperなし
    options.gpio_slowdown            = 3
    options.disable_hardware_pulsing = True
    options.brightness               = 80
    return options


class MatrixDisplay:
    def __init__(self):
        self.matrix = RGBMatrix(options=make_options())
        self.canvas = self.matrix.CreateFrameCanvas()

    def show(self, rgb_array):
        """
        rgb_array: shape (GRID_H, GRID_W, 3) uint8

        128×128 → 256×64 に変換してチェーン順に渡す:
          Chain0 (x=  0- 63): 左上象限 image(  0- 63,   0- 63)
          Chain1 (x= 64-127): 右上象限 image( 64-127,   0- 63)
          Chain2 (x=128-191): 左下象限 image(  0- 63,  64-127)
          Chain3 (x=192-255): 右下象限 image( 64-127,  64-127)
        """
        src = Image.fromarray(rgb_array, 'RGB')
        if src.size != (WIDTH, HEIGHT):
            src = src.resize((WIDTH, HEIGHT), Image.NEAREST)

        strip = Image.new("RGB", (_CANVAS_W, _CANVAS_H))
        strip.paste(src.crop((  0,  0,  64,  64)), (  0, 0))  # 左上 → Chain0
        strip.paste(src.crop(( 64,  0, 128,  64)), ( 64, 0))  # 右上 → Chain1
        strip.paste(src.crop((  0, 64,  64, 128)), (128, 0))  # 左下 → Chain2
        strip.paste(src.crop(( 64, 64, 128, 128)), (192, 0))  # 右下 → Chain3

        self.canvas.SetImage(strip)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def clear(self):
        self.canvas.Clear()
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
