# fluid_art

Raspberry Pi 4 + HUB75 64×64 LEDパネル 4枚（2×2 / 128×128px）による数理アート。

反応拡散・流体力学的シミュレーションを段階的に実装する。

## ハードウェア構成

| 項目 | 値 |
|---|---|
| パネル | HUB75 64×64 P3 × 4枚 |
| 配置 | 2×2（chain=4 / U-mapper） |
| 解像度 | 128×128px |
| HAT | Adafruit RGB Matrix HAT |

## 開発ステップ

- [x] Step 1: 表示エンジン + テストパターン（正弦波・干渉）
- [ ] Step 2: 反応拡散（Gray-Scott）
- [ ] Step 3: 色・輝度の演出
- [ ] Step 4: 流れ場（移流）
- [ ] Step 5: 渦注入
- [ ] Step 6: 外部入力（音・センサー）

## 実行方法

```bash
# テストパターン 0: sine_wave
sudo python3 main.py 0

# テストパターン 1: radial_pulse
sudo python3 main.py 1

# テストパターン 2: interference（干渉模様）
sudo python3 main.py 2
```
