"""產生一體板：佈線 → 鋪銅 → 檢查 → 預覽。"""
import time, pickle, sys
import board as B
from route import Router, WIDTH
import plot

ORDER = ['VBAT', 'MOT_FL', 'MOT_FR', 'MOT_RL', 'MOT_RR', 'VBUS', 'VSYS', 'DM', 'DP', 'CC1', 'CC2', '3V3',
         'GATE_FL', 'GATE_FR', 'GATE_RL', 'GATE_RR', 'SCK', 'MOSI', 'MISO', 'CS', 'TXD0', 'RXD0',
         'DTR', 'RTS', 'EN', 'IO0', 'Q6B', 'Q7B', 'VSENSE', 'LED', 'LEDA']

SPINE_X = 3.0
def preroute(R):
    """VBAT 主幹：電池插座正極 → 過孔 → 背面主幹（x = 3）→ 前、後兩條橫向分支（背面）。"""
    j2 = [p for p in B.PADS if p.ref == 'J2' and p.name == '1'][0]
    ytop = j2.y + j2.h / 2            # 焊墊上緣
    vy = ytop + 0.55
    R.add_track('F', 'VBAT', [(j2.x, ytop - 0.6), (j2.x, vy)], 1.0)
    R.add_via(j2.x - 0.45, vy, 'VBAT'); R.add_via(j2.x + 0.45, vy, 'VBAT')
    R.add_track('F', 'VBAT', [(j2.x - 0.45, vy), (j2.x + 0.45, vy)], 1.0)
    R.add_track('B', 'VBAT', [(j2.x - 0.45, vy), (SPINE_X, vy), (SPINE_X, 9.9)], 1.5)
    R.add_track('B', 'VBAT', [(-15.6, 9.9), (14.9, 9.9)], 1.2)
    R.add_track('B', 'VBAT', [(-15.6, -0.8), (15.1, -0.8)], 1.2)
    # 模組底部大焊墊（GND）的散熱/接地過孔
    # IMU 第 11 腳（GND，在上排中間）：直接往上拉一小段打孔
    p11 = [p for p in B.PADS if p.ref == 'U2' and p.name == '11'][0]
    R.add_track('F', 'GND', [(p11.x, p11.y), (p11.x, p11.y + 0.5), (p11.x - 0.65, p11.y + 0.95)], 0.2)
    R.add_via(p11.x - 0.65, p11.y + 0.95, 'GND')
    # IMU 第 8 腳（VDDIO）直接往上接 C9
    p8 = [p for p in B.PADS if p.ref == 'U2' and p.name == '8'][0]
    c9 = [p for p in B.PADS if p.ref == 'C9' and p.name == '1'][0]
    R.add_track('F', '3V3', [(p8.x, p8.y), (p8.x, p8.y + 0.5), (c9.x, p8.y + 0.8), (c9.x, c9.y)], 0.2)
    # IMU 第 13 腳（VDD）往左再往上接 C7
    p13 = [p for p in B.PADS if p.ref == 'U2' and p.name == '13'][0]
    c7 = [p for p in B.PADS if p.ref == 'C7' and p.name == '1'][0]
    R.add_track('F', '3V3', [(p13.x, p13.y), (p13.x - 0.55, p13.y), (p13.x - 0.55, c7.y - 0.5), (p13.x - 0.1, c7.y), (c7.x, c7.y)], 0.2)
    # 細腳距元件的 GND 先扇出（之後的訊號線會繞開）
    R.gnd_fanout(refs={('U2', '18'), ('U2', '19'), ('U2', '20'), 'U3', 'U4'})

def run(save='/tmp/r.pkl', tries=14):
    t = time.time()
    missing = [n for n in B.NETS if n not in ORDER and n != 'GND']
    if missing: print('沒排序的網路', missing)
    FIXED = ['VBAT', 'MOT_FL', 'MOT_FR', 'MOT_RL', 'MOT_RR', 'VBUS', 'VSYS']
    order = [n for n in ORDER if n not in FIXED]
    best = None
    for k in range(tries):
        R = Router()
        preroute(R)
        bad = []
        for n in FIXED + order:
            if not R.route_net(n, log=False): bad.append(n)
        print(f'第 {k + 1} 輪：失敗 {bad}  {time.time() - t:.0f}s')
        if best is None or len(bad) < len(best[1]): best = (R, bad, list(order))
        if not bad: break
        import random
        rng = random.Random(k)
        rest = [n for n in order if n not in bad]
        if k % 2: rng.shuffle(rest)
        order = [n for n in bad if n not in FIXED] + rest
    R, bad, order = best
    print('採用順序：', order)
    print('佈線失敗：', bad)
    pickle.dump(R, open(save, 'wb'))
    return R

def finish(R):
    """GND：模組大焊墊打孔、每個 GND 焊墊扇出、兩面鋪銅、縫合過孔。"""
    R.gnd_fanout(refs={p.ref for p in B.PADS if p.ref not in ('U1', 'U2', 'U3', 'U4')})
    top = R.pour('F'); bot = R.pour('B')
    n = R.stitch(top, bot)
    # 鋪銅要在縫合過孔之後重算（過孔本身是 GND，不影響）
    R.pour_F, R.pour_B = top, bot
    R.add_feat('F', 'GND', top, ('region', top), 'region')
    R.add_feat('B', 'GND', bot, ('region', bot), 'region')
    print(f'縫合過孔 {n} 個；總過孔 {len(R.vias)} 個')
    return R

if __name__ == '__main__':
    import sys
    if '--reuse' in sys.argv:
        R = pickle.load(open('/tmp/r.pkl', 'rb'))
    else:
        R = run()
    R = finish(R)
    pickle.dump(R, open('/tmp/final.pkl', 'wb'))
    def extra(d, tr):
        for f in R.feats:
            if f.kind == 'region':
                col = (60, 120, 80) if f.layer == 'F' else (40, 70, 120)
                for pg in (f.geom.geoms if hasattr(f.geom, 'geoms') else [f.geom]):
                    if f.layer == 'F': d.polygon([tr(*c) for c in pg.exterior.coords], outline=col)
        for f in R.feats:
            if f.kind == 'track':
                col = (220, 120, 40) if f.layer == 'F' else (80, 140, 255)
                w, pts = f.gerber[1], f.gerber[2]
                d.line([tr(*p) for p in pts], fill=col, width=max(1, int(w * plot.DP)))
        for x, y, n in R.vias:
            cx, cy = tr(x, y); r = 0.3 * plot.DP
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(240, 240, 240))
    plot.draw('/tmp/route.png', extra)
