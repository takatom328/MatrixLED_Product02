import numpy as np
from PIL import Image


def upscale_rgb_array(rgb_array: np.ndarray, scale: int = 2) -> np.ndarray:
    """
    shape=(H, W, 3) のRGB配列を scale倍に拡大し、NumPy配列として返す。
    """
    img = Image.fromarray(rgb_array, mode="RGB")
    img = img.resize(
        (rgb_array.shape[1] * scale, rgb_array.shape[0] * scale),
        resample=Image.NEAREST
    )
    return np.array(img)
