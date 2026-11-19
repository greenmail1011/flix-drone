"""大電流路徑補強：在 VBAT／馬達網路上加並聯過孔。

v2.0 原本電池正極只靠 2 個 0.3 mm 過孔把右邊兩顆馬達的電流送到背面，
右前、右後馬達插座各只有 1 個過孔，左邊兩顆馬達只走正面 0.8 mm 細線。
這裡在「正面、背面都已經有同網路銅箔」的地方加過孔（必要時補一小段背面線），
讓每個換層點至少 3～4 個過孔，並把背面 VBAT 橫向分支接到左邊兩個馬達插座。
"""
import math
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
import board as B
from route import CLR, EDGE_CLR, HOLE_CLR, VIA_PAD, VIA_DRILL, VIA_KEEPOUTS

HOLE_GAP = 0.45      # 孔壁到孔壁（規則 0.4，多留一點）


def _copper(R, layer, net):
    return unary_union([f.geom for f in R.feats if f.layer == layer and f.net == net])


def _others(R, layer, net):
    return unary_union([f.geom for f in R.feats if f.layer == layer and f.net != net])


def _ok_via(R, x, y, net, extra_b=None, extra_f=None):
    p = Point(x, y)
    pad = p.buffer(VIA_PAD / 2, 24)
    if not pad.buffer(EDGE_CLR).within(B.BOARD): return False
    if pad.intersects(B.ANT_KEEPOUT.buffer(0.1)): return False
    for kb in VIA_KEEPOUTS:
        if pad.intersects(kb): return False
    for h in R.hole_geoms:
        if pad.distance(h) < HOLE_CLR + 0.05: return False
    for dx, dy, dw, dh, *_ in R.drills:
        if math.hypot(x - dx, y - dy) - max(dw, dh) / 2 - VIA_DRILL / 2 < HOLE_GAP: return False
    # 不打在 SMD 焊墊上（避免吃錫）
    for f in R.feats:
        if f.kind == 'smd' and f.geom.distance(pad) < 0.1: return False
    gF = pad if extra_f is None else pad.union(extra_f)
    gB = pad if extra_b is None else pad.union(extra_b)
    if gF.distance(_others(R, 'F', net)) < CLR + 0.02: return False
    if gB.distance(_others(R, 'B', net)) < CLR + 0.02: return False
    return True


def add_vias(R, net, center, radius, want, btrack_w=None, max_link=1.6, label='', base='F'):
    """在 center 半徑 radius 內，為 net 加最多 want 個並聯過孔。

    候選點必須在正面同網路銅箔上；背面若沒有同網路銅箔，就拉一段直線（寬 btrack_w）
    接到最近的背面同網路銅箔（最長 max_link）。
    """
    added = []
    cx, cy = center
    step = 0.1
    cands = []
    link_layer = 'B' if base == 'F' else 'F'
    F = _copper(R, base, net)
    k = int(radius / step)
    for i in range(-k, k + 1):
        for j in range(-k, k + 1):
            x, y = cx + i * step, cy + j * step
            if math.hypot(x - cx, y - cy) > radius: continue
            if F.contains(Point(x, y)) and not any(f.kind == 'smd' and f.net == net and f.geom.contains(Point(x, y)) for f in R.feats):
                cands.append((x, y))
    for _ in range(want):
        Bc = unary_union([f.geom for f in R.feats if f.layer == link_layer and f.net == net and f.kind != 'smd'] +
                         [f.geom.buffer(-0.15) for f in R.feats if f.layer == link_layer and f.net == net and f.kind == 'smd'])
        best = None
        for x, y in cands:
            p = Point(x, y)
            if Bc.contains(p):
                link, d = None, 0.0
            else:
                d = Bc.distance(p)
                if btrack_w is None or d > max_link: continue
                from shapely.ops import nearest_points
                q = nearest_points(Bc, p)[0]
                # 往銅箔內多伸一點，確保接上
                ux, uy = q.x - x, q.y - y
                n = math.hypot(ux, uy) or 1
                q2 = (q.x + ux / n * btrack_w / 2, q.y + uy / n * btrack_w / 2)
                link = LineString([(x, y), q2])
            eb = None if link is None else link.buffer(btrack_w / 2, 12)
            ok = _ok_via(R, x, y, net, extra_b=eb) if link_layer == 'B' else _ok_via(R, x, y, net, extra_f=eb)
            if not ok: continue
            score = d + 0.05 * math.hypot(x - cx, y - cy)
            if best is None or score < best[0]: best = (score, x, y, link)
        if best is None: break
        _, x, y, link = best
        if link is not None:
            R.add_track(link_layer, net, list(link.coords), btrack_w)
        R.add_via(x, y, net)
        added.append((round(x, 2), round(y, 2)))
    print(f'  {label or net}：加 {len(added)} 個過孔 {added}')
    return added


# 每個換層點：(網路, 中心, 半徑, 要加幾個, 背面補線寬, 說明)
PLAN = [
    ('VBAT', (-1.0, -15.9), 2.2, 3, 1.0, '電池正極 → 背面主幹'),
    ('VBAT', (15.12, 9.38), 1.6, 2, 0.8, '右前馬達 J5 供電'),
    ('VBAT', (-15.4, -0.6), 1.4, 3, 0.8, '背面分支 → 左後馬達 J3'),
    ('VBAT', (-15.6, 9.5), 1.4, 3, 0.8, '背面分支 → 左前馬達 J6'),
]


# 手動指定：(網路, 過孔位置, [(層, 線段點, 線寬)], 說明)
MANUAL = [
    ('VBAT', (16.4, -2.5), [('F', [(16.4, -2.5), (16.4, -1.5)], 0.8), ('B', [(16.4, -2.5), (15.43, -1.23)], 0.8)], '右後馬達 J4 供電 #2'),
    ('VBAT', (17.2, -2.5), [('F', [(17.2, -2.5), (17.0, -1.5)], 0.8), ('B', [(17.2, -2.5), (16.4, -2.5)], 0.8)], '右後馬達 J4 供電 #3'),
    ('MOT_RL', (-17.3, -2.75), [('F', [(-17.3, -2.75), (-17.0, -1.5)], 0.8), ('B', [(-17.3, -2.75), (-16.57, -2.23)], 0.8)], '左後馬達 MOT_RL 插座端 #2'),
]


def add_manual(R, net, xy, tracks, label):
    x, y = xy
    eb = unary_union([LineString(p).buffer(w / 2, 12) for L, p, w in tracks if L == 'B'] or [Point(x, y)])
    ef = unary_union([LineString(p).buffer(w / 2, 12) for L, p, w in tracks if L == 'F'] or [Point(x, y)])
    if not _ok_via(R, x, y, net, extra_b=eb, extra_f=ef):
        print(f'  {label}：位置不行，跳過'); return 0
    for L, p, w in tracks: R.add_track(L, net, p, w)
    R.add_via(x, y, net)
    print(f'  {label}：加 1 個過孔 {(x, y)}')
    return 1


def run(R):
    print('大電流過孔補強：')
    total = 0
    for net, xy, tr, lab in MANUAL:
        total += add_manual(R, net, xy, tr, lab)
    for net, c, r, want, w, lab, *base in PLAN:
        total += len(add_vias(R, net, c, r, want, btrack_w=w, label=lab, base=(base[0] if base else 'F')))
    return total
