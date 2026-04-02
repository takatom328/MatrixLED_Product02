#!/usr/bin/env python3
"""
診断用スクリプト: 4象限を異なる色で表示してパネルのマッピングを確認する
正しく補正されていれば: 左上=赤 / 右上=緑 / 左下=青 / 右下=黄
"""
import sys
import time
import signal
import numpy as np

from display import MatrixDisplay, GRID_W, GRID_H

disp = MatrixDisplay()

arr = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
hw, hh = GRID_W // 2, GRID_H // 2

arr[:hh, :hw] = (180, 0,   0  )  # 左上: 赤
arr[:hh, hw:] = (0,   180, 0  )  # 右上: 緑
arr[hh:, :hw] = (0,   0,   180)  # 左下: 青
arr[hh:, hw:] = (180, 180, 0  )  # 右下: 黄

print("表示中... Ctrl+C で終了")
print("期待する表示: 左上=赤 / 右上=緑 / 左下=青 / 右下=黄")

running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))
while running:
    disp.show(arr)
    time.sleep(0.5)

disp.clear()
