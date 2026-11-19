"""FutureZebra Flix 一體板 v2.0 — 元件、擺放、網路。

座標：機身座標（mm），原點 = 機身中心，+Y = 機頭，+X = 右，從上往下看（元件面）。
接腳完全照 Flix 韌體預設（classic ESP32）：
  馬達 RL=GPIO12、RR=GPIO13、FR=GPIO14、FL=GPIO15
  IMU SPI：SCK=18、MISO=19、MOSI=23、CS=5（Arduino ESP32 預設 VSPI）
  LED=GPIO2（LED_BUILTIN）
另外：電池分壓（100k/100k）→ GPIO33（PWR_VOLT_PIN=33，PWR_VOLT_SCALE=2）
      IMU 的 INT 腳不接（Flix 對 classic ESP32 預設不用中斷，改用輪詢）
"""
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
from fp import Footprint, place, transform_pts

NAME = 'fz-flix-onboard'
VERSION = 'v2.0.2'
BOARD_T = 1.0

# ---------------- 板子外框（與載板 v1.x 相同外形，後方凸片加長放 USB-C） ----------------
C = 3.5
TAB_W, TAB_Y = 7.5, -26.0
OUTLINE = [(-23 + C, 19.5), (23 - C, 19.5), (23, 19.5 - C), (23, -19.5 + C), (23 - C, -19.5),
           (TAB_W, -19.5), (TAB_W, TAB_Y + 1.5), (TAB_W - 1.5, TAB_Y), (-TAB_W + 1.5, TAB_Y), (-TAB_W, TAB_Y + 1.5),
           (-TAB_W, -19.5), (-23 + C, -19.5), (-23, -19.5 + C), (-23, 19.5 - C)]
BOARD = Polygon(OUTLINE)
MOUNT_HOLES = [(-13.51, 17.5), (13.51, 17.5), (-13.51, -17.5), (13.51, -17.5)]
MOUNT_D = 1.6
MOUNT_KEEP = 1.45        # 安裝孔周圍不放銅的半徑（螺絲頭、支柱）

# ---------------- 元件 ----------------
FP = {
    'ESP32': 'RF_Module.pretty/ESP32-WROOM-32',
    'IMU': 'Sensor_Motion.pretty/InvenSense_QFN-24_3x3mm_P0.4mm',
    'SOIC16': 'Package_SO.pretty/SOIC-16_3.9x9.9mm_P1.27mm',
    'SOT23': 'Package_TO_SOT_SMD.pretty/SOT-23',
    'SOT235': 'Package_TO_SOT_SMD.pretty/SOT-23-5',
    'SOD123': 'Diode_SMD.pretty/D_SOD-123',
    'R0603': 'Resistor_SMD.pretty/R_0603_1608Metric',
    'C0603': 'Capacitor_SMD.pretty/C_0603_1608Metric',
    'C0805': 'Capacitor_SMD.pretty/C_0805_2012Metric',
    'LED0603': 'LED_SMD.pretty/LED_0603_1608Metric',
    'USBC': 'Connector_USB.pretty/USB_C_Receptacle_HRO_TYPE-C-31-M-12',
    'PH2': 'Connector_JST.pretty/JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal',
    'PICO2': 'Connector_Molex.pretty/Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal',
    'SH4': 'Connector_JST.pretty/JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
    'SH4V': 'Connector_JST.pretty/JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical',
    'SOT236': 'Package_TO_SOT_SMD.pretty/SOT-23-6',
    'R0402': 'Resistor_SMD.pretty/R_0402_1005Metric',
}
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
BATPAD_FP = _os.path.join(_HERE, 'fp_custom', 'BatteryPads_THT_P12mm')
FP['L2016'] = _os.path.join(_HERE, 'fp_custom', 'L_Sunlord_WPN2016')   # v2.0.2 升壓電感（自訂封裝）
_cache = {}
def fpobj(k):
    if k not in _cache: _cache[k] = Footprint(FP[k])
    return _cache[k]

# 料件：value、LCSC、封裝名稱（BOM 用）
PARTS = {
    'ESP32': ('ESP32-WROOM-32E-N4', 'C701341', 'SMD,25.5x18mm'),
    'IMU': ('ICM-40609-D', 'C5360621', 'LGA-24(3x3)'),
    'CH340C': ('CH340C', 'C84681', 'SOP-16'),
    'LDO': ('AP2112K-3.3TRG1', 'C51118', 'SOT-23-5'),
    'USBC': ('TYPE-C-31-M-12', 'C165948', 'USB-C-SMD_TYPE-C-31-M-12'),
    'PH2': ('WAFER-PH2.0-2PWB', 'C3029440', 'SMD,P=2.0mm,Right Angle'),
    'PICO2': ('A1251WR-S-2P', 'C225111', 'SMD,P=1.25mm,Right Angle'),
    'SH4': ('SM04B-SRSS-TB(LF)(SN)', 'C160404', 'SMD,P=1mm,Right Angle'),
    'AO3400A': ('AO3400A', 'C20917', 'SOT-23'),
    'AO3401A': ('AO3401A', 'C15127', 'SOT-23'),
    'MMBT3904': ('MMBT3904', 'C20526', 'SOT-23'),
    'B5819W': ('B5819W SL', 'C8598', 'SOD-123'),
    'LED': ('Red LED 0603', 'C2286', '0603'),
    '10k': ('10kΩ ±1% 0603', 'C25804', '0603'),
    '5.1k': ('5.1kΩ ±1% 0603', 'C23186', '0603'),
    '100k': ('100kΩ ±1% 0603', 'C25803', '0603'),
    '22u': ('22uF 25V X5R 0805', 'C45783', '0805'),
    '10u': ('10uF 10V X5R 0603', 'C19702', '0603'),
    '2.2u': ('2.2uF 16V X5R 0603', 'C23630', '0603'),
    '100n': ('100nF 50V X7R 0603', 'C14663', '0603'),
    '10n': ('10nF 50V X7R 0603', 'C57112', '0603'),
    # v2.0.2：J8 感測器插座與 5V 升壓
    'TLV61070A': ('TLV61070ADBVR', 'C6881375', 'SOT-23-6'),
    'L1u': ('WPN201610H1R0MT 1uH', 'C97002', 'SMD,2x1.6mm'),
    'SH4V': ('BM04B-SRSS-TB(LF)(SN)', 'C160390', 'SMD,P=1mm,Vertical'),
    '20k': ('20kΩ ±1% 0402', 'C25765', '0402'),
    '2.2k': ('2.2kΩ ±1% 0402', 'C25879', '0402'),
    '100k-0402': ('100kΩ ±1% 0402', 'C25741', '0402'),
    '1k': ('1kΩ ±1% 0402', 'C11702', '0402'),
}

# (ref, 料件, 封裝, x, y, 旋轉, {焊墊: 網路}, 說明)
COMPS = []
def add(ref, part, fpk, x, y, rot, nets, note=''):
    COMPS.append(dict(ref=ref, part=part, fp=fpk, x=x, y=y, rot=rot, nets=nets, note=note))

# ESP32 模組：天線朝機頭（+Y），底面中心 (0, 3.75)
U1_ORIGIN = (0.0, 3.75)
esp = {'26': 'BOOST_EN', '27': 'RX2', '28': 'TX2', '1': 'GND', '15': 'GND', '38': 'GND', '39': 'GND', '2': '3V3', '3': 'EN', '33': 'SDA', '36': 'SCL',
       '9': 'VSENSE', '13': 'GATE_FR', '14': 'GATE_RL', '16': 'GATE_RR', '23': 'GATE_FL', '24': 'LED',
       '25': 'IO0', '29': 'CS', '30': 'SCK', '31': 'MISO', '34': 'RXD0', '35': 'TXD0', '37': 'MOSI'}
add('U1', 'ESP32', 'ESP32', *U1_ORIGIN, 0, esp, '主控')

# 馬達通道：插座 J（開口朝左右板邊）、MOSFET Q、閘極下拉 R
MOTORS = [  # name, gpio, side, 插座 y, Q 位置, Q 旋轉, R 位置, R 旋轉
    ('FL', 15, -1, 8.8, (-17.4, 15.7), 180, (-21.4, 15.1), 90),
    ('FR', 14, +1, 8.8, (17.4, 15.7), 0, (21.4, 15.1), 90),
    ('RL', 12, -1, -0.8, (-13.5, -3.5), 180, (-10.9, -3.4), 90),
    ('RR', 13, +1, -0.8, (13.5, -3.5), 0, (10.9, -3.4), 90),
]
MOTOR_NO = {'RL': 0, 'RR': 1, 'FR': 2, 'FL': 3}
for (nm, gpio, s, y, qxy, qr, rxy, rr) in MOTORS:
    n = MOTOR_NO[nm]
    add(f'J{3 + n}', 'PICO2', 'PICO2', s * 19.0, y, -90 if s < 0 else 90,
        {'1': 'VBAT', '2': f'MOT_{nm}', 'MP': f'MP_J{3+n}'}, f'馬達 {n}（{nm}）')
    add(f'Q{1 + n}', 'AO3400A', 'SOT23', *qxy, qr, {'1': f'GATE_{nm}', '2': 'GND', '3': f'MOT_{nm}'}, f'馬達 {n} 開關')
    add(f'R{1 + n}', '10k', 'R0603', *rxy, rr, {'1': f'GATE_{nm}', '2': 'GND'}, f'馬達 {n} 閘極下拉')

# IMU：模組右側中段（靠近 SPI 腳位，也比較靠近機身中心）。轉 180°：晶片 +X 朝左（機身 +Y），和 Flix 預設 IMU_ROT_YAW = π/2 相同
IMU_XY = (12.6, 3.0)
add('U2', 'IMU', 'IMU', IMU_XY[0], IMU_XY[1], 180,
    {'8': '3V3', '9': 'MISO', '11': 'GND', '13': '3V3', '18': 'GND', '19': 'GND', '20': 'GND',
     '22': 'CS', '23': 'SCK', '24': 'MOSI'}, 'IMU')
add('C7', '100n', 'C0603', 12.6, 8.1, 0, {'1': '3V3', '2': 'GND'}, 'IMU VDD')
add('C8', '2.2u', 'C0603', 12.6, 9.7, 0, {'1': '3V3', '2': 'GND'}, 'IMU VDD')
add('C9', '10n', 'C0603', 12.6, 6.5, 180, {'1': '3V3', '2': 'GND'}, 'IMU VDDIO')
add('C2', '22u', 'C0805', 12.6, 11.8, 0, {'1': 'VBAT', '2': 'GND'}, '前方馬達旁')

# 電池插座：後方凸片，開口朝後
add('J2', 'PH2', 'PH2', 0.0, TAB_Y + 4.6 + 0.35, 0, {'1': 'VBAT', '2': 'GND', 'MP': 'MP_J2'}, '電池')
add('C1', '22u', 'C0805', 6.0, -17.6, 90, {'1': 'VBAT', '2': 'GND'}, '電池旁')

# USB-C：左側後方，開口朝左
add('J1', 'USBC', 'USBC', -23.0 + 3.65 + 0.1, -11.0, -90,
    {'A1': 'GND', 'B1': 'GND', 'A12': 'GND', 'B12': 'GND', 'A4': 'VBUS', 'B4': 'VBUS', 'A9': 'VBUS', 'B9': 'VBUS',
     'A5': 'CC1', 'B5': 'CC2', 'A6': 'DP', 'B6': 'DP', 'A7': 'DM', 'B7': 'DM', 'S1': 'GND'}, 'USB-C 燒錄')
add('R5', '5.1k', 'R0603', -12.5, -7.55, 90, {'1': 'CC1', '2': 'GND'}, 'CC1')
add('R6', '5.1k', 'R0603', -12.45, -14.6, 0, {'1': 'CC2', '2': 'GND'}, 'CC2')

# CH340C：USB 右邊（橫放）與自動燒錄電路
add('U3', 'CH340C', 'SOIC16', -4.2, -11.2, 270,
    {'1': 'GND', '2': 'RXD0', '3': 'TXD0', '4': '3V3', '5': 'DP', '6': 'DM', '13': 'DTR', '14': 'RTS', '16': '3V3'},
    'USB 轉序列')
add('C10', '100n', 'C0603', 1.75, -14.4, 90, {'1': '3V3', '2': 'GND'}, 'CH340 VCC')
add('Q6', 'MMBT3904', 'SOT23', 4.2, -9.4, 0, {'1': 'Q6B', '2': 'RTS', '3': 'EN'}, '自動重置（EN）')
add('Q7', 'MMBT3904', 'SOT23', 4.2, -13.0, 0, {'1': 'Q7B', '2': 'DTR', '3': 'IO0'}, '自動進燒錄（IO0）')
# v2.0.2：R7、R8 往左移 0.75 mm、R8 往上 0.4 mm，讓出 J8 的位置
add('R7', '10k', 'R0603', 6.65, -9.4, 90, {'1': 'DTR', '2': 'Q6B'}, 'Q6 基極')
add('R8', '10k', 'R0603', 6.65, -12.6, 90, {'1': 'RTS', '2': 'Q7B'}, 'Q7 基極')

# 電源切換：電池/USB → VSYS（左後方，USB 與電池之間）
add('Q5', 'AO3401A', 'SOT23', -10.3, -17.7, 0, {'1': 'VBUS', '2': 'VSYS', '3': 'VBAT'}, '電池/USB 切換')
add('D1', 'B5819W', 'SOD123', -12.5, -11.4, 90, {'1': 'VSYS', '2': 'VBUS'}, 'USB → VSYS')
add('R10', '100k', 'R0603', -7.0, -15.75, 0, {'1': 'VBUS', '2': 'GND'}, 'Q5 閘極下拉')

# 模組左側：3.3V 穩壓、去耦、EN、電池電壓偵測
X_L = -11.6
add('U4', 'LDO', 'SOT235', X_L, 11.55, 90, {'1': 'VSYS', '2': 'GND', '3': 'VSYS', '5': '3V3'}, '3.3V 穩壓')
add('C3', '10u', 'C0603', -14.2, 11.5, 90, {'1': 'VSYS', '2': 'GND'}, '穩壓輸入')
add('C4', '22u', 'C0805', X_L, 5.45, 0, {'1': '3V3', '2': 'GND'}, '穩壓輸出')
add('C5', '100n', 'C0603', X_L, 3.7, 0, {'1': '3V3', '2': 'GND'}, 'ESP32 3V3')
add('R9', '10k', 'R0603', X_L, 8.7, 0, {'1': '3V3', '2': 'EN'}, 'EN 上拉')
add('C6', '2.2u', 'C0603', X_L, 7.2, 180, {'1': 'EN', '2': 'GND'}, 'EN 延遲')
add('R11', '100k', 'R0603', X_L, 2.1, 0, {'1': 'VBAT', '2': 'VSENSE'}, '分壓上')
add('R12', '100k', 'R0603', X_L, 0.55, 0, {'1': 'VSENSE', '2': 'GND'}, '分壓下')
add('C11', '100n', 'C0603', X_L, -1.0, 0, {'1': 'VSENSE', '2': 'GND'}, '分壓濾波')

# LED（GPIO2）：右後方，靠近板邊
add('D2', 'LED', 'LED0603', 17.0, -17.6, 0, {'1': 'GND', '2': 'LEDA'}, '狀態燈')
add('R13', '5.1k', 'R0603', 17.0, -16.0, 0, {'1': 'LED', '2': 'LEDA'}, 'LED 限流')

# 擴充插座（v2.0.1）：JST SH 1.0 mm 4P，Qwiic / STEMMA QT 腳位（1 GND、2 3V3、3 SDA、4 SCL），右側板邊、開口朝右
# IO21 = SDA、IO22 = SCL；也可在韌體改成 UART 給光流模組用。上拉 5.1 kΩ（和 R13 同料）
add('J7', 'SH4', 'SH4', 19.3, -9.9, 90, {'1': 'GND', '2': '3V3', '3': 'SDA', '4': 'SCL', 'MP': 'MP_J7'}, '擴充 I2C（Qwiic）')
add('R14', '5.1k', 'R0603', 20.3, -14.9, 0, {'1': '3V3', '2': 'SDA'}, 'SDA 上拉')
add('R15', '5.1k', 'R0603', 20.3, -16.4, 0, {'1': '3V3', '2': 'SCL'}, 'SCL 上拉')

# 感測器插座 J8（v2.0.2）：JST SH 1.0 mm 4P 立式（BM04B），右後方、四個板邊都滿了所以用立式。
# 腳位 1 GND、2 5V、3 TX（IO17 經 R19 1k）、4 RX（IO16 經 R20 1k）——和 MicoAir MTF-01/02 的 GND、5V、Rx、Tx 一對一直通。
# 轉 90°：訊號腳朝右（+X），1 號腳在最下面（靠安裝孔），固定腳在左邊。
J8_XY = (10.0, -15.22)
add('J8', 'SH4V', 'SH4V', *J8_XY, 90, {'1': 'GND', '2': '5V', '3': 'TX2_J', '4': 'RX2_J', 'MP': 'MP_J8'}, '感測器 UART＋5V')
add('R19', '1k', 'R0402', 13.55, J8_XY[1] + 0.5, 0, {'1': 'TX2_J', '2': 'TX2'}, 'TX 串聯保護')
add('R20', '1k', 'R0402', 13.55, J8_XY[1] + 1.5, 0, {'1': 'RX2_J', '2': 'RX2'}, 'RX 串聯保護')

# 5V 升壓（v2.0.2）：TI TLV61070A，VIN 接 VSYS（只插 USB 也能測），EN = IO4（R18 下拉，開機預設關）。
# Vout = 0.5 V ×（1 + 20k / 2.2k）= 5.05 V。轉 270°：上排 EN、GND、SW；下排 FB、VOUT、VIN。
add('U5', 'TLV61070A', 'SOT236', 11.9, -7.3, 270,
    {'1': 'SW5', '2': 'GND', '3': 'BOOST_EN', '4': 'FB5', '5': '5V', '6': 'VSYS'}, '5V 升壓')
add('L1', 'L1u', 'L2016', 14.85, -7.3, 90, {'1': 'VSYS', '2': 'SW5'}, '升壓電感 1 µH')
add('C12', '10u', 'C0603', 14.85, -10.1, 270, {'1': 'VSYS', '2': 'GND'}, '升壓輸入')
add('C13', '22u', 'C0805', 11.9, -10.33, 0, {'1': '5V', '2': 'GND'}, '升壓輸出')
add('R18', '100k-0402', 'R0402', 9.25, -7.3, 180, {'1': 'BOOST_EN', '2': 'GND'}, 'EN 下拉')
add('R17', '2.2k', 'R0402', 9.25, -8.45, 180, {'1': 'FB5', '2': 'GND'}, 'FB 下')
add('R16', '20k', 'R0402', 9.25, -9.6, 180, {'1': 'FB5', '2': '5V'}, 'FB 上')


def build():
    pads, courts, fabs = [], {}, {}
    for c in COMPS:
        f = fpobj(c['fp'])
        ps = place(f, c['ref'], c['x'], c['y'], c['rot'], c['nets'])
        pads += ps
        cy = [p for seg in f.courtyard for p in seg]
        if cy:
            xs, ys = [p[0] for p in cy], [p[1] for p in cy]
            if c['fp'] == 'ESP32':   # 模組外框（不含天線禁區）
                poly = Polygon(transform_pts([(-9.75, -10.5), (9.75, -10.5), (9.75, 15.745), (-9.75, 15.745)], c['x'], c['y'], c['rot']))
            else:
                poly = Polygon(transform_pts([(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))], c['x'], c['y'], c['rot']))
            courts[c['ref']] = poly
        fabs[c['ref']] = [transform_pts(seg, c['x'], c['y'], c['rot']) for seg in f.fab]
    return pads, courts, fabs


PADS, COURTS, FABS = build()

# 電池備用焊墊（v2.0.1，不貼片、不進 BOM）：後方凸片兩側通孔，左 + 右 −，和 J2 並聯。
# 平常不用；PH2.0 壓降太大時可焊 BT2.0／XT30 電池線（拔掉 PH2.0 電池，不要兩個同時接）。
BATPAD_XY = (0.0, -23.0)
PADS += place(Footprint(BATPAD_FP), 'BT1', BATPAD_XY[0], BATPAD_XY[1], 0, {'1': 'VBAT', '2': 'GND'})

# 天線下方：兩面都不放銅（模組天線區 + 往外 1 mm）
ANT_KEEPOUT = box(-14.5, U1_ORIGIN[1] + 9.97, 14.5, 25)

NETS = sorted({p.net for p in PADS if p.net and not p.net.startswith('NC_') and not p.net.startswith('MP_')})

if __name__ == '__main__':
    import itertools
    print(len(COMPS), '個元件', len(PADS), '個焊墊', len(NETS), '個網路')
    bad = 0
    for (a, pa), (b, pb) in itertools.combinations(COURTS.items(), 2):
        if pa.intersection(pb).area > 0.01:
            print('重疊', a, b, round(pa.intersection(pb).area, 2)); bad += 1
    for r, p in COURTS.items():
        if not p.within(BOARD.buffer(0.01)) and r not in ('J1', 'J2', 'J3', 'J4', 'J5', 'J6'):
            print('超出板框', r, round(p.difference(BOARD).area, 2))
    from shapely import affinity
    for x, y in MOUNT_HOLES:
        h = Point(x, y).buffer(MOUNT_KEEP)
        for p in PADS:
            g = affinity.translate(affinity.rotate(box(-p.w/2, -p.h/2, p.w/2, p.h/2), p.rot, origin=(0, 0)), p.x, p.y)
            if g.intersects(h): print('焊墊壓到安裝孔', p.ref, p.name, (x, y))
    for p in PADS:
        g = affinity.translate(affinity.rotate(box(-p.w/2, -p.h/2, p.w/2, p.h/2), p.rot, origin=(0, 0)), p.x, p.y)
        if not g.within(BOARD.buffer(-0.3)): print('焊墊太靠板邊', p.ref, p.name)
    from collections import Counter
    cnt = Counter(p.net for p in PADS if p.net)
    for n in NETS:
        if cnt[n] < 2: print('只有一個焊墊的網路', n)
    print('重疊', bad)
