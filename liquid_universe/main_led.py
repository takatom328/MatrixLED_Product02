"""
LEDパネル出力版。

  sudo python3 main_led.py

1サイクルのシナリオ（PRESET_CYCLE_SEC 秒）:
  フェードイン → 渦 → 炎 → 渦に戻る → フェードアウト → 真っ暗 → 次のプリセット
"""
import sys
import time
import signal
import numpy as np

sys.path.insert(0, '/home/tt18/projects/fluid_art')
from display import MatrixDisplay, WIDTH, HEIGHT

from simulation import GrayScott
from palette import fire_emergence

running = True

def handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

# ---- タイミング設定（秒） ----
FADE_IN_SEC    =  6.0   # フェードイン
VORTEX_SEC     = 15.0   # 渦の通常表示
FIRE_SEC       = 20.0   # 炎（sin カーブで出て引く）
RETURN_SEC     = 10.0   # 渦に戻る
FADE_OUT_SEC   =  6.0   # フェードアウト
BLACK_SEC      =  2.0   # 真っ暗

# サイクル内の各フェーズ開始時刻
T_VORTEX      = FADE_IN_SEC
T_FIRE        = T_VORTEX  + VORTEX_SEC
T_RETURN      = T_FIRE    + FIRE_SEC
T_FADE_OUT    = T_RETURN  + RETURN_SEC
T_BLACK       = T_FADE_OUT + FADE_OUT_SEC
CYCLE_TOTAL   = T_BLACK   + BLACK_SEC

FLOW_NORMAL   = 0.6   # 通常の流れ速度

PRESET_ORDER  = ['coral', 'maze', 'spots', 'waves', 'mitosis']


def main() -> None:
    print('起動中...  Ctrl+C で停止')
    print(f'プリセット順: {" → ".join(PRESET_ORDER)}')
    print(f'1サイクル {CYCLE_TOTAL:.0f}秒: 渦 → 炎 → 渦 → 暗転')

    disp = MatrixDisplay()

    preset_idx = 0
    gs = GrayScott(WIDTH, HEIGHT, preset=PRESET_ORDER[preset_idx])

    frame     = 0
    t0        = time.time()
    t_cycle   = time.time()
    flicker_t   = 0.0
    noise_drift = np.zeros(4, dtype=np.float32)  # ランダムウォーク位相

    while running:
        now     = time.time()
        elapsed = now - t0
        phase   = now - t_cycle   # このサイクルに入ってからの秒数

        # ---- サイクル終了 → 次のプリセット ----
        if phase >= CYCLE_TOTAL:
            preset_idx = (preset_idx + 1) % len(PRESET_ORDER)
            print(f'\n→ {PRESET_ORDER[preset_idx]}')
            gs = GrayScott(WIDTH, HEIGHT, preset=PRESET_ORDER[preset_idx])
            t_cycle = time.time()
            continue

        # ---- フェーズ判定 ----
        dark_intensity = 0.0
        color_dim      = 1.0
        if phase < T_VORTEX:
            # フェードイン
            brightness     = phase / FADE_IN_SEC
            fire_intensity = 0.0
            flow_speed     = FLOW_NORMAL

        elif phase < T_FIRE:
            # 渦（通常）
            brightness     = 1.0
            fire_intensity = 0.0
            flow_speed     = FLOW_NORMAL

        elif phase < T_RETURN:
            # 炎フェーズ：前半で燃え上がり、後半は炎が渦に引き込まれる
            p              = (phase - T_FIRE) / FIRE_SEC
            fire_intensity = float(np.sin(np.pi * p))
            brightness     = 1.0
            # 後半（p>0.5）は flow を通常より強くして炎を渦に引き込む
            if p <= 0.5:
                flow_speed = FLOW_NORMAL * (1.0 - fire_intensity)
            else:
                pull = (p - 0.5) * 2.0   # 0→1
                flow_speed = FLOW_NORMAL * (1.0 - fire_intensity) + FLOW_NORMAL * 1.8 * pull * (1.0 - fire_intensity)

        elif phase < T_FADE_OUT:
            # 渦に戻る（強めの流れ + 色が徐々に黒へ + 軽い暗渦）
            p_return       = (phase - T_RETURN) / RETURN_SEC   # 0→1
            fire_intensity = 0.0
            dark_intensity = 0.0
            brightness     = 1.0
            color_dim      = 1.0 - p_return ** 1.2 * 0.6      # 1.0 → 0.4
            flow_speed     = FLOW_NORMAL * (1.0 + 0.8 * (1.0 - p_return))

        elif phase < T_BLACK:
            # フェードアウト：黒渦が広がりながら完全に消える
            p_out          = (phase - T_FADE_OUT) / FADE_OUT_SEC   # 0→1
            fire_intensity = 0.0
            dark_intensity = 0.0
            brightness     = 1.0
            color_dim      = 0.4 * (1.0 - p_out ** 0.8)       # 0.4 → 0.0
            flow_speed     = FLOW_NORMAL * (1.0 - p_out * 0.6)

        else:
            # 真っ暗
            disp.show(np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8))
            frame += 1
            continue

        # ---- フリッカーフィールドを生成（極座標差動回転 + ランダム揺らぎ）----
        flicker_t   += flow_speed * 0.8 + fire_intensity * 0.4
        # ランダムウォーク：炎が強いほど揺れが大きい
        rand_strength = 0.06 + fire_intensity * 0.18
        noise_drift  += np.random.uniform(-rand_strength, rand_strength, 4).astype(np.float32)

        px = np.linspace(-1.0, 1.0, WIDTH,  dtype=np.float32)
        py = np.linspace(-1.0, 1.0, HEIGHT, dtype=np.float32)
        gx, gy = np.meshgrid(px, py)
        r      = np.sqrt(gx**2 + gy**2)
        theta  = np.arctan2(gy, gx)
        r_safe = r + 0.3

        flicker = (
            0.40 * np.sin(theta * 3 - flicker_t * 1.0 / r_safe + noise_drift[0]) +
            0.28 * np.sin(r * 7.0   + flicker_t * 2.0           + noise_drift[1]) +
            0.20 * np.sin(theta * 5 - flicker_t * 0.5 / r_safe  + noise_drift[2]) +
            0.12 * np.sin(theta * 7 + r * 4.0 - flicker_t * 1.3 + noise_drift[3])
        )
        flicker = (flicker - flicker.min()) / (flicker.max() - flicker.min() + 1e-6)
        flicker = flicker.astype(np.float32)

        # ---- シミュレーション & 描画 ----
        gs.step(flow_speed=flow_speed)
        field = gs.field

        rgb = fire_emergence(field, intensity=fire_intensity, flicker=flicker,
                             dark_intensity=dark_intensity)

        # 色を黒に寄せる（後半フェーズで徐々に暗くなる）
        if color_dim < 1.0:
            rgb = (rgb.astype(np.float32) * color_dim).astype(np.uint8)

        # ---- 暗渦マスク：RETURN から始まり FADE_OUT で完結 ----
        if phase >= T_RETURN and phase < T_BLACK:
            if phase < T_FADE_OUT:
                # RETURN フェーズ：薄く始まる (0→0.3)
                p_r   = (phase - T_RETURN) / RETURN_SEC
                p_dark = p_r ** 2.0 * 0.3
            else:
                # FADE_OUT フェーズ：0.3→1.0 まで広げる
                p_out  = (phase - T_FADE_OUT) / FADE_OUT_SEC
                p_dark = 0.3 + p_out ** 0.7 * 0.7

            dark_mask = np.clip((p_dark - flicker) / 0.3, 0.0, 1.0)
            rgb = np.clip(
                rgb.astype(np.float32) * (1.0 - dark_mask[:, :, np.newaxis]),
                0, 255
            ).astype(np.uint8)

        rgb = (rgb.astype(np.float32) * brightness).astype(np.uint8)
        disp.show(rgb)

        frame += 1
        if frame % 30 == 0:
            fps     = frame / elapsed if elapsed > 0 else 0
            current = PRESET_ORDER[preset_idx]
            print(f'  fps={fps:.1f}  [{current}]  phase={phase:.1f}s  fire={fire_intensity:.2f}  flow={flow_speed:.2f}', end='\r')

    disp.clear()
    print('\nStopped.')


if __name__ == '__main__':
    main()
