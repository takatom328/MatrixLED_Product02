import numpy as np
from PIL import Image


def field_to_grayscale_image(field: np.ndarray, scale: int = 2) -> Image.Image:
    """
    0.0 ～ 1.0 の2次元配列をグレースケール画像に変換して返す。
    scale=2 なら、64x64 -> 128x128 に拡大する（4パネル 128x128 に合わせる）。
    """
    img_array = np.clip(field * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(img_array, mode="L")
    img = img.resize(
        (field.shape[1] * scale, field.shape[0] * scale),
        resample=Image.NEAREST
    )
    return img


def _palette_rgb(t: np.ndarray, name: str):
    if name == 'fire':
        return t**0.6*255, t**1.8*200, t**4.0*80
    elif name == 'aurora':
        return t**2.0*180, t**0.9*220, t**1.2*255
    elif name == 'blue_purple':
        return t**1.8*220, t**2.5*120, t**0.8*255
    else:  # blue
        return t**2.5*80, t**1.3*180, t**0.7*255


def field_to_rgb_array(field: np.ndarray, palette_blend: float = 0.0) -> np.ndarray:
    """
    0.0 ～ 1.0 の2次元配列を (H, W, 3) uint8 のRGB配列に変換して返す。
    palette_blend: 0.0～4.0 で blue_purple→blue→fire→aurora を巡回。
    """
    t = np.clip(field, 0.0, 1.0)
    order = ['blue_purple', 'blue', 'fire', 'aurora']
    idx   = int(palette_blend) % 4
    nxt   = (idx + 1) % 4
    alpha = palette_blend % 1.0

    r0, g0, b0 = _palette_rgb(t, order[idx])
    r1, g1, b1 = _palette_rgb(t, order[nxt])

    r = np.clip(r0*(1-alpha) + r1*alpha, 0, 255)
    g = np.clip(g0*(1-alpha) + g1*alpha, 0, 255)
    b = np.clip(b0*(1-alpha) + b1*alpha, 0, 255)
    return np.stack([r, g, b], axis=-1).astype(np.uint8)


def field_to_color_image(field: np.ndarray, scale: int = 2, palette: str = "blue") -> Image.Image:
    """
    0.0 ～ 1.0 の2次元配列をカラー画像に変換して返す。

    palette:
        blue   : 黒 → 深青 → シアン → 白（デフォルト）
        fire   : 黒 → 赤 → オレンジ → 黄白
        aurora : 黒 → 紫 → 緑 → 白
    """
    t = np.clip(field, 0.0, 1.0)

    if palette == "fire":
        r = np.clip(t ** 0.6 * 255, 0, 255)
        g = np.clip(t ** 1.8 * 200, 0, 255)
        b = np.clip(t ** 4.0 * 80,  0, 255)
    elif palette == "aurora":
        r = np.clip(t ** 2.0 * 180, 0, 255)
        g = np.clip(t ** 0.9 * 220, 0, 255)
        b = np.clip(t ** 1.2 * 255, 0, 255)
    else:  # blue
        r = np.clip(t ** 2.5 * 80,  0, 255)
        g = np.clip(t ** 1.3 * 180, 0, 255)
        b = np.clip(t ** 0.7 * 255, 0, 255)

    rgb = np.stack([r, g, b], axis=-1).astype(np.uint8)
    img = Image.fromarray(rgb, mode="RGB")
    img = img.resize(
        (field.shape[1] * scale, field.shape[0] * scale),
        resample=Image.NEAREST
    )
    return img
