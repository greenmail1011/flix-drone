# FutureZebra × Flix 一體板 v2.0.2 製造說明 / Manufacturing Notes

板名 Board：`fz-flix-onboard` v2.0.2 ｜ 廠商 Fab：JLCPCB ｜ 日期 Date：2026-11-20 ｜ 收貨地 Ship to：台灣新竹 Hsinchu, Taiwan

ESP32 模組、IMU、USB 燒錄、穩壓和 4 路馬達開關全部做在一塊板上，**學生不用焊接**：插電池、插馬達、裝槳就能飛。
ESP32 module, IMU, USB programming, regulator and 4 motor switches on one board. **No soldering for students.**

**v2.0.2 變更 / Changes**：新增感測器插座 J8（JST SH 1.0 mm 4P 立式，UART＋可開關的 5V，給 MicoAir MTF-02 光流測距模組用）、5V 升壓 U5（TI TLV61070A）與 L1、C12、C13、R16–R18，以及 TX/RX 串聯保護電阻 R19、R20（1 kΩ）。R7、R8 往左移 0.75 mm 讓位置。大電流補強過孔改在訊號線佈線之前放（數量和 v2.0.1 相同）。
Added sensor connector J8 (UART + switchable 5 V boost) with series 1 kΩ protection on TX/RX.

## 1. 檔案 / Files

| 檔案 File | 用途 Purpose |
| --- | --- |
| `fz-flix-onboard-gerber.zip` | Gerber + 鑽孔（PTH、NPTH，含 USB 外殼長圓孔）/ Gerbers + drills (incl. USB shell slots) |
| `fz-flix-onboard-BOM.csv` | BOM（JLC 格式，28 種料件、56 個元件）|
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
| J7 JST SH 4P | 開口朝**右**板邊。Opening to right edge. |
| **U5 TLV61070A**（v2.0.2，SOT-23-6）| 第 1 腳（SW）在**右上**，靠 L1；看組裝圖紅點。Pin 1 (SW) at top-right, next to L1. |
| **L1 1 µH**（v2.0.2，2016）| 無極性；兩個焊墊上下排列，在 U5 右邊。Non-polar, pads above/below each other, right of U5. |
| **J8 JST SH 4P 立式**（v2.0.2，BM04B）| **直立式**，插頭從上往下插。4 支訊號腳朝**右**、兩個固定腳大焊墊在**左**；第 1 腳在**最下面**（靠右後安裝孔，組裝圖紅點）。Vertical; signal pins face right, pin 1 at the bottom (next to the rear-right mounting hole). |
| R16–R20（v2.0.2，0402）| 無極性。Non-polar. |
| BT1 | 通孔焊墊，**不貼片**（不在 BOM／座標檔）。Plain PTH pads, not assembled. |

## 4. 電路重點 / Circuit summary

- 馬達：每顆一個 AO3400A 低側開關，G 接 GPIO、D 接馬達負極、S 接 GND，G–S 10 kΩ 下拉；馬達正極接電池。接腳照 Flix 預設：RL=IO12、RR=IO13、FR=IO14、FL=IO15。
- IMU：ICM-40609-D（Flix 官方 PCB 用的同一顆），SPI：SCK=IO18、MISO=IO19、MOSI=IO23、CS=IO5。
- 電源：電池 → AO3401A（USB 插著時自動關閉）→ VSYS；USB 5V → B5819W → VSYS；VSYS → AP2112K → 3.3V。**只插 USB 時馬達沒有電**（安全）。
- USB：CH340C + 2 顆 MMBT3904 自動燒錄（DTR/RTS → EN/IO0），不用按鍵。
- 電池電壓：100 kΩ/100 kΩ 分壓 → IO33。LED：IO2。
- 擴充 J7（v2.0.1）：JST SH 1.0 mm 4P，Qwiic 腳位 1 GND、2 3V3、3 SDA（IO21）、4 SCL（IO22），R14/R15 5.1 kΩ 上拉。
- 電池備用焊墊 BT1（v2.0.1）：後方凸片兩側 Ø0.9 mm 通孔（左 + VBAT、右 − GND），和 J2 並聯，給 BT2.0／XT30 電池線用。
- **感測器插座 J8（v2.0.2）**：JST SH 1.0 mm 4P 立式（BM04B-SRSS-TB），腳位 **1 GND、2 5V、3 TX（IO17 經 R19 1 kΩ）、4 RX（IO16 經 R20 1 kΩ）**，和 MicoAir MTF-01／MTF-02 的 GND、5V、Rx、Tx 一對一直通（TX/RX 已在板上交叉）。1 kΩ 串聯電阻在接錯線、靜電時保護 ESP32 腳位。
- **5V 升壓（v2.0.2）**：U5 TLV61070A，VIN 接 VSYS（只插 USB 也能測感測器），L1 1 µH（Sunlord WPN201610H，Isat 3.85 A），C12 10 µF 輸入、C13 22 µF 輸出；Vout = 0.5 V ×（1 + 20 k / 2.2 k）= **5.05 V**（最差 4.81～5.29 V，低於 5.5 V 過壓保護）。**EN = IO4**，R18 100 kΩ 下拉：開機與燒錄時 5V 是關的，韌體把 IO4 拉高才有電；關閉時輸出和輸入真正斷開。輸出有短路保護。
- IO16／IO17 只有 ESP32-WROOM-32E-**N4**（沒有 PSRAM）可以用，**不要換成 WROVER**。

## 5. 品質確認 / Verification done

- 自寫 DRC（精確幾何）：0 錯誤（v2.0.2 重新佈線後重跑）；最小間距 0.163 mm、銅到板邊 0.35 mm、孔壁間距 ≥ 0.40 mm。
- 連通檢查：42 個網路全部連通、沒有短路。
- 擺放檢查：56 個元件外框（courtyard）沒有重疊、焊墊都離安裝孔 1.45 mm 以上、離板邊 0.3 mm 以上。
- Gerber 用 pygerber 獨立算圖，和設計資料逐像素比對（v2.0.2 起用 50 px/mm）：0 處差異 > 0.08 mm。
- v2.0.2 新料件（U5、L1、R16–R20、J8）的 LCSC 料號、TLV61070A 腳位（1 SW、2 GND、3 EN、4 FB、5 VOUT、6 VIN）都對過原廠／JLC 資料。
- 封裝取自 KiCad 官方元件庫；**板子不是用 KiCad 畫的**（Python 產生、自動佈線），下單前請再看 JLC 線上 Gerber Viewer 和 DFM。
- Not drawn in KiCad (Python-generated, auto-routed). Footprints from the official KiCad library. Please run JLC's online DFM.

## 6. 收到板子後 / Bring-up

1. 折掉工藝邊，用砂紙磨平郵票孔毛邊。
2. **先不插電池**，USB 接電腦：應出現 CH340 序列埠；LED 不會亮（韌體還沒燒）。
3. 用 ESP32 Web Flasher 燒 `flix.esp32.merged.bin`（位址 0），不用按鍵。
4. 在 Flix 主控台設定參數：`p IMU_MODEL 4`、`p PWR_VOLT_PIN 33`、`p PWR_VOLT_LOW 3.5`（`PWR_VOLT_SCALE` 預設 2），重開機後用 `imu` 指令確認 status OK。IMU 轉向和 Flix 預設相同，不用改 `IMU_ROT_*`，但仍要用 QGroundControl 轉動機身確認姿態方向。
5. **確認電池插頭的正負極**和板上 + / − 一致（PH2.0 電池各家正負極不一定一樣，接反會讓 4 顆馬達直接轉）。**PH2.0 插座和 BT1 備用焊墊只能用一個**，不要同時接兩顆電池。
6. 拆槳，插電池，用 `mfl`、`mfr`、`mrl`、`mrr` 測四顆馬達的位置和轉向。轉向反了就把該顆馬達插頭的線對調（空心杯馬達的轉向由正負極決定）。
7. **J8 感測器插座（v2.0.2）**：見第 7 節的 5V 與附線檢查。Flix 韌體目前還沒用到 UART2／IO4，**平常 J8 沒有電**是正常的。

## 7. 打樣測試清單 / Prototype test checklist（v2.0.2）

第一批 5 片收到後，**至少 2 片**照下表測過再給學生用。溫度用紅外線溫度計或熱電偶，室溫記下來。

| # | 項目 Item | 做法 How | 合格 Pass |
| --- | --- | --- | --- |
| 1 | 電池插座 J2（PH2.0）溫度 | 裝槳、滿電，懸停 **1 分鐘**後馬上量插座外殼 | ≤ 60 °C；插頭不鬆、不變色 |
| 2 | 馬達插座 J3–J6 溫度 | 綁住機身（或拆槳＋負載），**全油門 30 秒**，量最熱的一個 | ≤ 60 °C；塑膠不軟化 |
| 3 | USB-C 外殼固定腳焊接 | 放大鏡看四個外殼腳（通孔）都有吃錫；插拔 20 次 | 外殼不晃、焊點不裂 |
| 4 | 5V 輸出電壓 | 燒測試程式（下方）把 IO4 拉高，量 J8 第 2 腳對第 1 腳；分別在「只插 USB」「只插電池」兩種情況量 | **4.8～5.3 V** |
| 5 | 5V 關閉 | IO4 拉低（或剛開機、燒錄中） | J8 第 2 腳 **0 V**（< 0.1 V） |
| 6 | 5V 短路保護 | IO4 拉高，用電流表把 J8 第 2 腳短到第 1 腳 **2 秒** | 電流被限制（約 0.2 A 以下）、ESP32 不重開機；拿掉短路後 5V 自動恢復 |
| 7 | MTF-02 附線 | 拿到模組後，用三用電表量附線兩端的 1 號腳是否相通（直通線） | 直通：1↔1、2↔2、3↔3、4↔4。**如果是反接線（1↔4），不能直接插**，要換直通線 |
| 8 | J8 通訊 | 接上 MTF-02，IO4 拉高，讀 Serial2 | 模組的燈亮，Serial2 收得到資料 |
| 9 | 升壓溫度 | 接 MTF-02 開 5 分鐘，量 U5、L1 | ≤ 50 °C |

測試程式（Arduino，ESP32 Dev Module；測完再燒回 Flix）：

```
void setup() {
  Serial.begin(115200);
  pinMode(4, OUTPUT); digitalWrite(4, HIGH);          // 打開 J8 的 5V
  Serial2.begin(115200, SERIAL_8N1, 16, 17);         // RX = IO16、TX = IO17
}
void loop() {
  while (Serial2.available()) Serial.printf("%02X ", Serial2.read());
}
```

鮑率依 MTF-02 的設定改（看模組說明書）；收到亂碼也代表線路通了，只是鮑率不對。

## 8. 電流與壓降 / Current and voltage drop（v2.0.1，v2.0.2 不變）

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
- 如果實測 PH2.0 壓降太大：拔掉 PH2.0 電池，在 BT1 焊 BT2.0（連續 9 A）或 XT30（15 A）電池線，不用重做板子。
- J8 的 5V（v2.0.2）：MTF-02 約 40 mA，從 VSYS 抽約 65 mA，對電池可以忽略。

## 9. 已知限制 / Known limitations

- 沒有電池反接保護。/ No reverse-battery protection.
- 1.25 mm 馬達插座、PH2.0 電池插座都在額定以上使用（見第 7 節）。
- 原理圖是接線表式（同名網路相連），不是傳統圖形原理圖。
- J8 的 5V 是給小型感測器用的（MTF-02 約 40 mA），**不要接馬達、舵機或燈條**。
- Flix 韌體目前沒有用 UART2，定高功能要另外寫（之後的工作）。
