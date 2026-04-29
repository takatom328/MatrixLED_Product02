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

DEFAULT_PRESET = 'maze'


class GrayScott:
    def __init__(self, width=64, height=64, preset=DEFAULT_PRESET):
        self.W = width
        self.H = height

        p = PRESETS[preset]
        self.f  = p['f']
        self.k  = p['k']
        self.Du = 0.2100   # U の拡散係数
        self.Dv = 0.1050   # V の拡散係数 (Du の半分)
        self.dt = 0.4      # 時間ステップ

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

    def to_rgb(self, palette=None):
        """
        V の濃度と輪郭を色に変換して (H, W, 3) uint8 を返す

        palette: 'ocean'(default) / 'aurora' / 'lava' / 'void' / 'gold'
        """
        if palette is None:
            palette = getattr(self, 'palette', 'ocean')

        v = self.V  # 0.0 〜 1.0

        # 輪郭強調: V の勾配の大きさ（境界線を光らせる）
        gx = np.roll(v, -1, axis=1) - np.roll(v, 1, axis=1)
        gy = np.roll(v, -1, axis=0) - np.roll(v, 1, axis=0)
        edge = np.clip(np.sqrt(gx**2 + gy**2) * 6.0, 0.0, 1.0)

        # 輝度カーブ: 暗部を黒に、ハイライトを鋭く（LED映え）
        t = np.clip(v * 2.5, 0.0, 1.0) ** 1.4

        if palette == 'ocean':
            # 深い青〜シアン〜白。輪郭はシアン白で発光
            r = t ** 2.5 * 60  + edge * 180
            g = t ** 1.3 * 180 + edge * 240
            b = t ** 0.8 * 255 + edge * 255

        elif palette == 'aurora':
            # 紫〜緑〜白。U-V の差で色相をシフト
            uv = np.clip((self.U - self.V) * 2.0, 0.0, 1.0)
            r = t ** 2.0 * 120 * (1 - uv) + edge * 200
            g = t ** 1.0 * 220 * uv        + edge * 200
            b = t ** 1.5 * 255             + edge * 180

        elif palette == 'lava':
            # 暗赤〜オレンジ〜黄白。溶岩・有機体感
            r = t ** 0.7 * 255 + edge * 255
            g = t ** 2.0 * 160 + edge * 180
            b = t ** 4.0 * 60  + edge * 80

        elif palette == 'void':
            # ほぼ黒。輪郭だけが細い光の線として浮かぶ
            r = edge * 40  + t ** 3.0 * 20
            g = edge * 128 + t ** 2.5 * 80
            b = edge * 20 + t ** 2.0 * 180

        elif palette == 'gold':
            # 金・琥珀・白金。和風・神秘的
            r = t ** 0.9 * 255 + edge * 255
            g = t ** 1.4 * 180 + edge * 200
            b = t ** 3.0 * 40  + edge * 100

        else:
            r = t * 200
            g = t * 200
            b = t * 200

        r = np.clip(r, 0, 255).astype(np.uint8)
        g = np.clip(g, 0, 255).astype(np.uint8)
        b = np.clip(b, 0, 255).astype(np.uint8)

        return np.stack([r, g, b], axis=2)

    def set_preset(self, name):
        if name in PRESETS:
            p = PRESETS[name]
            self.f = p['f']
            self.k = p['k']
