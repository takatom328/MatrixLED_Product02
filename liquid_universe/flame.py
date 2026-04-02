import numpy as np


class Flame:
    """
    古典的な炎シミュレーション。

    底辺にランダムな熱を注入し、上方向に拡散・冷却することで
    炎の揺らぎを生成する。

    使い方:
        flame = Flame(width=32, height=48)
        flame.step()
        rgb = flame.to_rgb()   # shape=(H, W, 3) uint8
    """

    def __init__(self, width: int = 32, height: int = 48,
                 cooling: float = 0.07, spread: float = 0.8):
        self.w        = width
        self.h        = height
        self.cooling  = cooling   # 上昇するごとに冷える速さ
        self.spread   = spread    # 横方向への広がり
        self.heat     = np.zeros((height, width), dtype=np.float32)

    def step(self) -> None:
        # 1. 底辺にランダムな熱を注入（熱源）
        self.heat[-1, :] = np.random.uniform(0.8, 1.0, self.w).astype(np.float32)
        self.heat[-2, :] = np.random.uniform(0.6, 1.0, self.w).astype(np.float32)

        # 2. 上方向への拡散（隣接3セルの平均で上に伝わる）
        new_heat = np.zeros_like(self.heat)
        for y in range(self.h - 1):
            left  = np.roll(self.heat[y + 1], -1)
            right = np.roll(self.heat[y + 1],  1)
            new_heat[y] = (self.heat[y + 1] * (1.0 - self.spread) +
                           (left + right) * (self.spread / 2.0))

        # 3. 冷却（高さに応じて冷える）
        cool = np.linspace(self.cooling, self.cooling * 0.1, self.h)[:, np.newaxis]
        new_heat = np.clip(new_heat - cool, 0.0, 1.0)
        new_heat[-1] = self.heat[-1]   # 底辺は熱源なので上書き
        new_heat[-2] = self.heat[-2]
        self.heat = new_heat

    def to_rgb(self, alpha: float = 1.0) -> np.ndarray:
        """
        熱場を炎色のRGB配列に変換する。
        - 横方向にソフトマスクをかけて端を透明化
        - 急峻なべき乗カーブで冷たい部分を完全に黒にする
        alpha: 0.0～1.0 で全体の明るさを制御。
        returns: shape=(H, W, 3) uint8
        """
        # 横方向のソフトマスク（端が 0 になる）
        x = np.linspace(0.0, 1.0, self.w)
        h_mask = np.sin(np.pi * x) ** 1.5   # (W,)

        # 急峻なカーブで冷たい部分を黒にする
        t = np.clip(self.heat * alpha, 0.0, 1.0) ** 1.8
        t = t * h_mask[np.newaxis, :]        # 横マスクを掛ける

        r = np.clip(t ** 0.5 * 255,  0, 255)
        g = np.clip(t ** 2.0 * 220,  0, 255)
        b = np.clip(t ** 6.0 * 100,  0, 255)
        return np.stack([r, g, b], axis=-1).astype(np.uint8)


class FlameManager:
    """
    複数の炎を管理する。ランダムな位置で発生・消滅する。
    """

    def __init__(self, canvas_w: int, canvas_h: int,
                 max_flames: int = 3,
                 spawn_prob: float = 0.02):
        self.cw         = canvas_w
        self.ch         = canvas_h
        self.max_flames = max_flames
        self.spawn_prob = spawn_prob
        self.flames: list = []   # [(flame, x, y, age, max_age), ...]

    def _spawn(self) -> None:
        fw = np.random.randint(20, 40)
        fh = np.random.randint(30, 60)
        x  = np.random.randint(0, max(1, self.cw - fw))
        y  = np.random.randint(self.ch // 2, max(self.ch // 2 + 1, self.ch - fh))
        max_age = np.random.randint(60, 180)
        flame = Flame(width=fw, height=fh,
                      cooling=np.random.uniform(0.05, 0.12),
                      spread=np.random.uniform(0.6, 0.9))
        self.flames.append([flame, x, y, 0, max_age])

    def step(self) -> None:
        # 炎を更新・年齢を進める
        for entry in self.flames:
            entry[0].step()
            entry[3] += 1

        # 寿命が来たものを削除
        self.flames = [e for e in self.flames if e[3] < e[4]]

        # 新しい炎を発生
        if len(self.flames) < self.max_flames and np.random.rand() < self.spawn_prob:
            self._spawn()

    def render(self, canvas: np.ndarray) -> np.ndarray:
        """
        canvas (H, W, 3) uint8 に炎を加算合成して返す。
        """
        out = canvas.astype(np.int32)
        for flame, x, y, age, max_age in self.flames:
            # フェードイン・アウト
            fade_frames = max_age // 4
            if age < fade_frames:
                alpha = age / fade_frames
            elif age > max_age - fade_frames:
                alpha = (max_age - age) / fade_frames
            else:
                alpha = 1.0

            rgb = flame.to_rgb(alpha=alpha)
            fh, fw = rgb.shape[:2]

            # キャンバスに収まる範囲だけ貼る
            y1 = min(y + fh, self.ch)
            x1 = min(x + fw, self.cw)
            fy = y1 - y
            fx = x1 - x
            out[y:y1, x:x1] += rgb[:fy, :fx].astype(np.int32)

        return np.clip(out, 0, 255).astype(np.uint8)
