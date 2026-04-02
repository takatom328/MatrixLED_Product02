import numpy as np


class GrayScott:
    """
    Gray-Scott 反応拡散モデル。

    step() の処理順:
      1. 反応拡散（U, V を更新）  ← 常に動く
      2. V だけ渦ベクトル場で移流  ← flow_speed > 0 のとき
      3. ノイズ注入
      4. 外力注入（V スポット）
    """

    PRESETS = {
        'coral':   dict(f=0.055, k=0.062),
        'maze':    dict(f=0.037, k=0.060),
        'spots':   dict(f=0.025, k=0.060),
        'waves':   dict(f=0.039, k=0.058),
        'mitosis': dict(f=0.028, k=0.053),
    }

    def __init__(self, width: int, height: int, preset: str = 'coral'):
        self.w = width
        self.h = height
        p = self.PRESETS[preset]
        self.f   = p['f']
        self.k   = p['k']
        self.Du  = 0.21
        self.Dv  = 0.105
        self.dt  = 1.0
        self._flow_t = 0.0

        self.U = np.ones((height, width), dtype=np.float32)
        self.V = np.zeros((height, width), dtype=np.float32)

        # ランダムな位置にシードを配置
        rng = np.random.default_rng()
        r  = max(height, width) // 8
        cx = np.random.randint(r, width  - r)
        cy = np.random.randint(r, height - r)
        y0, y1 = cy - r, cy + r
        x0, x1 = cx - r, cx + r
        self.U[y0:y1, x0:x1] = 0.5  + rng.random((y1-y0, x1-x0), dtype=np.float32) * 0.1
        self.V[y0:y1, x0:x1] = 0.25 + rng.random((y1-y0, x1-x0), dtype=np.float32) * 0.1

        # 中心固定の渦ベクトル場を事前計算（変わらないので1回だけ）
        self._vx, self._vy = self._make_center_vortex()

    # ------------------------------------------------------------------ #
    #  ベクトル場
    # ------------------------------------------------------------------ #

    def _make_center_vortex(self) -> tuple:
        """
        中心を軸に回転する渦ベクトル場。
        returns: vx, vy  各 (H, W) float32
        """
        px = np.arange(self.w, dtype=np.float32) - self.w / 2.0
        py = np.arange(self.h, dtype=np.float32) - self.h / 2.0
        gx, gy = np.meshgrid(px, py)
        r2 = gx**2 + gy**2 + 1e-6
        # 接線方向: (-y, x) / r  で渦
        vx = -gy / np.sqrt(r2)
        vy =  gx / np.sqrt(r2)
        return vx.astype(np.float32), vy.astype(np.float32)

    # ------------------------------------------------------------------ #
    #  移流（セミラグランジュ法）
    # ------------------------------------------------------------------ #

    def _advect(self, Z: np.ndarray, vx: np.ndarray, vy: np.ndarray) -> np.ndarray:
        h, w = Z.shape
        gx, gy = np.meshgrid(np.arange(w, dtype=np.float32),
                              np.arange(h, dtype=np.float32))
        src_x = np.clip(gx - vx, 0, w - 1)
        src_y = np.clip(gy - vy, 0, h - 1)

        x0 = np.floor(src_x).astype(np.int32)
        y0 = np.floor(src_y).astype(np.int32)
        x1 = np.clip(x0 + 1, 0, w - 1)
        y1 = np.clip(y0 + 1, 0, h - 1)
        tx = src_x - x0
        ty = src_y - y0

        return (Z[y0, x0] * (1-tx) * (1-ty) +
                Z[y0, x1] *    tx  * (1-ty) +
                Z[y1, x0] * (1-tx) *    ty  +
                Z[y1, x1] *    tx  *    ty ).astype(np.float32)

    # ------------------------------------------------------------------ #
    #  ラプラシアン
    # ------------------------------------------------------------------ #

    def _laplacian(self, Z: np.ndarray) -> np.ndarray:
        return (np.roll(Z,  1, axis=0) + np.roll(Z, -1, axis=0) +
                np.roll(Z,  1, axis=1) + np.roll(Z, -1, axis=1) - 4.0 * Z)

    # ------------------------------------------------------------------ #
    #  メインループ
    # ------------------------------------------------------------------ #

    def blend_preset(self, target: str, alpha: float) -> None:
        """
        現在の f, k を target プリセットへ alpha（0.0→1.0）で補間する。
        毎フレーム小さい alpha で呼ぶと、模様がじわじわ変形していく。
        """
        p = self.PRESETS[target]
        self.f += (p['f'] - self.f) * alpha
        self.k += (p['k'] - self.k) * alpha

    def step(self, n: int = 4,
             flow_speed: float = 0.6,
             noise_scale: float = 0.01,
             inject_prob: float = 0.01,
             inject_radius: int = 2) -> None:

        # 1. 反応拡散（U, V 両方を更新）
        for _ in range(n):
            U, V = self.U, self.V
            uvv  = U * V * V
            self.U = np.clip(U + self.dt * (self.Du * self._laplacian(U) - uvv + self.f * (1 - U)), 0, 1)
            self.V = np.clip(V + self.dt * (self.Dv * self._laplacian(V) + uvv - (self.f + self.k) * V), 0, 1)

        # 2. V だけ渦で移流（表示に "流れ" を加える）
        if flow_speed > 0:
            self.V = self._advect(self.V, self._vx * flow_speed, self._vy * flow_speed)

        # 3. ノイズ
        if noise_scale > 0:
            noise = (np.random.rand(*self.U.shape).astype(np.float32) - 0.5) * noise_scale
            self.U = np.clip(self.U + noise, 0, 1)
            self.V = np.clip(self.V + noise, 0, 1)

        # 4. 外力注入
        if inject_prob > 0 and np.random.rand() < inject_prob:
            r = inject_radius
            x = np.random.randint(r, self.w - r)
            y = np.random.randint(r, self.h - r)
            self.V[y-r:y+r, x-r:x+r] = 1.0
            self.U[y-r:y+r, x-r:x+r] = 0.0

    @property
    def field(self) -> np.ndarray:
        """V フィールドを 0.0～1.0 で返す。"""
        return self.V


def generate_wave_field(width: int, height: int, t: float) -> np.ndarray:
    x = np.linspace(0.0, 1.0, width)
    y = np.linspace(0.0, 1.0, height)
    xx, yy = np.meshgrid(x, y)
    wave1 = np.sin(2.0 * np.pi * (3.0 * xx + 0.8 * t))
    wave2 = np.sin(2.0 * np.pi * (2.0 * yy - 0.5 * t))
    cx, cy = 0.5, 0.5
    rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    wave3 = np.sin(2.0 * np.pi * (8.0 * rr - 1.2 * t))
    field = 0.4 * wave1 + 0.3 * wave2 + 0.3 * wave3
    field = (field - field.min()) / (field.max() - field.min())
    return field
