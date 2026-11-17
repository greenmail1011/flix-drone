# Rabboni 體感遙控版

手拿 Rabboni 傾斜，控制 Flix 無人機往前後左右飛。無人機硬體和標準版完全一樣。

完整說明（含運作方式圖、步驟、操作對照表、安全機制）：<https://greenmail1011.github.io/flix-drone/#rabboni>

## 快速開始

```bash
pip install bleak pyflix
python rabboni_flix.py --selftest    # 不用硬體，檢查換算公式
python rabboni_flix.py --no-drone    # 只連 Rabboni，練習校正
python rabboni_flix.py               # 電腦連上 Wi-Fi「flix」後正式使用
```

第一次連無人機時，**一定先拆掉螺旋槳**測試。

## 鍵盤

| 按鍵 | 功能 |
| --- | --- |
| A | 解鎖（油門必須是 0） |
| ↑ ↓ 或 W S | 油門加減 |
| 按住 ← → | 原地左轉／右轉 |
| L | 自動降落後上鎖 |
| 空白鍵 | 緊急停止（馬達立刻停） |
| C | 重新校正 |

## 已驗證／未驗證

- 已驗證：校正與傾角換算（`--selftest` 模擬 300 種握法）、按鍵與自動降落邏輯（用假裝置測過）。
- 未驗證：還沒有接真的 Rabboni 和無人機飛過。Rabboni 的藍牙裝置名稱以「RABBONI」搜尋；找不到時用 `--address` 指定。

## 資料來源

- Rabboni 藍牙協定：PyPI 套件 [Rabboni](https://pypi.org/project/Rabboni/) 與 [rabboni-multi-python-sdk](https://pypi.org/project/rabboni-multi-python-sdk/) 的原始碼（資料特徵值 `00001601-…`，前 12 bytes 為加速度、角速度 int16 大端序）。
- Flix 控制：[pyflix](https://github.com/okalachev/flix/tree/master/tools/pyflix)（MIT）的 `set_controls()`、`set_armed()`；斷訊自動降落見韌體 `safety.ino`。
