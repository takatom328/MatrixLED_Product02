"""
reaction.py - Gray-Scott 反応拡散システム
Step 2: 数式から模様が自律的に生まれ続ける

dU/dt = Du * ∇²U  -  U*V²  +  f*(1-U)
dV/dt = Dv * ∇²V  +  U*V²  -  (f+k)*V

U: 物質A（広がりやすい）
V: 物質B（局所的に反応）
f: feed rate（Uの供給速度）
k: kill rate（Vの消滅速度）

f/k の組み合わせで模様の性格が変わる:
  (0.055, 0.062) → 斑点・コーラル
  (0.037, 0.060) → 迷路状
  (0.025, 0.060) → 増殖する島
  (0.039, 0.058) → うねる縞
"""

import numpy as np

# パラメータプリセット
PRESETS = {
    'coral':  dict(f=0.055, k=0.062),
    'maze':   dict(f=0.037, k=0.060),
    'spots':  dict(f=0.025, k=0.060),
    'waves':  dict(f=0.039, k=0.058),
    'mitosis': dict(f=0.028, k=0.053),
}

DEFAULT_PRESET = 'coral'


class GrayScott:
    def __init__(self, width=64, height=64, preset=DEFAULT_PRESET):
        self.W = width
        self.H = height

        p = PRESETS[preset]
        self.f  = p['f']
        self.k  = p['k']
        self.Du = 0.2100   # U の拡散係数
        self.Dv = 0.1050   # V の拡散係数 (Du の半分)
        self.dt = 1.0      # 時間ステップ

        self._init_field()

    def _init_field(self):
        """フィールド初期化: ランダムな位置にVの種を撒く"""
        self.U = np.ones((self.H, self.W), dtype=np.float32)
        self.V = np.zeros((self.H, self.W), dtype=np.float32)

        rng = np.random.default_rng()
        n_seeds = max(5, (self.W * self.H) // 400)
        for _ in range(n_seeds):
            cy = rng.integers(8, self.H - 8)
            cx = rng.integers(8, self.W - 8)
            r = rng.integers(3, 7)
            self.U[cy-r:cy+r, cx-r:cx+r] = 0.50
            self.V[cy-r:cy+r, cx-r:cx+r] = 0.25

    def _laplacian(self, Z):
        """2Dラプラシアン（周期境界条件）"""
        return (
            np.roll(Z,  1, axis=0) + np.roll(Z, -1, axis=0) +
            np.roll(Z,  1, axis=1) + np.roll(Z, -1, axis=1) -
            4 * Z
        )

    def step(self, n=8):
        """n ステップ更新"""
        U, V = self.U, self.V
        for _ in range(n):
            Lu = self._laplacian(U)
            Lv = self._laplacian(V)
            uvv = U * V * V
            dU = self.Du * Lu - uvv + self.f * (1.0 - U)
            dV = self.Dv * Lv + uvv - (self.f + self.k) * V
            U += dU * self.dt
            V += dV * self.dt
        np.clip(U, 0, 1, out=U)
        np.clip(V, 0, 1, out=V)
        self.U, self.V = U, V

    def to_rgb(self):
        """
        V の濃度を色に変換して (H, W, 3) uint8 を返す
        色: 深い青〜シアン〜白（LED映えする配色）
        """
        v = self.V  # 0.0 〜 1.0

        # 輝度を強調（低い値は切り捨て、高い値を広げる）
        t = np.clip(v * 3.0, 0.0, 1.0)

        r = (t ** 2.0 * 80).astype(np.uint8)
        g = (t ** 1.2 * 200).astype(np.uint8)
        b = (t ** 0.7 * 255).astype(np.uint8)

        return np.stack([r, g, b], axis=2)

    def set_preset(self, name):
        if name in PRESETS:
            p = PRESETS[name]
            self.f = p['f']
            self.k = p['k']
