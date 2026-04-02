import numpy as np


def _apply(t: np.ndarray, r_exp, r_scale, g_exp, g_scale, b_exp, b_scale) -> np.ndarray:
    r = np.clip(t ** r_exp * r_scale, 0, 255)
    g = np.clip(t ** g_exp * g_scale, 0, 255)
    b = np.clip(t ** b_exp * b_scale, 0, 255)
    return np.stack([r, g, b], axis=-1)


def blue_purple_palette(field: np.ndarray) -> np.ndarray:
    """黒 → 深青 → 紫 → 白"""
    t = np.clip(field, 0.0, 1.0)
    return _apply(t, 1.8, 220, 2.5, 120, 0.8, 255).astype(np.uint8)


def blue_palette(field: np.ndarray) -> np.ndarray:
    """黒 → 深青 → シアン → 白"""
    t = np.clip(field, 0.0, 1.0)
    return _apply(t, 2.5, 80, 1.3, 180, 0.7, 255).astype(np.uint8)


def fire_palette(field: np.ndarray) -> np.ndarray:
    """黒 → 赤 → オレンジ → 黄白"""
    t = np.clip(field, 0.0, 1.0)
    return _apply(t, 0.6, 255, 1.8, 200, 4.0, 80).astype(np.uint8)


def aurora_palette(field: np.ndarray) -> np.ndarray:
    """黒 → 紫 → 緑 → 白"""
    t = np.clip(field, 0.0, 1.0)
    return _apply(t, 2.0, 180, 0.9, 220, 1.2, 255).astype(np.uint8)


# パレット名 → 関数のマップ
PALETTES = {
    'blue_purple': blue_purple_palette,
    'blue':        blue_palette,
    'fire':        fire_palette,
    'aurora':      aurora_palette,
}


def blend(field: np.ndarray, palette_blend: float) -> np.ndarray:
    """
    palette_blend: 0.0 ～ 4.0 を連続値で巡回。
    """
    order = ['blue_purple', 'blue', 'fire', 'aurora']
    idx   = int(palette_blend) % len(order)
    nxt   = (idx + 1) % len(order)
    alpha = palette_blend % 1.0
    rgb0 = PALETTES[order[idx]](field).astype(np.float32)
    rgb1 = PALETTES[order[nxt]](field).astype(np.float32)
    return np.clip(rgb0 * (1 - alpha) + rgb1 * alpha, 0, 255).astype(np.uint8)


def fire_emergence(field: np.ndarray, intensity: float,
                   flicker: np.ndarray = None,
                   dark_intensity: float = 0.0) -> np.ndarray:
    """
    intensity:      0.0 → 冷たい氷青, 1.0 → 全画面真っ赤
    dark_intensity: 0.0 → 通常, 1.0 → 黒い炎が全面を覆う
    flicker:        (H, W) 0.0〜1.0 の揺らぎマップ
    """
    t = np.clip(field, 0.0, 1.0)

    # 冷たい背景（氷青〜シアン）
    r_cold = t ** 3.0 *  40
    g_cold = t ** 1.2 * 200
    b_cold = t ** 0.6 * 255

    # 暖かい背景（紫〜マゼンタ）
    r_warm = t ** 1.4 * 200
    g_warm = t ** 3.5 *  60
    b_warm = t ** 1.2 * 180

    # intensity に応じて冷→暖へ補間
    warmth = np.clip(intensity * 1.5, 0.0, 1.0)
    r_bg = r_cold * (1 - warmth) + r_warm * warmth
    g_bg = g_cold * (1 - warmth) + g_warm * warmth
    b_bg = b_cold * (1 - warmth) + b_warm * warmth

    # 炎色（赤→オレンジ→黄→白）
    r_fire = t ** 0.5 * 255
    g_fire = t ** 2.0 * 220
    b_fire = t ** 6.0 * 100

    # V値に基づくマスク（intensityで閾値が下がる）
    threshold = 0.3 * (1.0 - intensity)
    width     = max(0.05, 0.4 * (1.0 - intensity * 0.8))
    fire_mask = np.clip((t - threshold) / width, 0.0, 1.0)

    r = r_bg * (1 - fire_mask) + r_fire * fire_mask
    g = g_bg * (1 - fire_mask) + g_fire * fire_mask
    b = b_bg * (1 - fire_mask) + b_fire * fire_mask

    # ピーク時に全画面を真っ赤に
    base = intensity ** 2.0
    r = r + base * (255 - r)
    g = g * (1.0 - base * 0.75)
    b = b * (1.0 - base * 0.95)

    # 明炎の揺らぎ（炎フェーズ）
    if flicker is not None and intensity > 0:
        flicker_strength = intensity ** 1.5
        lum = 1.0 - flicker_strength * (1.0 - flicker) * 0.4
        r = r * lum
        g = g * lum
        b = b * lum

    # 黒い炎：フリッカーの谷が暗闇となって侵食する
    if flicker is not None and dark_intensity > 0:
        dark_flame = (1.0 - flicker) ** 1.2 * dark_intensity
        r = r * (1.0 - dark_flame)
        g = g * (1.0 - dark_flame)
        b = b * (1.0 - dark_flame)

    return np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)
