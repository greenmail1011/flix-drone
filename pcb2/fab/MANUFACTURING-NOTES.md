# FutureZebra × Flix 一體板 v2.0.1 製造說明 / Manufacturing Notes

板名 Board：`fz-flix-onboard` v2.0.1 ｜ 廠商 Fab：JLCPCB ｜ 日期 Date：2026-11-19

ESP32 模組、IMU、USB 燒錄、穩壓和 4 路馬達開關全部做在一塊板上，**學生不用焊接**：插電池、插馬達、裝槳就能飛。
ESP32 module, IMU, USB programming, regulator and 4 motor switches on one board. **No soldering for students.**

## 1. 檔案 / Files

| 檔案 File | 用途 Purpose |
| --- | --- |
| `fz-flix-onboard-gerber.zip` | Gerber + 鑽孔（PTH、NPTH，含 USB 外殼長圓孔）/ Gerbers + drills (incl. USB shell slots) |
| `fz-flix-onboard-BOM.csv` | BOM（JLC 格式，20 種料件、43 個元件）|
| `fz-flix-onboard-CPL.csv` | 座標檔 Pick & place（Top only）|
| `fz-flix-onboard-assembly.pdf` | 組裝圖 Assembly drawing |
| `fz-flix-onboard-schematic.pdf` | 原理圖（接線表式）Schematic (net-label table) |

## 2. PCB 規格 / PCB specification

| 項目 Item | 設定 Setting |
| --- | --- |
| 尺寸 Size | **70 × 70 mm（含工藝邊 incl. rails）**；板子本體 46 × 45.5 mm |
| 層數 Layers | 2 |
| 板厚 Thickness | 1.0 mm（1.6 mm 也可以 / 1.6 OK） |
| 銅厚 Copper | 1 oz |
| 最小線寬/線距 Min track/space | 0.15 / 0.15 mm（DRC 最小 0.150 mm） |
| 最小孔 Min drill | 0.30 mm（過孔 via 0.3/0.6，蓋油 tented） |
| 表面處理 Finish | 無鉛噴錫 Lead-free HASL（或沉金 ENIG，IMU 細腳距較好）|
| 防焊/絲印 Mask/silk | 綠/白 Green/White |
| 拼板 Panel | **自己的工藝邊（Panel by customer, 1 design）**，4 個郵票孔連接點；3 個光學點、4 個 1.152 mm 定位孔已在工藝邊上 |
| 訂單號 Order number | 指定位置：工藝邊上的 `JLCJLCJLCJLC` / Specify position (on rail) |

## 3. 貼片 / Assembly

- **標準貼片 Standard PCBA**（ESP32 模組只能用標準貼片 / ESP32 module is "Standard only"），**只貼正面 Top side only**。
- 建議勾選「Confirm Parts Placement」，讓 JLC 工程師確認方向。/ Please select "Confirm Parts Placement".
- 座標檔的旋轉角用 KiCad 慣例；JLC 預覽裡如果方向不對，請以下表為準調整：

| 位號 Ref | 檢查 Check |
| --- | --- |
| U1 ESP32-WROOM-32E | 天線朝板子前方（FRONT 箭頭）。Antenna toward FRONT arrow. |
| U2 ICM-40609-D | 第 1 腳（圓點）在**右下**（看組裝圖紅點）。Pin 1 at bottom-right. |
| U3 CH340C | 第 1 腳在**右上**。Pin 1 at top-right. |
| U4 AP2112K | 第 1 腳（VIN）在左下，5 腳（VOUT）在左上。 |
| Q1–Q7 | 第 3 腳（單獨那一腳）照組裝圖紅點。Pin 3 (single pin) per red dots. |
| D1 B5819W | 陰極（K，有色帶）在**下方**（靠 CH340 那側的下端）。Cathode at bottom. |
| D2 LED | 陰極（K）在**左邊**。Cathode on the left. |
| J1 USB-C | 開口朝**左**板邊。Opening to left edge. |
| J2 PH2.0 | 開口朝**後**（板子下方凸片）。Opening to rear tab. |
| J3–J6 1.25 mm | 開口朝左右板邊。Openings to side edges. |

## 4. 電路重點 / Circuit summary

- 馬達：每顆一個 AO3400A 低側開關，G 接 GPIO、D 接馬達負極、S 接 GND，G–S 10 kΩ 下拉；馬達正極接電池。接腳照 Flix 預設：RL=IO12、RR=IO13、FR=IO14、FL=IO15。
- IMU：ICM-40609-D（Flix 官方 PCB 用的同一顆），SPI：SCK=IO18、MISO=IO19、MOSI=IO23、CS=IO5。
- 電源：電池 → AO3401A（USB 插著時自動關閉）→ VSYS；USB 5V → B5819W → VSYS；VSYS → AP2112K → 3.3V。**只插 USB 時馬達沒有電**（安全）。
- USB：CH340C + 2 顆 MMBT3904 自動燒錄（DTR/RTS → EN/IO0），不用按鍵。
- 電池電壓：100 kΩ/100 kΩ 分壓 → IO33。LED：IO2。

## 5. 品質確認 / Verification done

- 自寫 DRC（精確幾何）：0 錯誤（v2.0.1 加過孔後重跑）；最小間距 0.150 mm、銅到板邊 0.35 mm、孔壁間距 ≥ 0.40 mm。
- 連通檢查：32 個網路全部連通、沒有短路。
- Gerber 用 pygerber 獨立算圖，和設計資料逐像素比對：0 處差異 > 0.1 mm。
- 封裝取自 KiCad 官方元件庫；**板子不是用 KiCad 畫的**（Python 產生、自動佈線），下單前請再看 JLC 線上 Gerber Viewer 和 DFM。
- Not drawn in KiCad (Python-generated, auto-routed). Footprints from the official KiCad library. Please run JLC's online DFM.

## 6. 收到板子後 / Bring-up

1. 折掉工藝邊，用砂紙磨平郵票孔毛邊。
2. **先不插電池**，USB 接電腦：應出現 CH340 序列埠；LED 不會亮（韌體還沒燒）。
3. 用 ESP32 Web Flasher 燒 `flix.esp32.merged.bin`（位址 0），不用按鍵。
4. 在 Flix 主控台設定參數：`p IMU_MODEL 4`、`p PWR_VOLT_PIN 33`、`p PWR_VOLT_LOW 3.5`（`PWR_VOLT_SCALE` 預設 2），重開機後用 `imu` 指令確認 status OK。IMU 轉向和 Flix 預設相同，不用改 `IMU_ROT_*`，但仍要用 QGroundControl 轉動機身確認姿態方向。
5. **確認電池插頭的正負極**和板上 + / − 一致（PH2.0 電池各家正負極不一定一樣，接反會讓 4 顆馬達直接轉）。
6. 拆槳，插電池，用 `mfl`、`mfr`、`mrl`、`mrr` 測四顆馬達的位置和轉向。轉向反了就把該顆馬達插頭的線對調（空心杯馬達的轉向由正負極決定）。

## 7. 電流與壓降 / Current and voltage drop（v2.0.1）

估算條件：Flix 整機約 50–66 g、8520 馬達 + 55 mm 槳、1S 1000 mAh 25C 電池。

| 狀況 | 每顆馬達 | 電池總電流 |
| --- | --- | --- |
| 懸停 Hover | 約 0.8–1.2 A | 約 3–5 A |
| 全油門 Full throttle（短時間）| 約 2–2.5 A | 約 8–10 A（Flix 建議電池能給 15 A）|

- **v2.0.1 補強**：大電流換層點全部改成多個並聯過孔（每個 0.3 mm 過孔約可長時間流 1–1.5 A）。電池正極 → 背面主幹 5 個、每個馬達插座 3 個、左後馬達訊號 2 個；背面 VBAT 橫向分支現在也直接供電給左邊兩顆馬達（v2.0 左邊只靠正面 0.8 mm 細線）。
- **J3–J6 1.25 mm 插座**（相容件額定 1 A）：懸停接近額定、全油門約 2 倍。正版 Molex PicoBlade 2P 用 26/28 AWG 線時是 2.5/2.0 A（溫升 30 °C）。一次飛 5 分鐘以內可接受；插座會溫、會磨耗，壞了換馬達插頭即可。
- **J2 PH2.0 電池插座**（額定 2 A）：懸停就超過 1.5–2.5 倍，是整條電源路徑最弱的一環；壓降約 0.1 V（懸停）～0.3 V（全油門）。和早期 Tiny Whoop 一樣的用法，會溫、接點會慢慢氧化，電池插頭要定期換。
- **3.3 V 穩壓（AP2112K，600 mA 時壓降典型 0.25 V、最大 0.4 V）**：ESP32 規格 3.0–3.6 V。電池在負載下低於約 3.3 V 時 3.3 V 會跟著往下掉；**低電量又全油門**時板上電壓可能掉到約 2.8 V，3.3 V 掉到約 2.65 V，有重開機（brown-out）、空中斷電的風險。
  → 韌體設定 `p PWR_VOLT_LOW 3.5`（Flix 預設 2.7 V 太低），教學上電池到 3.5 V 就降落。

## 8. 已知限制 / Known limitations

- 沒有電池反接保護。/ No reverse-battery protection.
- 1.25 mm 馬達插座、PH2.0 電池插座都在額定以上使用（見第 7 節）。
- 原理圖是接線表式（同名網路相連），不是傳統圖形原理圖。
