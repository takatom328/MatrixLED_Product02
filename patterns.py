"""
patterns.py - Step1 テストパターン集
全パターンは (GRID_H, GRID_W, 3) uint8 を返す
"""

import numpy as np
import math


def sine_wave(t, grid_w=64, grid_h=64):
    """
    正弦波グラデーション（時間で流れる）
    t: 時刻（秒）
    """
    x = np.linspace(0, 2 * math.pi, grid_w)
    y = np.linspace(0, 2 * math.pi, grid_h)
    xx, yy = np.meshgrid(x, y)

    # 真横に流れる波
    val = 0.5 + 0.5 * np.sin(yy - t * 1.5)

    # 青〜シアン系の色
    r = (val * 16).astype(np.uint8)
    g = (val * 128).astype(np.uint8)
    b = (val * 64).astype(np.uint8)

    return np.stack([r, g, b], axis=2)


def radial_pulse(t, grid_w=64, grid_h=64):
    """
    中心から広がる同心円（時間で脈打つ）
    """
    cx, cy = grid_w / 2, grid_h / 2
    x = np.arange(grid_w)
    y = np.arange(grid_h)
    xx, yy = np.meshgrid(x, y)

    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    val = 0.5 + 0.5 * np.sin(dist * 0.4 - t * 3.0)

    r = (val * 10).astype(np.uint8)
    g = (val * 80).astype(np.uint8)
    b = (val * 255).astype(np.uint8)

    return np.stack([r, g, b], axis=2)


def interference(t, grid_w=64, grid_h=64):
    """
    2つの波源の干渉模様
    """
    x = np.arange(grid_w, dtype=float)
    y = np.arange(grid_h, dtype=float)
    xx, yy = np.meshgrid(x, y)

    # 2つの波源（時間でゆっくり移動）
    ax = grid_w * (0.3 + 0.15 * math.sin(t * 0.3))
    ay = grid_h * (0.4 + 0.1 * math.sin(t * 0.5))
    bx = grid_w * (0.7 + 0.1 * math.sin(t * 0.4))
    by = grid_h * (0.6 + 0.15 * math.sin(t * 0.2))

    d1 = np.sqrt((xx - ax) ** 2 + (yy - ay) ** 2)
    d2 = np.sqrt((xx - bx) ** 2 + (yy - by) ** 2)

    val = 0.5 + 0.25 * np.sin(d1 * 0.25 - t * 2.0) \
              + 0.25 * np.sin(d2 * 0.25 - t * 2.0)

    # 白黒ベース + エッジにプリズムカラー
    gx = np.roll(val, -1, axis=1) - np.roll(val, 1, axis=1)
    gy = np.roll(val, -1, axis=0) - np.roll(val, 1, axis=0)
    edge = np.clip(np.sqrt(gx**2 + gy**2) * 8.0, 0.0, 1.0)

    gray = val ** 1.2

    # 波源間の光路差でプリズム分光（自然な薄膜干渉に近い挙動）
    phase = (d1 - d2) * 0.4 + t * 0.8
    cr = 0.5 + 0.5 * np.sin(phase)
    cg = 0.5 + 0.5 * np.sin(phase + 2.094)
    cb = 0.5 + 0.5 * np.sin(phase + 4.189)

    r = np.clip(gray * 180 + edge * cr * 220, 0, 255).astype(np.uint8)
    g = np.clip(gray * 180 + edge * cg * 220, 0, 255).astype(np.uint8)
    b = np.clip(gray * 180 + edge * cb * 220, 0, 255).astype(np.uint8)

    return np.stack([r, g, b], axis=2)
