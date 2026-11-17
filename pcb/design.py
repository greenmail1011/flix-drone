"""FutureZebra Flix 載板（carrier board）v1.0 — 設計資料。

座標：機身座標，單位 mm，原點在板子中心（= 機身中心），+Y = 機頭，+X = 右，從上往下看（元件面）。
輸出 Gerber 時整體平移 OFF，讓所有座標為正。

電路完全照 Flix 官方接法：每顆馬達一顆 N-MOSFET 低側開關，
G 接 GPIO、D 接馬達負極、S 接電池負極（GND），G–S 之間 10 kΩ 下拉；
馬達正極接電池正極；電池正負接 MINI32 的 VCC、GND。
"""
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union

OFF = (23.0, 26.0)          # 輸出平移：板子左下角 → (0,0)
BOARD_T = 1.0               # 板厚（mm）

# ---------------- 板子外框 ----------------
C = 3.5                     # 外側四角倒角
OUTLINE = [(-23 + C, 19.5), (23 - C, 19.5), (23, 19.5 - C), (23, -19.5 + C), (23 - C, -19.5),
           (7, -19.5), (7, -24.5), (5.5, -26), (-5.5, -26), (-7, -24.5), (-7, -19.5),
           (-23 + C, -19.5), (-23, -19.5 + C), (-23, 19.5 - C)]
BOARD = Polygon(OUTLINE)

ANTENNA_KEEPOUT = box(-15.5, 13.0, 15.5, 19.5)   # MINI32 天線下方：兩面都不鋪銅
MOUNT_HOLES = [(-13.51, 17.5), (13.51, 17.5), (-13.51, -17.5), (13.51, -17.5)]   # 與 ESP32 支架柱腳同位
MOUNT_D = 1.6               # NPTH，M1.4 自攻螺絲穿過

# ---------------- MINI32 排針 ----------------
COLS = {'LO': -13.97, 'LI': -11.43, 'RI': 11.43, 'RO': 13.97}
def pin_xy(col, n):
    return (COLS[col], 11.43 - (n - 1) * 2.54)

MINI_PINS = {
    'LO': ['GND', 'NC', 'SVN', 'IO35', 'IO33', 'IO34', 'IO14', 'NC', 'SD2', 'CMD'],
    'LI': ['RST', 'SVP', 'IO26', 'IO18', 'IO19', 'IO23', 'IO5', '3V3', 'IO13', 'SD3'],
    'RI': ['TXD', 'RXD', 'IO22', 'IO21', 'IO17', 'IO16', 'GND', 'VCC', 'IO15', 'SD0'],
    'RO': ['GND', 'IO27', 'IO25', 'IO32', 'IO12', 'IO4', 'IO0', 'IO2', 'SD1', 'CLK'],
}
# 用到的腳 → 網路名稱
PIN_NET = {
    ('LO', 1): 'GND', ('RI', 7): 'GND', ('RO', 1): 'GND',
    ('RI', 8): 'VBAT',                     # MINI32 VCC ← 電池正極
    ('LI', 8): '3V3',
    ('LI', 4): 'SCK', ('LI', 5): 'MISO', ('LI', 6): 'MOSI', ('LI', 7): 'CS',
    ('RO', 5): 'GATE0', ('LI', 9): 'GATE1', ('LO', 7): 'GATE2', ('RI', 9): 'GATE3',
}

# ---------------- 馬達通道 ----------------
# 編號、位置、轉向、GPIO 照 Flix 官方（交接檔第 4 節）
MOTORS = [
    dict(m=0, name='RL', dir='CCW', gpio=12, side=-1, fr=-1),
    dict(m=1, name='RR', dir='CW',  gpio=13, side=+1, fr=-1),
    dict(m=2, name='FR', dir='CCW', gpio=14, side=+1, fr=+1),
    dict(m=3, name='FL', dir='CW',  gpio=15, side=-1, fr=+1),
]
QX, QY = 18.6, 8.0          # MOSFET 中心 |x|、|y|
for M in MOTORS:
    s, f = M['side'], M['fr']
    M['q'] = (s * QX, f * QY)
    M['rot'] = 0 if f > 0 else 180            # 前方 0°（D 朝前），後方 180°（D 朝後）；D 永遠朝向自己的馬達焊點
    M['r'] = (s * QX, f * (QY - 2.9))         # 10k 電阻（水平擺放）
    M['mneg'] = (s * QX, f * 12.0)            # 馬達負極焊點（接 D）
    M['mpos'] = (s * 21.5, f * 12.0)          # 馬達正極焊點（接 VBAT）

# SOT-23-3（JLC/EasyEDA 0° 方向：1、2 腳在下，3 腳在上）
# AO3400A：1 = G、2 = S、3 = D
SOT_PADS = {'G': (-0.95, -1.0), 'S': (0.95, -1.0), 'D': (0.0, 1.0)}
SOT_PAD = (0.6, 1.3)
R_PADS = {'1': (-0.8, 0.0), '2': (0.8, 0.0)}
R_PAD = (0.85, 0.95)

def rot(p, deg):
    x, y = p
    if deg == 0: return (x, y)
    if deg == 180: return (-x, -y)
    raise ValueError

def q_pad(M, name):
    dx, dy = rot(SOT_PADS[name], M['rot'])
    return (M['q'][0] + dx, M['q'][1] + dy)

def r_pad(M, k):
    dx, dy = R_PADS[k]
    return (M['r'][0] + dx, M['r'][1] + dy)

def r_pad_for(M, which):
    """回傳接 G 或接 S 的那個電阻焊墊座標。"""
    g = q_pad(M, 'G')
    p1, p2 = r_pad(M, '1'), r_pad(M, '2')
    pg = p1 if abs(p1[0] - g[0]) < abs(p2[0] - g[0]) else p2
    ps = p2 if pg is p1 else p1
    return pg if which == 'G' else ps

# ---------------- GY-91（IMU）焊點：6 孔一排 ----------------
GY_X = -5.0
GY_PINS = [('3V3', 6.35), ('GND', 3.81), ('SCL', 1.27), ('SDA', -1.27), ('SDO', -3.81), ('NCS', -6.35)]
GY_NET = {'3V3': '3V3', 'GND': 'GND', 'SCL': 'SCK', 'SDA': 'MOSI', 'SDO': 'MISO', 'NCS': 'CS'}

# ---------------- 電池焊點 ----------------
BAT = {'BAT+': (-2.5, -23.0), 'BAT-': (2.5, -23.0)}

# ---------------- 尺寸規則 ----------------
HDR_DRILL, HDR_PAD = 1.0, 1.7
MOT_DRILL, MOT_PAD = 1.0, 2.0
BAT_DRILL, BAT_PAD = 1.3, 2.6
VIA_DRILL, VIA_PAD = 0.4, 0.7
W_SIG, W_PWR, W_MOT = 0.25, 0.3, 0.8
CLR = 0.2            # 設計最小線距（JLC 能力 0.127）
POUR_CLR = 0.3       # 鋪銅與其他網路的距離
EDGE_CLR = 0.4       # 銅到板邊

# 絲印文字區（不打縫合過孔，字才不會被孔切掉）
SILK_TEXT_ZONES = [box(-12.5, -18.3, 12.5, -16.9), box(-9.5, 9.0, 9.5, 10.3)]
