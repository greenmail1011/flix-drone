"""DRC 與連通檢查（用精確的 shapely 圖形，不是點陣圖）。"""
import itertools, collections, math, pickle, sys
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
import board as B
from route import CLR, EDGE_CLR, HOLE_CLR, VIA_DRILL

RULES = dict(clearance=0.127, edge=0.3, hole_copper=0.25, hole_to_hole=0.4, min_track=0.15, min_drill=0.3, ring_via=0.13)

def run(R):
    errs, info = [], []
    for layer in 'FB':
        fs = [f for f in R.feats if f.layer == layer]
        nets = collections.defaultdict(list)
        for f in fs: nets[f.net].append(f.geom)
        merged = {n: unary_union(g) for n, g in nets.items()}
        names = list(merged)
        tree = STRtree([merged[n] for n in names])
        mins = []
        for i, n in enumerate(names):
            g = merged[n]
            for j in tree.query(g.buffer(0.6)):
                if j <= i: continue
                d = g.distance(merged[names[j]])
                mins.append((d, n, names[j]))
                if d < RULES['clearance'] - 1e-4:
                    # 找出位置
                    a = g.buffer(RULES['clearance'] / 2).intersection(merged[names[j]].buffer(RULES['clearance'] / 2)).centroid
                    errs.append(f'[{layer}] 間距 {d:.3f} mm：{n} ↔ {names[j]} 約在 ({a.x:.2f},{a.y:.2f})')
        mins.sort()
        info.append(f'[{layer}] 最小間距 {mins[0][0]:.3f} mm（{mins[0][1]} ↔ {mins[0][2]}）')
    edge = B.BOARD.exterior
    worst = min((f.geom.distance(edge), f.net, f.ref) for f in R.feats if f.geom.within(B.BOARD))
    out = [f for f in R.feats if not f.geom.within(B.BOARD)]
    for f in out: errs.append(f'銅箔超出板框：{f.net} {f.ref} {f.kind}')
    if worst[0] < RULES['edge']: errs.append(f'銅到板邊 {worst[0]:.3f} mm（{worst[1]} {worst[2]}）')
    info.append(f'銅到板邊最小 {worst[0]:.3f} mm')
    for h in R.hole_geoms:
        for f in R.feats:
            d = f.geom.distance(h)
            if d < RULES['hole_copper']: errs.append(f'孔 ({h.centroid.x:.2f},{h.centroid.y:.2f}) 到銅 {d:.3f}（{f.net}）')
    for f in R.feats:
        if f.geom.intersection(B.ANT_KEEPOUT).area > 1e-6: errs.append(f'天線禁區有銅：{f.net} {f.ref}')
    def hole_shape(x, y, dw, dh):
        if abs(dw - dh) < 1e-6: return Point(x, y).buffer(dw / 2, 32)
        # 長圓孔：找出對應焊墊的方向
        pad = min((p for p in B.PADS if p.drill), key=lambda p: math.hypot(p.x - x, p.y - y))
        r = min(dw, dh) / 2; L = max(dw, dh) / 2 - r
        ang = math.radians(pad.rot + (90 if dh > dw else 0))
        return LineString([(x - L * math.cos(ang), y - L * math.sin(ang)), (x + L * math.cos(ang), y + L * math.sin(ang))]).buffer(r, 16)
    holes = [(x, y, max(dw, dh), hole_shape(x, y, dw, dh)) for x, y, dw, dh, *_ in R.drills] + [(x, y, B.MOUNT_D, Point(x, y).buffer(B.MOUNT_D / 2)) for x, y in B.MOUNT_HOLES]
    hh = []
    for a, b in itertools.combinations(holes, 2):
        if math.hypot(a[0] - b[0], a[1] - b[1]) > 4: continue
        d = a[3].distance(b[3])
        hh.append(d)
        if d < RULES['hole_to_hole']: errs.append(f'孔距 {d:.3f} @({a[0]:.2f},{a[1]:.2f})')
    info.append(f'孔壁到孔壁最小 {min(hh):.3f} mm；最小鑽孔 {min(h[2] for h in holes):.2f} mm')
    for f in R.feats:
        if f.gerber[0] == 'draw' and f.gerber[1] < RULES['min_track']: errs.append(f'線寬 {f.gerber[1]}（{f.net}）')
    # 連通
    parent = list(range(len(R.feats)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for layer in 'FB':
        idx = [i for i, f in enumerate(R.feats) if f.layer == layer]
        tree = STRtree([R.feats[i].geom for i in idx])
        for k, i in enumerate(idx):
            for j in tree.query(R.feats[i].geom):
                jj = idx[j]
                if jj > i and R.feats[i].geom.intersects(R.feats[jj].geom):
                    if R.feats[i].net != R.feats[jj].net:
                        errs.append(f'短路：{R.feats[i].net} ↔ {R.feats[jj].net}')
                    parent[find(i)] = find(jj)
    # 鍍通孔把兩層連起來
    for x, y, dw, dh, pl, net in R.drills:
        if not pl: continue
        p = Point(x, y)
        ids = [i for i, f in enumerate(R.feats) if f.net == net and f.geom.distance(p) < 1e-3]
        for a in ids[1:]: parent[find(a)] = find(ids[0])
    groups = collections.defaultdict(set)
    for i, f in enumerate(R.feats):
        if f.kind in ('smd', 'tht') and f.net and not f.net.startswith(('NC_', 'MP_')):
            groups[f.net].add(find(i))
    for net, g in sorted(groups.items()):
        if len(g) != 1:
            # 列出沒連上的焊墊
            comp = collections.defaultdict(list)
            for i, f in enumerate(R.feats):
                if f.net == net and f.kind in ('smd', 'tht'): comp[find(i)].append(f'{f.ref}')
            errs.append(f'網路 {net} 分成 {len(g)} 塊：' + ' | '.join(','.join(sorted(set(v))) for v in comp.values()))
    info.append(f'檢查 {len(groups)} 個網路的連通')
    return errs, info

if __name__ == '__main__':
    R = pickle.load(open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/final.pkl', 'rb'))
    e, i = run(R)
    print('\n'.join(i))
    print('DRC：0 錯誤' if not e else f'錯誤 {len(e)}：')
    print('\n'.join(sorted(set(e))[:60]))
