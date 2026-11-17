# FutureZebra 程控無人機（Flix 路線）

用開源 [Flix](https://github.com/okalachev/flix) 做的 Python 程控無人機：ESP32、8520 空心杯馬達、1S 電池、3D 列印機身。

**3D 組裝教學頁：** 開啟本 repo 的 GitHub Pages（`index.html`）。

- 13 步組裝動畫，每步附做法與檢查清單；接線拆成「電源、IMU 6 條線、4 組馬達」三步
- 機身、支架、墊片使用 Flix 官方 STL 幾何；MINI32、GY-91 照官方照片建模，其他零件依規格書尺寸建模
- 每條電線都接到主板上真實的腳位孔，點電線可看用途；可顯示主板 40 個孔的腳位名稱
- 中文接線圖（`docs/wiring.svg`）與逐條接線表；每個零件都有功能說明
- 剖面、尺寸標註、機身半透明、MINI32／NODEMCU-32S 切換（標出排針與支架衝突處）
- 零件表含蝦皮連結與價格（2026/11/17 快照）

## 重新產生頁面

```bash
cd src
git clone --depth 1 https://github.com/okalachev/flix.git
pip install trimesh
python3 prep.py flix      # 官方 STL → meshes.js
npm install
python3 build.py          # 打包成 src/index.html
cp index.html ../index.html
```

改零件、價格、步驟文字或接線表：編輯 `src/data.js`。接線圖由 `src/wiring.js` 產生。

重新產生 SVG：`cd src && node --input-type=module -e "import {wiringSVG} from './wiring.js'; import fs from 'fs'; fs.writeFileSync('../docs/wiring.svg', wiringSVG())"`

## 授權

- 本 repo 的程式碼由 FutureZebra 撰寫。
- 機身、支架、墊片的幾何來自 Flix（作者 Oleg Kalachev）。Flix repo 沒有 LICENSE 檔，Arduino Project Hub 標示 CC BY-NC；非商業教學以外的用途請先向原作者確認。
- 走線與 IMU 排針朝向為示意；NODEMCU-32S 尺寸與排針列距為估計值。
