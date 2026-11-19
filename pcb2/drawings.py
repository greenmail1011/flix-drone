"""組裝圖與原理圖（網路標籤式）。輸出 PNG、PDF、SVG。"""
import os, math, pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MPoly, Circle
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
import board as B
from route import pad_geom

for f in ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'):
    if os.path.exists(f): font_manager.fontManager.addfont(f)
plt.rcParams['font.family'] = ['Noto Sans CJK TC', 'DejaVu Sans']
plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['pdf.fonttype'] = 42
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fab')
NAME = B.NAME
RED, BLUE, INK, GRY = '#c62828', '#1f5fbf', '#1d1d1f', '#777'

PIN_NAMES = {
    'U1': {'1': 'GND', '2': '3V3', '3': 'EN', '9': 'IO33', '13': 'IO14', '14': 'IO12', '15': 'GND', '16': 'IO13', '23': 'IO15',
           '24': 'IO2', '25': 'IO0', '29': 'IO5', '30': 'IO18', '31': 'IO19', '33': 'IO21', '36': 'IO22', '34': 'RXD0', '35': 'TXD0', '37': 'IO23', '38': 'GND', '39': 'EP'},
    'U2': {'8': 'VDDIO', '9': 'SDO', '11': 'RESV', '13': 'VDD', '18': 'GND', '19': 'FSYNC', '20': 'RESV', '22': 'nCS', '23': 'SCLK', '24': 'SDI'},
    'U3': {'1': 'GND', '2': 'TXD', '3': 'RXD', '4': 'V3', '5': 'UD+', '6': 'UD-', '13': 'DTR#', '14': 'RTS#', '16': 'VCC'},
    'U4': {'1': 'VIN', '2': 'GND', '3': 'EN', '5': 'VOUT'},
    'J1': {'A4': 'VBUS', 'A5': 'CC1', 'B5': 'CC2', 'A6': 'D+', 'A7': 'D-', 'A1': 'GND', 'S1': 'SHIELD'},
    'J2': {'1': 'BAT+', '2': 'BAT-'},
    'Q': {'1': 'G', '2': 'S', '3': 'D'}, 'QN': {'1': 'B', '2': 'E', '3': 'C'},
    'D': {'1': 'K', '2': 'A'}, 'J': {'1': '+', '2': '-'},
}


def pins_of(ref):
    seen, out = set(), []
    for p in B.PADS:
        if p.ref != ref or p.kind == 'npth' or not p.net or p.net.startswith(('NC_', 'MP_')): continue
        key = (p.net, PIN_NAMES.get(ref, {}).get(p.name, p.name))
        if ref == 'J1' and p.name not in PIN_NAMES['J1']: continue
        if key in seen: continue
        seen.add(key); out.append((p.name, p.net))
    return out


def pname(ref, num):
    c = [x for x in B.COMPS if x['ref'] == ref][0]
    if ref in PIN_NAMES: return PIN_NAMES[ref].get(num, num)
    if c['part'] in ('AO3400A', 'AO3401A'): return PIN_NAMES['Q'][num]
    if c['part'] == 'MMBT3904': return PIN_NAMES['QN'][num]
    if c['part'] in ('B5819W', 'LED'): return PIN_NAMES['D'][num]
    if c['part'] == 'PICO2': return PIN_NAMES['J'][num]
    return num


BLOCKS = [  # 標題, 元件, 位置 (x, y) 單位：格
    ('USB-C 與 USB 轉序列', ['J1', 'R5', 'R6', 'U3', 'C10'], (0, 0)),
    ('自動燒錄（DTR/RTS → EN/IO0）', ['Q6', 'Q7', 'R7', 'R8'], (0, 1)),
    ('電源：電池 / USB 切換、3.3V 穩壓', ['J2', 'C1', 'C2', 'Q5', 'R10', 'D1', 'U4', 'C3', 'C4', 'C5'], (1, 0)),
    ('ESP32 模組、擴充 I2C', ['U1', 'R9', 'C6', 'R11', 'R12', 'C11', 'D2', 'R13', 'J7', 'R14', 'R15'], (1, 1)),
    ('IMU（SPI）', ['U2', 'C7', 'C8', 'C9'], (2, 0)),
    ('馬達開關 ×4（低側 N-MOSFET）', ['J3', 'Q1', 'R1', 'J4', 'Q2', 'R2', 'J5', 'Q3', 'R3', 'J6', 'Q4', 'R4'], (2, 1)),
]


def schematic(pdf):
    fig = plt.figure(figsize=(16.54, 11.69))   # A3 橫
    fig.suptitle(f'FutureZebra × Flix 一體板 {B.VERSION} 原理圖（同名網路標籤相連）', fontsize=15, x=0.02, ha='left', y=0.985)
    W, H = 1 / 3, 0.47
    for title, refs, (cx, cy) in BLOCKS:
        x0, y0 = 0.02 + cx * W, 0.5 - cy * H + 0.005
        ax = fig.add_axes([x0, y0 - 0.0, W - 0.03, H - 0.04])
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
        ax.add_patch(Rectangle((0, 0), 10, 10, fill=False, ec=GRY, lw=0.8, ls='--'))
        ax.text(0.2, 9.6, title, fontsize=10.5, weight='bold', va='top')
        # 元件：每個一行
        y = 8.9
        for ref in refs:
            c = [x for x in B.COMPS if x['ref'] == ref][0]
            val = B.PARTS[c['part']][0]
            pins = pins_of(ref)
            ax.text(0.3, y, ref, fontsize=8.5, weight='bold', va='center', family='DejaVu Sans')
            ax.text(1.3, y, val, fontsize=7.2, va='center', color=GRY, family='DejaVu Sans')
            line = '   '.join(f'{pname(ref, n)}→{net}' for n, net in pins)
            # 換行
            words, cur, lines = line.split('   '), '', []
            for w_ in words:
                if len(cur) + len(w_) > 40: lines.append(cur); cur = w_
                else: cur = (cur + '   ' + w_) if cur else w_
            lines.append(cur)
            for k, ln in enumerate(lines):
                ax.text(4.6 if k == 0 else 1.3, y - k * 0.42, ln, fontsize=6.6, va='center', family='DejaVu Sans Mono',
                        color=INK)
            y -= 0.48 + 0.42 * (len(lines) - 1) + 0.1
    fig.text(0.02, 0.004, '馬達接腳照 Flix 韌體預設：RL=IO12、RR=IO13、FR=IO14、FL=IO15；IMU：SCK=IO18、MISO=IO19、MOSI=IO23、CS=IO5；'
             'LED=IO2；電池分壓→IO33（PWR_VOLT_PIN=33、PWR_VOLT_SCALE=2）；IMU_MODEL=4（ICM-40609-D）；擴充 J7 Qwiic：SDA=IO21、SCL=IO22。\n'
             'BT1：電池備用通孔焊墊（+ = VBAT、− = GND，和 J2 並聯，不貼片、不進 BOM）。', fontsize=8.5, color=INK)
    pdf.savefig(fig); fig.savefig(os.path.join(OUT, f'{NAME}-schematic.png'), dpi=110); fig.savefig(os.path.join(OUT, f'{NAME}-schematic.svg'))
    plt.close(fig)


def assembly(pdf, R):
    fig, ax = plt.subplots(figsize=(11.69, 11.69))
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-26, 26); ax.set_ylim(-28.5, 21.5)
    ax.add_patch(MPoly(list(B.BOARD.exterior.coords), closed=True, fc='#eef5ee', ec=INK, lw=1.2))
    for x, y in B.MOUNT_HOLES:
        ax.add_patch(Circle((x, y), B.MOUNT_D / 2, fc='white', ec=INK, lw=0.8))
    for p in B.PADS:
        if p.kind == 'npth': continue
        g = pad_geom(p)
        ax.add_patch(MPoly(list(g.exterior.coords), closed=True, fc='#d9b25a', ec='none'))
    for c in B.COMPS:
        poly = B.COURTS[c['ref']]
        ax.add_patch(MPoly(list(poly.exterior.coords), closed=True, fill=False, ec=BLUE, lw=0.6))
        fs = 7 if c['ref'][0] in 'UJ' else 5.2
        cx, cy = poly.centroid.x, poly.centroid.y
        if c['ref'] == 'U1': cy = 2.0
        ax.text(cx, cy, c['ref'], ha='center', va='center', fontsize=fs, color=BLUE, weight='bold', family='DejaVu Sans')
    # 方向標記：MOSFET 的 D、二極體 K、LED K、IMU 第 1 腳
    for c in B.COMPS:
        mark = {'AO3400A': '3', 'AO3401A': '3', 'MMBT3904': '3', 'B5819W': '1', 'LED': '1', 'IMU': '1', 'CH340C': '1', 'LDO': '1'}.get(c['part'])
        if not mark: continue
        p = [q for q in B.PADS if q.ref == c['ref'] and q.name == mark][0]
        ax.add_patch(Circle((p.x, p.y), 0.22, fc=RED, ec='none'))
    ax.add_patch(MPoly([(0, 20.5), (-1.2, 18.6), (1.2, 18.6)], closed=True, fc=INK))
    ax.text(0, 17.6, 'FRONT（機頭）', ha='center', fontsize=9)
    ax.text(-25.5, -27.8, '紅點：MOSFET/電晶體第 3 腳（D/C）、二極體與 LED 的陰極（K）、IC 第 1 腳。藍框：元件外框。座標原點在板子中心（機身中心）。',
            fontsize=8, color=INK)
    fig.suptitle(f'FutureZebra × Flix 一體板 {B.VERSION} 組裝圖（正面，只有正面有零件）', fontsize=13, x=0.03, ha='left')
    pdf.savefig(fig); fig.savefig(os.path.join(OUT, f'{NAME}-assembly.png'), dpi=130)
    plt.close(fig)


if __name__ == '__main__':
    R = pickle.load(open('/tmp/final.pkl', 'rb'))
    with PdfPages(os.path.join(OUT, f'{NAME}-schematic.pdf')) as pdf: schematic(pdf)
    with PdfPages(os.path.join(OUT, f'{NAME}-assembly.pdf')) as pdf: assembly(pdf, R)
    print('ok')
