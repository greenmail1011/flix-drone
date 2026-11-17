// 零件資料與組裝步驟。價格取自交接檔（蝦皮購物車，2026/11/17）。
const sp = (s, i) => `https://shopee.tw/product/${s}/${i}`;
const GH = 'https://github.com/okalachev/flix';

export const PARTS = [
  { id: 'frame', fn: '機身骨架：把所有零件固定在一起，四支機臂把馬達撐開到固定距離，下方的槽放電池。', name: '機身（自印）', en: 'flix-frame-1.1.stl', qty: '1', n: 1, unit: null, status: 'print',
    spec: 'Flix 官方 STL，外框 95.9 × 95.9 × 18 mm。機臂中心距 120 mm（對角）、84.9 mm（相鄰）。',
    note: 'Bambu Lab A1：層高 0.2 mm、線寬 0.4 mm、100% 填充。PLA 估重約 16 g（由 STL 體積 12.9 cm³ 換算，未實秤）。四支馬達管內徑 8.58 mm，要緊配。',
    url: GH },
  { id: 'holder', fn: '把主板架高，讓主板不壓到下面的 IMU。兩側鏤空讓電線從下面穿上來，焊在主板的排針孔。', name: 'ESP32 支架（自印）', en: 'esp32-holder.stl', qty: '1', n: 1, unit: null, status: 'print',
    spec: 'I 字形平台 31 × 39 mm，四根支柱高 9.6 mm，柱底有 M1.4 螺絲孔。',
    note: '兩側鏤空是讓 MINI32 小板的排針孔通過。PLA 估重約 2.1 g。', url: GH },
  { id: 'washer', fn: '把 IMU 墊高 2 mm，讓朝下的晶片不會碰到機身。', name: 'M3 墊片（自印）', en: 'washer-m3.stl', qty: '2', n: 2, unit: null, status: 'print',
    spec: '外徑 5.4 mm、厚 2 mm。', note: '墊在 IMU 與機身之間，讓板子底面的焊點不碰機身。', url: GH },
  { id: 'esp32', fn: '無人機的大腦：讀 IMU 的資料、算出姿態、決定四顆馬達各要轉多快；也負責 Wi-Fi，接收電腦或 Python 程式的指令。', name: 'ESP32 主板', en: 'MINI32（官方尺寸）／NODEMCU-32S（購物車）', qty: '1', n: 1, unit: 140, status: 'cart',
    spec: 'MINI32（MH-ET LIVE MiniKit 同款）：約 31.4 × 39 mm，4 排 × 10 孔，孔距 2.54 mm。本頁照官方照片 esp32.jpg 建模（Micro USB 版；也有 USB-C 版）。購物車放的是 NODEMCU-32S（38 針），放不上官方支架。',
    note: '元件面朝上，用雙面膠貼在支架上；電線從下方穿過支架兩側的鏤空，焊在排針孔。勾選「主板腳位名稱」可以看每個孔的名稱。',
    url: sp(280233910, 11234324986) },
  { id: 'tape2', fn: '把主板黏在支架上，泡棉也能吸收一點震動。', name: '雙面泡棉膠', en: 'double-sided tape', qty: '少量', n: 1, unit: null, status: 'todo',
    spec: '約 1 mm 厚。', note: '貼 ESP32 到支架。', url: '' },
  { id: 'imu', fn: '慣性量測單元，無人機的「平衡感」：陀螺儀量機身轉得多快，加速度計量傾斜（重力方向）。每秒回報約 1000 次。', name: 'IMU：MPU9250 + BMP280', en: '10DOF 模組（GY-91 同款）', qty: '1', n: 1, unit: 250, status: 'cart',
    spec: '機身的孔位是照 GY-91 設計的，孔距 15.24 mm。氣壓計 Flix 目前不使用。',
    note: '用 SPI 接線（不是 I²C），共 6 條線。印字面朝上、晶片朝下（所以要墊片），VIN 端朝機頭、安裝孔在左。照這個方向，韌體參數設 IMU_ROT_ROLL = 3.142、IMU_ROT_PITCH = 0、IMU_ROT_YAW = 1.571，裝好後再用 QGroundControl 確認姿態。',
    url: sp(17188802, 52610555508) },
  { id: 'm3', fn: '把 IMU 鎖牢。IMU 只要會晃，量到的數字就會亂，飛行就不穩。', name: 'M3×5 螺絲', en: '鎖 IMU', qty: '2', n: 2, unit: null, status: 'todo',
    spec: '內六角或十字皆可。', note: '穿過 IMU、墊片，直接鎖進機身的 2.9 mm 孔（塑膠自攻）。不要鎖太緊，PLA 會滑牙。', url: '' },
  { id: 'motors', fn: '把電變成轉動，帶動螺旋槳產生升力。兩顆順時針、兩顆逆時針，扭力互相抵消，機身才不會原地打轉。', name: '8520 空心杯馬達 3.7V', en: 'UCI電子 8520', qty: '4', n: 4, unit: 40, status: 'cart',
    spec: 'Ø8.5 × 20 mm，軸徑 1 mm，白色塑膠尾蓋。官方要求標 3.7V 的款，不要「3.7–6V」寬電壓款。',
    note: '從上方壓入馬達管，馬達線從管壁的開槽拉出。順時針（CW）＝藍紅線、A 槳；逆時針（CCW）＝黑白線、B 槳。',
    url: sp(2305548, 879305527) },
  { id: 'mosfet', fn: '馬達的電子開關。主板的 GPIO 只能輸出很小的電流，推不動馬達；MOSFET 用小訊號控制大電流，每秒開關上萬次（PWM）來調整轉速。', name: 'MOSFET UMW 100N03A', en: 'TO-252', qty: '4', n: 4, unit: null, status: 'todo',
    spec: '每顆馬達一顆。官方註明要 UMW 牌，KIA 等其他牌可能不能用。三隻腳：G（左）、S（右）、D（中間短腳和背面金屬片）。背面那片金屬就是 D 腳，本來是設計來焊在電路板上導熱的，不是另外加裝的散熱片；這台的電流小，不需要散熱片。',
    note: '台灣店家沒查到，LCSC 約 US$0.19／顆。用透明膠帶貼在機臂上。',
    url: 'https://www.lcsc.com/product-detail/MOSFET_UMW-Youtai-Semiconductor-Co-Ltd-100N03A_C668200.html' },
  { id: 'resistor', fn: '下拉電阻：開機或燒錄時 GPIO 還沒設定好，電阻把 MOSFET 的 G 腳拉到 0V，馬達才不會突然轉起來。另外 2 顆可做電池電壓量測（選配）。', name: '10 kΩ 電阻', en: '1/4W，10 顆一包', qty: '1 包（用 6）', n: 1, unit: 10, status: 'cart',
    spec: '4 顆當 MOSFET 下拉電阻，2 顆做電池電壓分壓（選配）。', note: '下拉電阻接在 Gate 與 Source 之間，開機時馬達才不會亂轉。',
    url: sp(139069730, 2269552754) },
  { id: 'tape', fn: '把 MOSFET、電阻和電線固定在機臂上，避免震動把焊點拉斷。', name: '透明膠帶', en: '固定 MOSFET', qty: '少量', n: 1, unit: null, status: 'todo', spec: '', note: '把 MOSFET 和電阻貼在機臂上。', url: '' },
  { id: 'wire', fn: '把電和訊號送到各零件。紅＝正極、黑＝負極（接地）、黃＝訊號。', name: '28 AWG 矽膠線', en: '1585-1614 賣場，紅／黑／黃各 5 m', qty: '3 卷', n: 3, unit: 27, status: 'cart',
    spec: '官方建議 28 AWG。特軟矽膠線，耐熱，焊接時外皮不易縮。', note: '紅接正極、黑接地、黃接訊號。IMU 有 4 條黃色訊號線，焊之前在兩端貼紙膠帶寫上編號，才不會接錯。詳見下方接線表。',
    url: sp(105691234, 2747848722) },
  { id: 'm14', fn: '把支架鎖在機身上。', name: 'M1.4×5 螺絲', en: '鎖支架', qty: '4', n: 4, unit: null, status: 'todo',
    spec: '', note: '從機身底面往上鎖進支架的四根支柱。', url: '' },
  { id: 'battery', fn: '能量來源。1S 鋰聚合物電池 3.7V（充飽 4.2V），要能瞬間放出大電流（25C）給四顆馬達。', name: '1S LiPo 電池（尚未選）', en: '952540 或同尺寸', qty: '1', n: 1, unit: null, status: 'todo',
    spec: '9.5 × 25 × 40 mm，3.7V、1000 mAh 以上，官方建議 25C。',
    note: '機身下方的電池槽內部 26 × 31 × 10 mm，952540 剛好放得進去，兩端各露出約 4.5 mm。只能用 1S。',
    url: '' },
  { id: 'connector', fn: '電池插頭，可以快速拔下電池去充電。紅正黑負，不能插反。', name: 'MX2.0 2P 公母對插線', en: '10 cm', qty: '1', n: 1, unit: 8, status: 'cart',
    spec: '電池接頭。', note: '紅正黑負，極性接反會燒板。', url: sp(280233910, 3160575432) },
  { id: 'props', fn: '轉動時把空氣往下推，產生升力。A、B 槳的扭轉方向相反，要配合馬達轉向。', name: '55 mm 正反槳', en: '天鷹遙控，孔徑 1.0 mm', qty: '1 組（4 支）', n: 1, unit: 60, status: 'cart',
    spec: 'A 槳 2 支、B 槳 2 支。孔徑 1.0 mm 對得上 8520 馬達軸。',
    note: '本頁 A 槳畫成黑色、B 槳畫成白色。前左、後右裝 A；前右、後左裝 B。裝錯一起飛就翻。',
    url: sp(193623894, 29471388129) },
  { id: 'charger', fn: '給電池充電，不裝在飛機上。', name: 'TP4056 充電板 Type-C', en: '外接，不裝在機上', qty: '1', n: 1, unit: 10, status: 'cart',
    spec: '1A，帶保護。', note: '充電用，不裝在機身上，所以 3D 圖裡沒有。', url: sp(280233910, 6564386085) },
];

// ---------- 主板腳位（MINI32 正面＝元件面朝上、天線朝上看）----------
// 來源：MH-ET LIVE MiniKit 腳位（r0oland/ESP32_mini_KiCad_Library 的封裝，與 Flix 官方照片背面絲印一致）
export const MINI_COLS = { LO: -13.97, LI: -11.43, RI: 11.43, RO: 13.97 };
export const COL_NAME = { LO: '左外排', LI: '左內排', RI: '右內排', RO: '右外排' };
export const MINI_PINS = {
  LO: ['GND', 'NC', 'SVN', 'IO35', 'IO33', 'IO34', 'TMS', 'NC', 'SD2', 'CMD'],
  LI: ['RST', 'SVP', 'IO26', 'IO18', 'IO19', 'IO23', 'IO5', '3V3', 'TCK', 'SD3'],
  RI: ['TXD', 'RXD', 'IO22', 'IO21', 'IO17', 'IO16', 'GND', 'VCC', 'TDO', 'SD0'],
  RO: ['GND', 'IO27', 'IO25', 'IO32', 'TDI', 'IO4', 'IO0', 'IO2', 'SD1', 'CLK'],
};
export const PIN_ALIAS = { TMS: 'IO14', TCK: 'IO13', TDI: 'IO12', TDO: 'IO15' };
export const pinY = row => 11.43 - (row - 1) * 2.54;
export const pinName = (col, row) => { const n = MINI_PINS[col][row - 1]; return PIN_ALIAS[n] ? `${PIN_ALIAS[n]}（${n}）` : n; };
export const pinWhere = (col, row) => `${COL_NAME[col]}第 ${row} 孔`;
// GY-91 排針（印字面朝上看，由上到下）
export const IMU_PINS = ['VIN', '3V3', 'GND', 'SCL', 'SDA', 'SDO/SAO', 'NCS', 'CSB'];

// 馬達（機身座標：前 +X、左 +Y；3D 場景裡機頭是 +Y）；GPIO 取自官方 docs/assembly.md
export const MOTORS = [
  { k: 'RL', no: 0, name: '後左', sx: -1, sy: 1, cw: false, gpio: 12, pin: ['RO', 5] },
  { k: 'RR', no: 1, name: '後右', sx: -1, sy: -1, cw: true, gpio: 13, pin: ['LI', 9] },
  { k: 'FR', no: 2, name: '前右', sx: 1, sy: -1, cw: false, gpio: 14, pin: ['LO', 7] },
  { k: 'FL', no: 3, name: '前左', sx: 1, sy: 1, cw: true, gpio: 15, pin: ['RI', 9] },
];
export const motorWires = m => m.cw ? { neg: '藍', pos: '紅', negHex: '#2b6fd6', posHex: '#d62828' } : { neg: '黑', pos: '白', negHex: '#1b1b1b', posHex: '#f2f2f2' };

// ---------- 接線表（3D、接線圖、說明書共用）----------
const Y = '#f2c200', R = '#d62828', K = '#1b1b1b';
const esp = (col, row) => `MINI32 ${pinName(col, row)}（${pinWhere(col, row)}）`;
export const WIRES = [
  { g: 'power', id: 'P1', color: '紅', hex: R, from: '電池插頭（MX2.0 母座）紅線', to: '紅色匯流點', fn: '電池正極進來，在這裡分給主板和 4 顆馬達' },
  { g: 'power', id: 'P2', color: '黑', hex: K, from: '電池插頭（MX2.0 母座）黑線', to: '黑色匯流點', fn: '電池負極進來，在這裡分給主板和 4 顆 MOSFET' },
  { g: 'power', id: 'P3', color: '紅', hex: R, from: '紅色匯流點', to: esp('RI', 8), pin: ['RI', 8], fn: '主板電源。主板上的穩壓 IC 再把電池電壓轉成 3.3V' },
  { g: 'power', id: 'P4', color: '黑', hex: K, from: '黑色匯流點', to: esp('RI', 7), pin: ['RI', 7], fn: '主板接地（GND），所有電路共用的 0V' },
  { g: 'power', id: 'P5', color: '紅 ×4', hex: R, from: '紅色匯流點', to: '4 顆馬達的正極線（白線或紅線），接點套熱縮套管', fn: '馬達的正極直接接電池，開關放在負極那一側' },
  { g: 'power', id: 'P6', color: '黑 ×4', hex: K, from: '黑色匯流點', to: '4 顆 MOSFET 的 S 腳（Source，右邊的腳）', fn: '馬達電流經過 MOSFET 流回電池負極' },
  { g: 'imu', id: 'I1', color: '紅', hex: R, from: 'GY-91 3V3', imu: 1, to: esp('LI', 8), pin: ['LI', 8], fn: 'IMU 的 3.3V 電源（不要接 VIN）' },
  { g: 'imu', id: 'I2', color: '黑', hex: K, from: 'GY-91 GND', imu: 2, to: esp('LO', 1), pin: ['LO', 1], fn: 'IMU 接地' },
  { g: 'imu', id: 'I3', color: '黃 ①', hex: Y, tag: '①', from: 'GY-91 SCL', imu: 3, to: esp('LI', 4), pin: ['LI', 4], fn: 'SPI 時脈（SCK）：主板打拍子，兩邊照著拍子傳資料' },
  { g: 'imu', id: 'I4', color: '黃 ②', hex: Y, tag: '②', from: 'GY-91 SDA', imu: 4, to: esp('LI', 6), pin: ['LI', 6], fn: 'SPI MOSI：主板 → IMU，送出指令' },
  { g: 'imu', id: 'I5', color: '黃 ③', hex: Y, tag: '③', from: 'GY-91 SDO/SAO', imu: 5, to: esp('LI', 5), pin: ['LI', 5], fn: 'SPI MISO：IMU → 主板，回傳角速度和加速度' },
  { g: 'imu', id: 'I6', color: '黃 ④', hex: Y, tag: '④', from: 'GY-91 NCS', imu: 6, to: esp('LI', 7), pin: ['LI', 7], fn: '晶片選擇（CS）：這條線拉低時，IMU 才會回應主板' },
];
MOTORS.forEach(m => {
  const w = motorWires(m), [c, r] = m.pin;
  WIRES.push(
    { g: 'motor', id: `M${m.no}a`, m: m.no, color: '黃', hex: Y, from: esp(c, r), pin: m.pin, to: `${m.name} MOSFET 的 G 腳（Gate，左邊的腳）`, fn: `主板用 PWM 訊號開關 MOSFET，控制${m.name}馬達的轉速` },
    { g: 'motor', id: `M${m.no}b`, m: m.no, color: `${w.neg}（馬達線）`, hex: w.negHex, from: `${m.name}馬達負極（${w.neg}線）`, to: `${m.name} MOSFET 的 D 腳（Drain，背面金屬片）`, fn: 'MOSFET 導通時，馬達電流從這裡流過' },
    { g: 'motor', id: `M${m.no}c`, m: m.no, color: '電阻', hex: '#b08a5b', from: '10 kΩ 電阻一腳', to: `${m.name} MOSFET 的 G 腳；另一腳接 S 腳`, fn: '下拉電阻：主板還沒開機時把 G 拉到 0V，馬達不會亂轉' },
  );
});
export const WIRE_GROUPS = { power: '電源', imu: 'IMU（SPI）', motor: '馬達' };

// 每一步：標題、做法、檢查點、相機（目標點、方向、距離）
export const STEPS = [
  { t: '列印零件', parts: ['frame'],
    how: '用 Bambu Lab A1 印 4 個零件：機身、ESP32 支架、M3 墊片 ×2。層高 0.2 mm、線寬 0.4 mm、100% 填充。機身有懸空的電池槽底板，需要支撐。',
    check: ['四支馬達管內徑約 8.5 mm，馬達壓進去要緊、不會晃', '電池槽底板平整，沒有塌陷', 'IMU 兩個孔、支架四個孔沒有被支撐材堵住'],
    cam: [0, 0, -2, 1.25, 1, 0.9, 290] },
  { t: 'ESP32 貼到支架', parts: ['holder', 'tape2', 'esp32'],
    how: '先在桌上做：雙面泡棉膠貼在支架平台上，主板元件面朝上貼上去。裝上機身後，天線端朝機頭、USB 端朝機尾（和電池插頭同一側）。',
    check: ['板子貼平，不會翹', '四排孔都落在支架兩側的鏤空上方，從下面看得到', '切換到 NODEMCU-32S 看看：大板比支架長 12 mm，排針會撞到支架'],
    cam: [92, 0, 30, 0.35, -1, 1.2, 105] },
  { t: '放上 M3 墊片', parts: ['washer'],
    how: '兩片墊片對準機身中央的兩個 IMU 孔放好。',
    check: ['墊片的孔和機身的孔對齊'],
    cam: [2, 1, 3, 1, -0.9, 1.1, 85] },
  { t: '鎖上 IMU', parts: ['imu', 'm3'],
    how: 'GY-91 印字面朝上（晶片朝下）放在墊片上，VIN 那端朝機頭、安裝孔在左側、排針在右側，兩顆 M3×5 螺絲穿過 IMU 和墊片鎖進機身。這是官方組裝照片和 GY-91 座標圖的裝法。',
    check: ['VIN 端朝機頭（看本頁的「▲ 機頭」箭頭）', 'IMU 平貼、不會轉動，螺絲不要鎖過頭（PLA 會滑牙）', '晶片沒有碰到機身（墊片就是為了這個）'],
    cam: [3, 1, 5, 0.6, -0.9, 1.4, 70] },
  { t: '裝馬達', parts: ['motors'],
    how: '四顆馬達從上方壓進馬達管，馬達線從管壁開槽拉出。前左、後右放藍紅線（順時針）；前右、後左放黑白線（逆時針）。',
    check: ['馬達很緊、手搖不會動（鬆了用小片膠帶墊）', '四顆的位置與線色和標籤一致', '馬達頂面高度一致'],
    cam: [0, 0, 2, 0.35, -1.2, 1.0, 300] },
  { t: 'MOSFET 與下拉電阻', parts: ['mosfet', 'resistor'],
    how: '每支機臂放一顆 MOSFET：背面金屬片（D 腳）朝馬達、兩隻腳朝機身中心，字面朝上。這片金屬是零件本身的 D 腳，不用另外裝散熱片。10 kΩ 電阻跨接在左腳 G 和右腳 S 之間，先焊好。',
    check: ['電阻兩腳分別焊在 G、S，沒有碰到中間的金屬片', '三用電錶量 G–S 之間約 10 kΩ', '四顆方向都一樣：金屬片朝外'],
    cam: [30, 29, 4, -0.25, -1, 1.15, 70] },
  { t: '支架鎖上機身', parts: ['m14'],
    how: '把第 2 步做好的「支架＋主板」放到 IMU 上方，從機身底面往上鎖 4 顆 M1.4×5 螺絲。',
    check: ['支架四根柱子都貼平機身', '支架兩側的鏤空在左右，等一下電線要從這裡穿上去'],
    cam: [0, 0, -4, 0.35, -1, -0.95, 200] },
  { t: '接線①：電源', parts: ['connector', 'wire'], wires: 'power',
    how: '先做兩個匯流點：電池插頭的紅線、主板 VCC 線和 4 條通往馬達正極的紅線，焊在一起套熱縮管；黑線同樣接到主板 GND 和 4 顆 MOSFET 的 S 腳。主板只接右內排第 7 孔（GND）、第 8 孔（VCC）。（這一步主板和支架畫成半透明，才看得到下面的線。）',
    check: ['紅接 VCC（右內排第 8 孔），黑接 GND（右內排第 7 孔）', '馬達正極和紅線的接點都套了熱縮管', '三用電錶量紅、黑匯流點之間沒有短路（不是 0 Ω）'],
    cam: [2, -4, 8, 0.15, -1, 1.25, 120] },
  { t: '接線②：IMU 的 6 條線', parts: ['wire'], wires: 'imu',
    how: 'GY-91 的 3V3、GND、SCL、SDA、SDO/SAO、NCS 共 6 條線接到主板左邊兩排。4 條黃線先貼編號再焊。VIN 和 CSB 不接。（這一步主板和支架畫成半透明，才看得到下面的線。）',
    check: ['3V3 → 左內排第 8 孔，GND → 左外排第 1 孔', '黃①SCL→IO18、②SDA→IO23、③SDO→IO19、④NCS→IO5', 'VIN 不接（接了 3.3V 也不會壞，但沒必要）'],
    cam: [-2, 2, 9, -0.25, -1, 1.15, 95] },
  { t: '接線③：4 組馬達', parts: ['wire', 'tape'], wires: 'motor',
    how: '每支機臂 3 條線：黃線從主板 GPIO 到 MOSFET 的 G；馬達負極（黑或藍）焊到 MOSFET 背面的金屬片 D；馬達正極（白或紅）接紅色匯流點的線。最後用透明膠帶把 MOSFET 和電線貼在機臂上。（這一步主板和支架畫成半透明，才看得到下面的線。）',
    check: ['GPIO12 後左、GPIO13 後右、GPIO14 前右、GPIO15 前左', '馬達負極接 D（背面金屬片），不是接 S', '膠帶貼好，電線不會被槳打到'],
    cam: [0, 0, 6, 0.55, -1, 1.5, 150] },
  { t: '裝電池', parts: ['battery'],
    how: '電池從機尾推進機身下方的電池槽，插上 MX2.0 插頭。先不要裝槳。',
    check: ['電池不會滑出（太鬆可加一圈膠帶）', '插頭紅接紅、黑接黑', '開啟「剖面」可以看到電池在槽內的位置'],
    cam: [0, -12, -4, 0.75, -1.2, -0.3, 190] },
  { t: '燒錄韌體、測轉向', parts: [],
    how: '用 USB 線燒錄 Flix 韌體（見組裝說明書），拔掉 USB、改接電池，再用 mfl、mfr、mrl、mrr 指令逐顆轉動馬達，看轉向是否和箭頭一致。這一步一定不要裝槳。',
    check: ['畫面是從機尾上方往前看，左右和無人機一致', '前左、後右順時針（從上往下看）', '前右、後左逆時針', '轉向反了：對調那顆馬達的兩條線', '插著 USB 時不要轉馬達'],
    cam: [0, 8, 2, 0.12, -1, 1.7, 330] },
  { t: '裝槳，完成', parts: ['props'],
    how: '前左、後右裝 A 槳；前右、後左裝 B 槳。槳孔對準馬達軸壓到底。',
    check: ['A／B 槳的位置正確（本頁 A 黑、B 白）', '槳不碰機身，相鄰兩槳間距約 30 mm', '第一次試飛在空曠室內、繫留或低高度'],
    cam: [0, 0, 2, 1.25, 1, 0.95, 290] },
];
