"""DRC 與連通檢查（自己寫的，對照 JLCPCB 2 層板能力，取較保守的值）。"""
import itertools, collections
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
from design import *
import layout as L

RULES = dict(clearance=CLR - 1e-6, edge=0.3, hole_to_hole=0.5, annular_tht=0.25, annular_via=0.13, min_track=0.2, min_drill=0.3)

def run():
    errs, info = [], []
    # 1) 不同網路的銅箔間距（同層）
    for layer in 'FB':
        fs = [f for f in L.FEATS if f.layer == layer]
        nets = collections.defaultdict(list)
        for f in fs: nets[f.net].append(f.geom)
        merged = {n: unary_union(g) for n, g in nets.items()}
        names = list(merged)
        tree = STRtree([merged[n] for n in names])
        for i, n in enumerate(names):
            g = merged[n]
            for j in tree.query(g.buffer(RULES['clearance'])):
                if j <= i: continue
                d = g.distance(merged[names[j]])
                if d < RULES['clearance']:
                    errs.append(f'[{layer}] 間距 {d:.3f} mm：{n} ↔ {names[j]}')
        # 最小間距統計
        mins = []
        for i, n in enumerate(names):
            for j in tree.query(merged[n].buffer(0.6)):
                if j > i: mins.append((merged[n].distance(merged[names[j]]), n, names[j]))
        mins.sort()
        info.append(f'[{layer}] 最小線距 {mins[0][0]:.3f} mm（{mins[0][1]} ↔ {mins[0][2]}）')
    # 2) 銅到板邊
    edge = BOARD.exterior
    worst = min((f.geom.distance(edge), f.net) for f in L.FEATS if f.geom.within(BOARD) or True)
    if worst[0] < RULES['edge']: errs.append(f'銅到板邊 {worst[0]:.3f} mm（{worst[1]}）')
    out = [f for f in L.FEATS if not f.geom.within(BOARD)]
    if out: errs.append(f'{len(out)} 個銅箔超出板框')
    info.append(f'銅到板邊最小 {worst[0]:.3f} mm')
    # 3) 鑽孔
    holes = [(x, y, d) for x, y, d, *_ in L.DRILLS] + [(x, y, MOUNT_D) for x, y in MOUNT_HOLES]
    hh = min(Point(a[:2]).distance(Point(b[:2])) - a[2] / 2 - b[2] / 2 for a, b in itertools.combinations(holes, 2))
    if hh < RULES['hole_to_hole']: errs.append(f'孔到孔 {hh:.3f} mm')
    info.append(f'孔壁到孔壁最小 {hh:.3f} mm；最小鑽孔 {min(h[2] for h in holes):.2f} mm')
    for x, y, pad, drill, net, ref in L.THT:
        if (pad - drill) / 2 < RULES['annular_tht']: errs.append(f'{ref} 孔環太小')
    if (VIA_PAD - VIA_DRILL) / 2 < RULES['annular_via']: errs.append('過孔孔環太小')
    # NPTH 到銅
    for x, y in MOUNT_HOLES:
        h = Point(x, y).buffer(MOUNT_D / 2)
        d = min(f.geom.distance(h) for f in L.FEATS)
        if d < 0.3: errs.append(f'安裝孔 ({x},{y}) 到銅 {d:.3f}')
    # 4) 線寬
    for f in L.FEATS:
        if f.gerber[0] == 'draw' and f.gerber[1] < RULES['min_track']: errs.append(f'線寬 {f.gerber[1]} < 0.2（{f.net}）')
    # 5) 天線區無銅
    for f in L.FEATS:
        if f.geom.intersection(ANTENNA_KEEPOUT).area > 1e-6: errs.append(f'天線區有銅：{f.net}')
    # 6) 連通：每個網路必須連成一塊（兩層 + 穿孔/過孔）
    parent = {}
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b): parent[find(a)] = find(b)
    feats = list(enumerate(L.FEATS))
    for i, _ in feats: parent[i] = i
    for layer in 'FB':
        idx = [i for i, f in feats if f.layer == layer]
        tree = STRtree([L.FEATS[i].geom for i in idx])
        for k, i in enumerate(idx):
            for j in tree.query(L.FEATS[i].geom):
                jj = idx[j]
                if jj != i and L.FEATS[i].geom.intersects(L.FEATS[jj].geom):
                    if L.FEATS[i].net != L.FEATS[jj].net:
                        errs.append(f'短路：{L.FEATS[i].net} ↔ {L.FEATS[jj].net}')
                    union(i, jj)
    # 穿孔：同位置的上下層焊墊相連
    bypos = collections.defaultdict(list)
    for i, f in feats:
        if f.kind in ('tht', 'via'): bypos[(round(f.gerber[4], 3), round(f.gerber[5], 3))].append(i)
    for lst in bypos.values():
        for a in lst[1:]: union(lst[0], a)
    groups = collections.defaultdict(set)
    for i, f in feats:
        if f.net.startswith('NC_'): continue
        groups[f.net].add(find(i))
    for net, g in sorted(groups.items()):
        if len(g) != 1: errs.append(f'網路 {net} 沒有連通（{len(g)} 塊）')
    info.append('連通的網路：' + '、'.join(f'{n}' for n in sorted(groups) if len(groups[n]) == 1))
    info.append(f'接地縫合過孔 {len(L.STITCH)} 個')
    return errs, info

if __name__ == '__main__':
    e, i = run()
    print('\n'.join(i))
    print('錯誤：' if e else 'DRC：0 錯誤')
    print('\n'.join(sorted(set(e))))
