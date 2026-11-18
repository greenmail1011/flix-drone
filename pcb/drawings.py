"""原理圖與組裝圖（matplotlib 畫，輸出 SVG / PDF / PNG）。"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon as MPoly
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
from PIL import Image
from design import *

for f in ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'):
    font_manager.fontManager.addfont(f)
plt.rcParams['font.family'] = ['Noto Sans CJK TC', 'DejaVu Sans']
plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['pdf.fonttype'] = 42

OUT = os.path.join(os.path.dirname(__file__), 'fab')
PRE = os.path.join(os.path.dirname(__file__), 'preview')
INK, RED, BLUE, GRN, GRY = '#1d1d1f', '#c62828', '#1f5fbf', '#2e7d32', '#666'

# ======================= 原理圖 =======================
def netlabel(ax, x, y, name, side='r', color=BLUE):
    w = 0.12 * len(name) + 0.3
    if side == 'r':
        pts = [(x, y), (x + 0.2, y + 0.18), (x + 0.2 + w, y + 0.18), (x + 0.2 + w, y - 0.18), (x + 0.2, y - 0.18)]
        tx = x + 0.2 + w / 2
    else:
        pts = [(x, y), (x - 0.2, y + 0.18), (x - 0.2 - w, y + 0.18), (x - 0.2 - w, y - 0.18), (x - 0.2, y - 0.18)]
        tx = x - 0.2 - w / 2
    ax.add_patch(MPoly(pts, closed=True, fill=False, ec=color, lw=1))
    ax.text(tx, y, name, ha='center', va='center', fontsize=7.5, color=color, family='DejaVu Sans')

def gnd(ax, x, y):
    ax.plot([x, x], [y, y - 0.25], color=INK, lw=1.2)
    for i, w in enumerate((0.3, 0.2, 0.1)):
        ax.plot([x - w, x + w], [y - 0.25 - i * 0.09] * 2, color=INK, lw=1.2)

def vbat(ax, x, y):
    ax.plot([x, x], [y, y + 0.25], color=RED, lw=1.2)
    ax.plot([x - 0.25, x + 0.25], [y + 0.25] * 2, color=RED, lw=1.6)
    ax.text(x, y + 0.42, 'VBAT', ha='center', fontsize=7, color=RED, family='DejaVu Sans')

def resistor(ax, x, y0, y1, label):
    ym = (y0 + y1) / 2
    ax.plot([x, x], [y0, ym + 0.35], color=INK, lw=1.2)
    ax.plot([x, x], [ym - 0.35, y1], color=INK, lw=1.2)
    ax.add_patch(Rectangle((x - 0.12, ym - 0.35), 0.24, 0.7, fill=False, ec=INK, lw=1.2))
    ax.text(x + 0.22, ym, label, va='center', fontsize=7.5, family='DejaVu Sans')

def nmos(ax, x, y, label):
    """N-MOSFET：閘極在左（x, y），汲極在上（x+0.6, y+0.7），源極在下（x+0.6, y-0.7）。"""
    ax.plot([x, x + 0.3], [y, y], color=INK, lw=1.2)
    ax.plot([x + 0.3, x + 0.3], [y - 0.35, y + 0.35], color=INK, lw=1.2)
    for dy in (-0.3, 0, 0.3):
        ax.plot([x + 0.4, x + 0.4], [y + dy - 0.1, y + dy + 0.1], color=INK, lw=1.6)
    ax.plot([x + 0.4, x + 0.6, x + 0.6], [y + 0.3, y + 0.3, y + 0.7], color=INK, lw=1.2)
    ax.plot([x + 0.4, x + 0.6, x + 0.6], [y - 0.3, y - 0.3, y - 0.7], color=INK, lw=1.2)
    ax.plot([x + 0.4, x + 0.6], [y, y], color=INK, lw=1.2)
    ax.plot([x + 0.6, x + 0.6], [y, y - 0.3], color=INK, lw=1.2)
    ax.add_patch(MPoly([(x + 0.42, y), (x + 0.55, y + 0.07), (x + 0.55, y - 0.07)], color=INK))
    ax.text(x + 0.75, y + 0.05, label, fontsize=8, fontweight='bold', family='DejaVu Sans')
    ax.text(x + 0.75, y - 0.22, 'AO3400A', fontsize=6.5, color=GRY, family='DejaVu Sans')
    ax.text(x + 0.05, y + 0.1, 'G', fontsize=6, color=GRY); ax.text(x + 0.66, y + 0.5, 'D', fontsize=6, color=GRY); ax.text(x + 0.66, y - 0.6, 'S', fontsize=6, color=GRY)

def motor(ax, x, y, label):
    ax.add_patch(Circle((x, y), 0.35, fill=False, ec=INK, lw=1.2))
    ax.text(x, y, 'M', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(x + 0.45, y, label, va='center', fontsize=7.5)

def connector(ax, x, y, title, rows, side='r', width=2.6):
    h = 0.42 * len(rows) + 0.3
    ax.add_patch(Rectangle((x, y - h), width, h, fill=False, ec=INK, lw=1.4))
    ax.text(x + width / 2, y + 0.18, title, ha='center', fontsize=9, fontweight='bold')
    pins = {}
    for i, (pin, func) in enumerate(rows):
        yy = y - 0.4 - i * 0.42
        ax.text(x + 0.12, yy, pin, va='center', fontsize=7.5, family='DejaVu Sans')
        ax.text(x + width - 0.12, yy, func, va='center', ha='right', fontsize=7.5, family='DejaVu Sans')
        px = x + width if side == 'r' else x
        ax.plot([px, px + (0.35 if side == 'r' else -0.35)], [yy, yy], color=INK, lw=1.2)
        pins[pin] = (px + (0.35 if side == 'r' else -0.35), yy)
    return pins

def schematic():
    fig = plt.figure(figsize=(16.54, 11.69))       # A3 橫向
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 33); ax.set_ylim(0, 23.4); ax.axis('off')
    ax.add_patch(Rectangle((0.4, 0.4), 32.2, 22.6, fill=False, ec=INK, lw=1.5))
    ax.text(0.9, 22.3, 'FutureZebra × Flix 載板 v1.1 — 原理圖 Schematic', fontsize=16, fontweight='bold')
    ax.text(0.9, 21.75, '電路與 Flix 官方手焊版完全相同：每顆馬達一顆 N-MOSFET 低側開關（G = GPIO、D = 馬達負極、S = 電池負極），G–S 之間 10 kΩ 下拉。'
            'Identical to the official Flix wiring: one low-side N-MOSFET per motor, 10 kΩ gate pull-down.', fontsize=8.5, color=GRY)

    # J1 MINI32
    rows = [('RI8', 'VCC'), ('LO1', 'GND'), ('RI7', 'GND'), ('RO1', 'GND'), ('LI8', '3V3'),
            ('LI4', 'IO18 SCK'), ('LI5', 'IO19 MISO'), ('LI6', 'IO23 MOSI'), ('LI7', 'IO5 CS'),
            ('RO5', 'IO12'), ('LI9', 'IO13'), ('LO7', 'IO14'), ('RI9', 'IO15')]
    p = connector(ax, 1.5, 19.6, 'J1  MINI32（ESP32）\n排母 H1–H4（JLC 焊好）', rows, width=3.4)
    nets = {'RI8': ('VBAT', RED), 'LO1': ('GND', INK), 'RI7': ('GND', INK), 'RO1': ('GND', INK), 'LI8': ('3V3', RED),
            'LI4': ('SCK', BLUE), 'LI5': ('MISO', BLUE), 'LI6': ('MOSI', BLUE), 'LI7': ('CS', BLUE),
            'RO5': ('GATE0', GRN), 'LI9': ('GATE1', GRN), 'LO7': ('GATE2', GRN), 'RI9': ('GATE3', GRN)}
    for k, (n, c) in nets.items(): netlabel(ax, *p[k], n, 'r', c)
    ax.text(1.5, 13.4, '未列出的 27 個腳不接（排母照樣全部焊上，固定主板用）。\n腳位以元件面朝上、天線朝機頭為準。', fontsize=7.5, color=GRY, va='top')

    # J2 GY-91
    rows = [('3V3', '3V3'), ('GND', 'GND'), ('SCL', 'SCK'), ('SDA', 'MOSI'), ('SDO', 'MISO'), ('NCS', 'CS')]
    p = connector(ax, 9.2, 19.6, 'J2  GY-91（IMU）\n6 條線，SPI', rows, width=2.6)
    for (pin, n), c in zip(rows, (RED, INK, BLUE, BLUE, BLUE, BLUE)): netlabel(ax, *p[pin], n, 'r', c)
    ax.text(9.2, 16.6, 'GY-91 的 VIN、CSB 不接。\nGY-91 鎖在機身上，用 6 條短線接到載板。', fontsize=7.5, color=GRY, va='top')

    # 電池
    ax.add_patch(Rectangle((9.2, 12.0), 2.6, 1.6, fill=False, ec=INK, lw=1.4))
    ax.text(10.5, 13.8, 'BT1  電池 1S（MX2.0 線焊上）', ha='center', fontsize=9, fontweight='bold')
    ax.text(9.35, 13.1, 'BAT+', fontsize=7.5); ax.text(9.35, 12.45, 'BAT−', fontsize=7.5)
    ax.plot([11.8, 12.15], [13.1, 13.1], color=INK, lw=1.2); ax.plot([11.8, 12.15], [12.45, 12.45], color=INK, lw=1.2)
    netlabel(ax, 12.15, 13.1, 'VBAT', 'r', RED); netlabel(ax, 12.15, 12.45, 'GND', 'r', INK)
    ax.text(9.2, 11.6, '3.7 V 鋰電池。VBAT 同時供給 MINI32 的 VCC\n和四顆馬達的正極。', fontsize=7.5, color=GRY, va='top')

    # 四個馬達通道
    ax.text(16.6, 20.5, '馬達通道 ×4（照 Flix 官方編號）', fontsize=11, fontweight='bold')
    for i, M in enumerate(MOTORS):
        x0 = 16.8 + (i % 2) * 7.6; y0 = 17.2 - (i // 2) * 7.6
        m = M['m']
        ax.add_patch(FancyBboxPatch((x0 - 0.6, y0 - 5.0), 7.0, 6.8, boxstyle='round,pad=0.05', fill=False, ec='#bbb', lw=1, ls='--'))
        pos = {'RL': '左後', 'RR': '右後', 'FR': '右前', 'FL': '左前'}[M['name']]
        dirz = '逆時針' if M['dir'] == 'CCW' else '順時針'
        ax.text(x0 - 0.4, y0 + 1.45, f'馬達 {m}：{pos}・{dirz}（{M["dir"]}）・GPIO{M["gpio"]}', fontsize=9, fontweight='bold')
        mx, my = x0 + 3.6, y0 - 0.35
        vbat(ax, mx, my + 0.6)
        ax.plot([mx, mx], [my + 0.35, my + 0.6], color=INK, lw=1.2)
        motor(ax, mx, my, f'M{m}  8520 空心杯')
        ax.text(mx - 0.3, my + 0.5, '+', fontsize=8, color=RED, ha='right'); ax.text(mx - 0.3, my - 0.6, '−', fontsize=9, ha='right')
        qx, qy = mx - 0.6, my - 1.75
        ax.plot([mx, mx], [my - 0.35, qy + 0.7], color=INK, lw=1.2)
        ax.text(mx + 0.1, my - 0.75, f'DRAIN{m}', fontsize=6.5, color=GRY, family='DejaVu Sans')
        nmos(ax, qx, qy, f'Q{m}')
        ax.plot([mx, mx], [qy - 0.7, qy - 1.6], color=INK, lw=1.2)
        gnd(ax, mx, qy - 1.6)
        gx = qx - 1.4
        ax.plot([gx, qx], [qy, qy], color=INK, lw=1.2)
        ax.add_patch(Circle((gx + 0.5, qy), 0.05, color=INK))
        resistor(ax, gx + 0.5, qy, qy - 1.6, f'R{m}\n10 kΩ')
        ax.plot([gx + 0.5, mx], [qy - 1.6, qy - 1.6], color=INK, lw=1.2)
        netlabel(ax, gx, qy, f'GATE{m}', 'l', GRN)
        ax.text(x0 - 0.4, y0 - 4.7, f'GATE{m} = IO{M["gpio"]}　R{m} 讓 GPIO 還沒輸出時馬達保持停止', fontsize=7, color=GRY)

    # 元件表
    ax.text(1.5, 9.6, '元件表 BOM', fontsize=11, fontweight='bold')
    tbl = [('Q0–Q3', 'AO3400A N-MOSFET 30 V 5.7 A, SOT-23', 'LCSC C20917（JLC 基本零件）', 'JLC 貼片'),
           ('R0–R3', '10 kΩ 1% 0603', 'LCSC C25804（JLC 基本零件）', 'JLC 貼片'),
           ('H1–H4', '1×10 排母 2.54 mm, 8.5 mm 高 × 4', 'LCSC C2905418', 'JLC 焊（穿孔）'),
           ('J2', 'GY-91 6 條線（28 AWG）', '—', '學生手焊'),
           ('M0–M3', '8520 空心杯馬達線 × 8', '—', '學生手焊'),
           ('BT1', 'MX2.0 電池線 × 2', '—', '學生手焊')]
    for i, row in enumerate(tbl):
        for j, (t, x) in enumerate(zip(row, (1.5, 3.4, 9.6, 14.2))):
            ax.text(x, 9.0 - i * 0.45, t, fontsize=8, fontweight='bold' if j == 0 else 'normal')
    ax.text(1.5, 5.9, '為什麼不用官方的 100N03A：載板要給 JLC 貼片，AO3400A 是 JLC 的基本零件（不另收換料費、庫存多），\n'
            '3.3 V 就能完全導通（VGS(th) 最大 1.45 V，2.5 V 時 RDS(on) ≤ 48 mΩ）。\n'
            '每顆馬達約 1～2 A，MOSFET 發熱約 0.04～0.2 W，SOT-23 夠用。', fontsize=7.5, color=GRY, va='top')
    ax.text(32.2, 0.8, 'FutureZebra × Flix carrier v1.1　2026-11　github.com/greenmail1011/flix-drone', fontsize=7.5, color=GRY, ha='right')
    for ext in ('svg', 'pdf', 'png'):
        fig.savefig(os.path.join(OUT, f'fz-flix-carrier-schematic.{ext}'), dpi=110 if ext == 'png' else None)
    plt.close(fig)

# ======================= 組裝圖 =======================
def assembly():
    img = Image.open(os.path.join(PRE, 'render_top.png'))
    W, H = img.size
    DP = W / 46.0
    def px(x, y): return ((x + OFF[0]) * DP, H - (y + OFF[1]) * DP)
    fig = plt.figure(figsize=(16.54, 11.69))
    ax = fig.add_axes([0.02, 0.06, 0.56, 0.86]); ax.imshow(img); ax.axis('off')
    fig.text(0.02, 0.955, 'FutureZebra × Flix 載板 v1.1 — 組裝圖 Assembly drawing（上視圖，元件面）', fontsize=16, fontweight='bold')
    fig.text(0.02, 0.93, 'JLC 代工：正面貼片 Q0–Q3（AO3400A）、R0–R3（10 kΩ），加上 4 條 1×10 排母 H1–H4（穿孔，JLC 手焊）。學生只焊 16 條線。', fontsize=9, color=GRY)
    for M in MOTORS:
        m = M['m']
        x, y = px(*M['q'])
        ax.add_patch(Circle((x, y), 2.4 * DP, fill=False, ec='#ff5252', lw=2))
        dx, dy = px(*q_pad(M, 'D'))
        ax.annotate('', xy=(dx, dy + (-0.2 if M['fr'] > 0 else 0.2) * DP), xytext=(dx, dy + (2.4 if M['fr'] < 0 else -2.4) * DP * -1),
                    arrowprops=dict(arrowstyle='->', color='#ffd54f', lw=2))
    for i, col in enumerate(('LO', 'LI', 'RI', 'RO'), 1):
        x0, y0 = px(COLS[col] - 1.27, 12.7); x1, y1 = px(COLS[col] + 1.27, -12.7)
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec='#4fc3f7', lw=2, ls='--'))
        tx, ty = px(COLS[col], -13.8)
        ax.text(tx, ty, f'H{i}', color='#4fc3f7', fontsize=10, fontweight='bold', ha='center', va='top')
    fig.text(0.02, 0.025, '藍色虛線：排母 H1–H4（JLC 焊在正面）', fontsize=9.5, color='#0277bd')
    fig.text(0.02, 0.045, '紅圈：MOSFET 位置　黃色箭頭：3 腳（D）朝向自己的馬達焊點', fontsize=9.5, color='#c62828')
    # 右側說明
    ax2 = fig.add_axes([0.6, 0.06, 0.38, 0.86]); ax2.axis('off'); ax2.set_xlim(0, 10); ax2.set_ylim(0, 20)
    y = 19.4
    def head(t):
        nonlocal y; y -= 0.35; ax2.text(0, y, t, fontsize=11.5, fontweight='bold', va='top'); y -= 0.75
    def line(t, c=INK, s=9):
        nonlocal y; ax2.text(0.2, y, t, fontsize=s, color=c, va='top'); y -= 0.55 * (t.count('\n') + 1) + 0.12
    head('1. JLC 代工的零件')
    line('Q0–Q3  AO3400A  LCSC C20917  SOT-23（貼片）\nR0–R3  10 kΩ 1%  LCSC C25804  0603（貼片）\nH1–H4  1×10 排母 8.5 mm  LCSC C2905418（穿孔，JLC 焊）')
    line('MOSFET 方向：1 腳 G、2 腳 S 在同一邊，3 腳 D 單獨一邊，\n3 腳一律朝向同一角的馬達焊點（前面兩顆朝前、後面兩顆朝後）。\n'
         'Pin 3 (Drain) of every Q points toward its own motor pads.', GRY, 8.5)
    head('2. 學生要焊的（線從背面插入、正面焊）')
    line('MINI32 直接插在排母上：天線朝 FRONT、USB 朝後')
    line('J2：GY-91 的 6 條線 → 3V3、GND、SCL、SDA、SDO、NCS')
    line('馬達：每顆 2 條線。白或紅 → +；黑或藍 → −')
    line('電池：MX2.0 線 紅 → BAT+；黑 → BAT−')
    head('3. 馬達對照')
    for M in MOTORS:
        pos = {'RL': '左後', 'RR': '右後', 'FR': '右前', 'FL': '左前'}[M['name']]
        line(f'M{M["m"]}  {pos}  {"逆時針 B 槳" if M["dir"] == "CCW" else "順時針 A 槳"}  GPIO{M["gpio"]}  Q{M["m"]} / R{M["m"]}', s=9)
    head('4. 安裝')
    line('載板取代原本的 ESP32 支架：先把「載板支柱」(carrier-posts.stl)\n用 4 顆 M1.4×5 從機身底面鎖上，再把載板用 4 顆 M1.4×5 鎖在柱子上。\n'
         '載板的 4 個 1.6 mm 孔與原支架柱腳同位。GY-91 照原樣鎖在機身上。', s=8.8)
    head('5. 尺寸')
    line('外框 46.0 × 45.5 mm（含後方電池焊點凸片），板厚 1.0 mm\n原點：板子左下角（座標檔 CPL 的 Mid X / Mid Y 以此為準）', s=8.8)
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(OUT, f'fz-flix-carrier-assembly.{ext}'), dpi=120 if ext == 'png' else None)
    plt.close(fig)

if __name__ == '__main__':
    schematic(); assembly(); print('ok')
