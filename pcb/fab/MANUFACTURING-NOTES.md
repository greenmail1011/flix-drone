# FutureZebra × Flix 載板 v1.0　製造說明 / Fabrication & Assembly Notes

2026-11-18　聯絡人 Contact：Harry（新竹市無人機創新科技協會）

---

## 1. 檔案清單 / File list

| 檔案 File | 內容 Content |
| --- | --- |
| `fz-flix-carrier-gerber.zip` | Gerber RS-274X + Excellon，直接上傳 JLCPCB / upload as-is |
| ├ `-F_Cu.gtl` / `-B_Cu.gbl` | 上 / 下銅層 Top / bottom copper |
| ├ `-F_Mask.gts` / `-B_Mask.gbs` | 上 / 下防焊 Top / bottom solder mask |
| ├ `-F_Silkscreen.gto` / `-B_Silkscreen.gbo` | 上 / 下絲印 Top / bottom silkscreen |
| ├ `-F_Paste.gtp` | 上鋼網 Top paste (SMT stencil) |
| ├ `-Edge_Cuts.gm1` | 外框 Board outline |
| ├ `-PTH.drl` | 鍍銅孔 Plated holes：0.40 mm ×62（過孔 via）、1.00 mm ×54、1.30 mm ×2 |
| └ `-NPTH.drl` | 非鍍銅孔 Non-plated holes：1.60 mm ×4（安裝孔 mounting） |
| `fz-flix-carrier-BOM.csv` | JLCPCB BOM（Comment, Designator, Footprint, LCSC Part #） |
| `fz-flix-carrier-CPL.csv` | JLCPCB 座標檔 Pick-and-place（Designator, Mid X, Mid Y, Layer, Rotation） |
| `fz-flix-carrier-assembly.pdf` | 組裝圖 Assembly drawing |
| `fz-flix-carrier-schematic.pdf` / `.svg` | 原理圖 Schematic |
| `carrier-posts.stl` | 3D 列印支柱（不是給 PCB 廠的）/ 3D-printed standoff frame (not for the PCB fab) |

座標原點：板子外框左下角，單位 mm。Gerber 格式 4.6、公制。
Origin: lower-left corner of the board outline, millimetres. Gerber format 4.6, metric.

## 2. 板子規格 / Board specification

| 項目 Item | 規格 Value |
| --- | --- |
| 層數 Layers | 2 |
| 材料 Material | FR-4 (TG 135–140) |
| 外形 Size | 46.0 × 45.5 mm（含後方電池焊點凸片 incl. rear tab） |
| 板厚 Thickness | **1.0 mm**（1.6 mm 也可以，只是重 2 g / 1.6 mm also acceptable, +2 g） |
| 銅厚 Copper | 1 oz 內外層 / 1 oz outer |
| 最小線寬 / 線距 Min track / space | 0.25 mm / 0.27 mm（JLC 能力 0.127 / 0.127） |
| 最小鑽孔 Min drill | 0.40 mm（過孔 vias，孔環 0.15 mm） |
| 過孔 Vias | 蓋油 Tented |
| 表面處理 Surface finish | 無鉛噴錫 Lead-free HASL（學生手焊，建議無鉛）|
| 防焊 / 絲印 Mask / silk | 綠 / 白 Green / white（顏色可改 any colour OK）|
| 拼板 Panelization | 不拼板，單片出貨 None, single boards |
| 訂單號 Order number | 放在指定位置：上層絲印 `JLCJLCJLCJLC` / Specify position (top silk) |
| 金手指、半孔、邊緣鍍銅 | 無 None |

## 3. 貼片 / SMT assembly（只有正面 top side only）

| 位號 Designator | 零件 Part | 封裝 Package | LCSC | 類別 |
| --- | --- | --- | --- | --- |
| Q0, Q1, Q2, Q3 | AO3400A N-MOSFET 30 V 5.7 A | SOT-23 | C20917 | JLC 基本零件 Basic |
| R0, R1, R2, R3 | 10 kΩ ±1% 0.1 W | 0603 | C25804 | JLC 基本零件 Basic |

- **MOSFET 方向 / Orientation**：AO3400A 腳位 1 = G、2 = S、3 = D。每顆 Q 的 3 腳（單獨那一腳）都朝向同一角的馬達焊點：Q2、Q3 的 3 腳朝板子前方（FRONT），Q0、Q1 的 3 腳朝後方。絲印在每顆 Q 旁標了 G、S、D。
  Pin 3 (the single pin, Drain) of every Q faces its own motor pads: Q2/Q3 pin 3 toward FRONT, Q0/Q1 pin 3 toward the rear. Silkscreen marks G, S and D next to every Q.
- 座標檔的旋轉角以 JLC/EasyEDA 的 SOT-23 方向為準（0° 時 1、2 腳在下、3 腳在上）。**請在 JLC 的貼片預覽確認 3 腳落在標「D」的焊墊上**；若方向不對，在預覽裡把 Q 轉 180° 即可。
  CPL rotations assume the JLC/EasyEDA SOT-23 orientation (0° = pins 1, 2 at the bottom, pin 3 on top). **Please confirm in the placement preview that pin 3 lands on the pad marked "D"**; if not, rotate Q by 180°.
- 電阻沒有極性 / Resistors are non-polar.
- 其餘焊點（排母、馬達線、電池線、IMU 線）**全部不貼**，由學生手焊。
  All other pads (headers, motor wires, battery wires, IMU wires) are **not assembled** — hand-soldered by students.

## 4. 電路說明 / Circuit

照 Flix 官方接法 / Same as official Flix wiring：每顆馬達一顆低側 N-MOSFET，G 接 ESP32 GPIO（12、13、14、15），D 接馬達負極，S 接電池負極，G–S 之間 10 kΩ 下拉。電池正極同時接 MINI32 的 VCC 和四顆馬達正極。
One low-side N-MOSFET per motor; gate to GPIO 12/13/14/15, drain to motor −, source to battery −, 10 kΩ gate-source pull-down. Battery + feeds MINI32 VCC and all motor +.

- 下層幾乎整面接地鋪銅；上層也鋪接地，靠 59 個縫合過孔連接（每顆 MOSFET 的 S 腳旁各 3 個）。
  Bottom layer is a near-solid ground pour; top ground pour stitched with 59 vias (3 next to each MOSFET source).
- 電源 VBAT 在上層用 1.8～2.0 mm 寬的銅條送到四顆馬達；馬達負極走線 0.8 mm。四顆全開約 8 A 峰值。
  VBAT runs as 1.8–2.0 mm copper bars on top; motor-drain tracks 0.8 mm. ~8 A peak with all four motors.
- MINI32 天線下方（板子前方中央）兩面都不鋪銅。
  No copper on either layer under the MINI32 antenna (front centre).

## 5. 品質確認 / Verification done

- 自寫 DRC：最小線距 0.27 mm、銅到板邊 ≥ 0.40 mm、孔壁間距 ≥ 0.63 mm，0 錯誤。
- 連通檢查：15 個網路各自連成一塊，沒有短路。
- Gerber 用 pygerber 獨立算圖，和設計資料逐像素比對一致（差異 < 0.1 mm）；另用 gerbonara 讀取確認。
- 這塊板子不是用 KiCad 畫的（Python 產生），**下單前請再跑一次 JLC 線上 DFM / Gerber Viewer**。
- Own DRC: min clearance 0.27 mm, copper-to-edge ≥ 0.40 mm, hole-to-hole ≥ 0.63 mm, 0 errors. Connectivity: all 15 nets single-connected, no shorts. Gerbers rendered independently (pygerber, gerbonara) and matched the design pixel-by-pixel. Not made in KiCad — please also run JLC's online DFM / Gerber viewer.

## 6. 學生手焊與測試 / Hand assembly & test

1. 先用三用電表量：BAT+ 對 BAT− 不能短路；每個馬達「−」對 BAT− 不能短路。
2. 焊 4 條 1×10 排母：先把排母插在 MINI32 的排針上，整組放上載板再焊，排母才會正。MINI32 天線朝 FRONT、USB 朝後。
3. GY-91 照原樣鎖在機身上，6 條 28 AWG 線接到載板的 3V3、GND、SCL、SDA、SDO、NCS（VIN、CSB 不接）。
4. 馬達線：白或紅 → +，黑或藍 → −。線從背面插、正面焊。
5. 電池線：紅 → BAT+，黑 → BAT−。
6. **先不插 MINI32**，接電池量 J1 的 RI8（VCC）≈ 3.7～4.2 V、RI7（GND），手摸 MOSFET 不能發熱，再插上 MINI32。
7. 燒錄 Flix 韌體後，**拆槳**用 `mfl`、`mfr`、`mrl`、`mrr` 測四顆馬達。

## 7. 安裝 / Mounting

載板取代原本的 ESP32 支架。先印 `carrier-posts.stl`（PLA、0.2 mm 層高、4 圈牆），用 4 顆 M1.4×5 從機身底面鎖上，再把載板用 4 顆 M1.4×5 鎖在柱子上（總共 8 顆 M1.4×5）。載板的 4 個孔（Ø1.6 mm）和原支架柱腳同位：(±13.51, ±17.5) mm（以機身中心為原點）。
The carrier replaces the original ESP32 holder. Print `carrier-posts.stl`, screw it to the frame from below with 4 × M1.4×5, then screw the board onto the posts with 4 more M1.4×5 (8 in total).
