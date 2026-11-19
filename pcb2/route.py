"""兩層板自動佈線（格點 A*）＋ GND 鋪銅。

做法：
- 所有銅箔都存成 shapely 圖形（給 Gerber 與 DRC），同時畫進 0.05 mm 的「網路編號」點陣圖。
- 佈某個網路時，用距離轉換算出每個格點到「其他網路銅箔」的距離，
  距離不夠（線寬/2 + 間距）的格點就不能走。
- 每個網路從第一個焊墊開始長成一棵樹，其他焊墊一個一個用 A* 接到樹上。
- 路徑最後做「拉直」：在不違反間距的前提下，把鋸齒狀格點路徑合併成少數幾段直線。
"""
import heapq, math, time
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt
from shapely.geometry import Point, LineString, Polygon, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
import board as B

# ---------------- 設計規則（JLCPCB 2 層板能力：線寬/線距 0.1/0.1；這裡取保守值） ----------------
CLR = 0.16            # 不同網路銅箔最小間距（DRC 標準 0.127，留點陣誤差餘量）
EDGE_CLR = 0.35       # 銅到板邊
HOLE_CLR = 0.3        # 銅到 NPTH／安裝孔
VIA_PAD, VIA_DRILL = 0.6, 0.3
VIA_COST = 12         # 換層成本（格數）
BOTTOM_COST = 1.6     # 背面走線成本倍數（背面盡量留給 GND 鋪銅）
FINE = 0.05           # 障礙點陣圖解析度
G = 0.1               # 佈線格點
X0, Y0, X1, Y1 = -23.5, -26.5, 23.5, 20.0
NXF, NYF = int(round((X1 - X0) / FINE)), int(round((Y1 - Y0) / FINE))
NX, NY = NXF // 2, NYF // 2

WIDTH = {'VBAT': 1.0, 'MOT_FL': 0.8, 'MOT_FR': 0.8, 'MOT_RL': 0.8, 'MOT_RR': 0.8,
         'VSYS': 0.5, '3V3': 0.3, 'VBUS': 0.5, 'GND': 0.3, '5V': 0.4, 'SW5': 0.4}
DEFAULT_W = 0.15
BOTTOM_COST = 1.6
USE_MODULE_KEEPOUT = False
# 正面不走線的區域：ESP32 模組底下（模組底面只有 GND 大焊墊）
MODULE_KEEPOUT_F = box(-7.2, B.U1_ORIGIN[1] - 8.0, 7.2, B.U1_ORIGIN[1] + 15.8)


# 區域保留：(多邊形, 層, 允許的網路)。其他網路不能進入。
USB_NETS = {'VBUS', 'DP', 'DM', 'CC1', 'CC2', 'GND'}
KEEPOUTS = [
    (box(-16.2, -14.6, -13.4, -7.3), 'F', USB_NETS),     # USB-C 焊墊前方：只給 USB 的線
    (box(B.IMU_XY[0] - 1.15, B.IMU_XY[1] - 1.15, B.IMU_XY[0] + 1.15, B.IMU_XY[1] + 1.15), 'F', set()),   # IMU 底下（焊墊圈內）不走線
]
VIA_KEEPOUTS = [box(B.IMU_XY[0] - 1.55, B.IMU_XY[1] - 1.55, B.IMU_XY[0] + 1.55, B.IMU_XY[1] + 1.55)]   # IMU 底下不打孔


class Copper:
    """一個銅箔圖形。gerber: ('pad', Pad) | ('draw', width, pts) | ('region', polygon)"""
    def __init__(self, layer, net, geom, gerber, kind, ref=None):
        self.layer, self.net, self.geom, self.gerber, self.kind, self.ref = layer, net, geom, gerber, kind, ref


def pad_geom(p):
    """焊墊外形（本專案座標）。圓角矩形當作矩形（保守）；橢圓用長圓形。"""
    if p.shape in ('circle',):
        return Point(p.x, p.y).buffer(p.w / 2, 32)
    if p.shape == 'oval':
        r = min(p.w, p.h) / 2
        L = max(p.w, p.h) / 2 - r
        seg = LineString([(-L, 0), (L, 0)] if p.w >= p.h else [(0, -L), (0, L)]).buffer(r, 16)
        return affinity.translate(affinity.rotate(seg, p.rot, origin=(0, 0)), p.x, p.y)
    g = box(-p.w / 2, -p.h / 2, p.w / 2, p.h / 2)
    return affinity.translate(affinity.rotate(g, p.rot, origin=(0, 0)), p.x, p.y)


class Router:
    def __init__(self):
        self.nets = ['<none>'] + B.NETS + sorted({p.net for p in B.PADS if p.net and p.net not in B.NETS})
        self.nid = {n: i for i, n in enumerate(self.nets)}
        self.lab = {L: np.zeros((NYF, NXF), np.int32) for L in 'FB'}
        self.feats = []
        self.drills = []          # (x, y, dw, dh, plated, net)
        self.vias = []
        self.tracks = {}          # net -> list of (layer, pts, w)
        self._static()
        for p in B.PADS:
            self.add_pad(p)

    # ----- 點陣化 -----
    def _poly_to_px(self, poly):
        return [((x - X0) / FINE, (Y1 - y) / FINE) for x, y in poly.exterior.coords]

    def raster(self, layer, geom, value):
        im = Image.fromarray(self.lab[layer])
        d = ImageDraw.Draw(im)
        polys = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
        for pg in polys:
            if pg.is_empty: continue
            d.polygon(self._poly_to_px(pg), fill=int(value))
        self.lab[layer] = np.array(im, np.int32)

    def _static(self):
        """不能放銅的地方：板外、天線禁區、安裝孔、NPTH。"""
        im = Image.new('L', (NXF, NYF), 0)
        d = ImageDraw.Draw(im)
        outside = box(X0 - 1, Y0 - 1, X1 + 1, Y1 + 1).difference(B.BOARD)
        for pg in (outside.geoms if hasattr(outside, 'geoms') else [outside]):
            d.polygon(self._poly_to_px(pg), fill=255)
            for r in pg.interiors:
                d.polygon([((x - X0) / FINE, (Y1 - y) / FINE) for x, y in r.coords], fill=0)
        edge = np.array(im) > 0
        dist_edge = distance_transform_edt(~edge) * FINE
        im2 = Image.new('L', (NXF, NYF), 0)
        d2 = ImageDraw.Draw(im2)
        holes = [Point(x, y).buffer(B.MOUNT_D / 2, 32) for x, y in B.MOUNT_HOLES]
        holes += [Point(p.x, p.y).buffer(p.drill[0] / 2, 32) for p in B.PADS if p.kind == 'npth']
        for h in holes:
            d2.polygon(self._poly_to_px(h), fill=255)
        hole = np.array(im2) > 0
        dist_hole = distance_transform_edt(~hole) * FINE
        im3 = Image.new('L', (NXF, NYF), 0)
        ImageDraw.Draw(im3).polygon(self._poly_to_px(B.ANT_KEEPOUT.intersection(box(X0, Y0, X1, Y1))), fill=255)
        ant = np.array(im3) > 0
        dist_ant = distance_transform_edt(~ant) * FINE
        # 每個格點「最多能放多粗的半徑」：受板邊、孔、天線區限制
        self.static_r = np.minimum(np.minimum(dist_edge - EDGE_CLR, dist_hole - HOLE_CLR), dist_ant - 0.05) - FINE / 2
        im4 = Image.new('L', (NXF, NYF), 0)
        ImageDraw.Draw(im4).polygon(self._poly_to_px(MODULE_KEEPOUT_F), fill=255)
        mk = np.array(im4) > 0
        self.static_rF = np.minimum(self.static_r, distance_transform_edt(~mk) * FINE - FINE / 2)
        self.hole_geoms = holes

    def add_feat(self, layer, net, geom, gerber, kind, ref=None):
        self.feats.append(Copper(layer, net, geom, gerber, kind, ref))
        self.raster(layer, geom, self.nid.get(net, 0) if net else 0)

    def add_pad(self, p):
        if p.kind == 'npth':
            self.drills.append((p.x, p.y, p.drill[0], p.drill[1], False, None))
            return
        g = pad_geom(p)
        net = p.net
        if net not in self.nid:
            self.nid[net] = len(self.nets); self.nets.append(net)
        layers = 'FB' if p.kind == 'tht' else 'F'
        for L in layers:
            self.add_feat(L, net, g, ('pad', p), 'tht' if p.kind == 'tht' else 'smd', p.ref)
        if p.kind == 'tht':
            self.drills.append((p.x, p.y, p.drill[0], p.drill[1], True, net))

    def add_via(self, x, y, net):
        g = Point(x, y).buffer(VIA_PAD / 2, 24)
        for L in 'FB':
            self.add_feat(L, net, g, ('via', x, y), 'via')
        self.drills.append((x, y, VIA_DRILL, VIA_DRILL, True, net))
        self.vias.append((x, y, net))

    def add_track(self, layer, net, pts, w):
        g = LineString(pts).buffer(w / 2, 12) if len(pts) > 1 else Point(pts[0]).buffer(w / 2, 12)
        self.add_feat(layer, net, g, ('draw', w, list(pts)), 'track')
        self.tracks.setdefault(net, []).append((layer, list(pts), w))

    # ----- 距離場 -----
    def clearance_field(self, net):
        """回傳每層的「到其他網路銅箔的距離」（佈線格點解析度）。"""
        me = self.nid[net]
        out = {}
        for L in 'FB':
            lab = self.lab[L]
            other = (lab != 0) & (lab != me)
            dist = distance_transform_edt(~other) * FINE - FINE / 2
            st = self.static_rF if (L == 'F' and net != 'GND' and USE_MODULE_KEEPOUT) else self.static_r
            for poly, layers, allowed in KEEPOUTS:
                if L in layers and net not in allowed:
                    if not hasattr(self, '_ko'): self._ko = {}
                    key = (id(poly), L)
                    if key not in self._ko:
                        im = Image.new('L', (NXF, NYF), 0)
                        ImageDraw.Draw(im).polygon(self._poly_to_px(poly), fill=255)
                        self._ko[key] = distance_transform_edt(~(np.array(im) > 0)) * FINE - FINE / 2 - CLR
                    st = np.minimum(st, self._ko[key])
            out[L] = np.minimum(dist, st + CLR)[::2, ::2]   # static_r 已扣掉自己的間距
        return out

    def own_mask(self, net):
        me = self.nid[net]
        return {L: (self.lab[L] == me)[::2, ::2] for L in 'FB'}

    # ----- 座標 -----
    @staticmethod
    def cell_xy(i, j):
        return (X0 + (j * 2 + 0.5) * FINE, Y1 - (i * 2 + 0.5) * FINE)

    @staticmethod
    def xy_cell(x, y):
        return int(round((Y1 - y) / FINE - 0.5)) // 2, int(round((x - X0) / FINE - 0.5)) // 2

    # ----- A* -----
    def astar(self, net, w, starts, goal, free, allow_via=True, layers_ok=('F', 'B'), max_expand=3_000_000):
        """starts: [(L, i, j)]；goal: {L: bool 陣列}；free: {L: bool 陣列}。回傳 [(L, i, j), ...] 或 None。"""
        LI = {'F': 0, 'B': 1}
        gl = [goal['F'], goal['B']]
        fr = [free['F'] if 'F' in layers_ok else np.zeros_like(free['F']),
              free['B'] if 'B' in layers_ok else np.zeros_like(free['B'])]
        viaok = self._via_ok if allow_via else None
        gi = np.argwhere(gl[0] | gl[1])
        if len(gi) == 0: return None
        gy0, gx0 = gi.min(0); gy1, gx1 = gi.max(0)
        def h(i, j):
            dy = 0 if gy0 <= i <= gy1 else min(abs(i - gy0), abs(i - gy1))
            dx = 0 if gx0 <= j <= gx1 else min(abs(j - gx0), abs(j - gx1))
            return max(dx, dy) + 0.414 * min(dx, dy)
        best = {}
        came = {}
        pq = []
        for L, i, j in starts:
            s = (LI[L], i, j)
            best[s] = 0.0
            heapq.heappush(pq, (h(i, j), 0.0, s))
            came[s] = None
        moves = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
        n = 0
        while pq:
            f, gc, s = heapq.heappop(pq)
            if gc > best.get(s, 1e18) + 1e-9: continue
            l, i, j = s
            if gl[l][i, j]:
                path = []
                while s is not None:
                    path.append(('FB'[s[0]], s[1], s[2])); s = came[s]
                return path[::-1]
            n += 1
            if n > max_expand: return None
            k = 1.0 if l == 0 else BOTTOM_COST
            for di, dj, c in moves:
                ii, jj = i + di, j + dj
                if not (0 <= ii < NY and 0 <= jj < NX): continue
                if not fr[l][ii, jj]: continue
                ng = gc + c * k
                t = (l, ii, jj)
                if ng < best.get(t, 1e18):
                    best[t] = ng; came[t] = s
                    heapq.heappush(pq, (ng + h(ii, jj), ng, t))
            if viaok is not None and viaok[i, j]:
                t = (1 - l, i, j)
                if fr[1 - l][i, j]:
                    ng = gc + VIA_COST
                    if ng < best.get(t, 1e18):
                        best[t] = ng; came[t] = s
                        heapq.heappush(pq, (ng + h(i, j), ng, t))
        return None

    # ----- 拉直 -----
    def los(self, free, a, b):
        (i0, j0), (i1, j1) = a, b
        n = int(max(abs(i1 - i0), abs(j1 - j0)) * 2) + 1
        for t in np.linspace(0, 1, n + 1):
            i = int(round(i0 + (i1 - i0) * t)); j = int(round(j0 + (j1 - j0) * t))
            if not free[i, j]: return False
        return True

    def simplify(self, seg, free):
        """seg: [(i, j)]（同一層）。貪婪拉直，只用 0°/45°/90° 以外的任意角也可以。"""
        if len(seg) <= 2: return seg
        out = [seg[0]]
        k = 0
        while k < len(seg) - 1:
            m = len(seg) - 1
            while m > k + 1 and not self.los(free, seg[k], seg[m]):
                m -= 1
            out.append(seg[m]); k = m
        return out

    # ----- 佈一個網路 -----
    def route_net(self, net, w=None, order=None, log=True, seq=False):
        """seq=True：照 order 的順序接（不重新依距離排序）。"""
        w = w or WIDTH.get(net, DEFAULT_W)
        pads = [p for p in B.PADS if p.net == net and p.kind != 'npth']
        if order: pads.sort(key=order)
        if len(pads) < 2: return True
        cf = self.clearance_field(net)
        need = w / 2 + CLR
        free = {L: cf[L] >= need for L in 'FB'}
        vneed = VIA_PAD / 2 + CLR
        self._via_ok = (cf['F'] >= vneed) & (cf['B'] >= vneed) & self._via_drill_ok(net)
        # 樹：先放第一個焊墊
        tree = {L: np.zeros((NY, NX), bool) for L in 'FB'}
        def mark_pad(p):
            g = pad_geom(p)
            minx, miny, maxx, maxy = g.bounds
            i0, j0 = self.xy_cell(minx, maxy); i1, j1 = self.xy_cell(maxx, miny)
            cells = []
            for i in range(max(i0 - 1, 0), min(i1 + 2, NY)):
                for j in range(max(j0 - 1, 0), min(j1 + 2, NX)):
                    x, y = self.cell_xy(i, j)
                    if g.contains(Point(x, y)):
                        cells.append((i, j))
            if not cells:
                cells = [self.xy_cell(p.x, p.y)]
            layers = 'FB' if p.kind == 'tht' else 'F'
            return [(L, i, j) for L in layers for i, j in cells]
        first = pads[0]
        for L, i, j in mark_pad(first):
            tree[L][i, j] = True
        # 已經有的同網路銅（例如預先佈好的主幹）：和第一個焊墊相連的部分也算樹
        self._grow_tree(net, tree)
        ok = True
        rest = pads[1:]
        # 由近到遠接
        while rest:
            if not seq:
                tx = np.argwhere(tree['F'] | tree['B'])
                cy, cx = tx.mean(0)
                rest.sort(key=lambda p: (self.xy_cell(p.x, p.y)[0] - cy) ** 2 + (self.xy_cell(p.x, p.y)[1] - cx) ** 2)
            p = rest.pop(0)
            st = mark_pad(p)
            self._grow_tree(net, tree)
            if any(tree[L][i, j] for L, i, j in st):
                continue
            wc = w
            small = min(p.w, p.h)
            if small < w:
                wc = max(DEFAULT_W, small)
            fr = free if wc == w else {L: cf[L] >= wc / 2 + CLR for L in 'FB'}
            for L, i, j in st:
                fr[L][i, j] = True
            for L in 'FB':
                fr[L] |= tree[L]
            layers_ok = ('F', 'B')
            path = self.astar(net, wc, st, tree, fr, layers_ok=layers_ok)
            if path is None:
                if log: print(f'  ✗ {net}: {p.ref}.{p.name} 接不上')
                ok = False
                continue
            self.commit(net, wc, path, fr)
            for L, i, j in st:
                tree[L][i, j] = True
            for L, i, j in path:
                tree[L][i, j] = True
            # 通孔兩層都算
        if log: print(f'  ✓ {net}' if ok else f'  ~ {net}（部分）')
        return ok

    def _grow_tree(self, net, tree):
        """把和樹相連的同網路銅（兩層，經過孔/通孔相連）都加進樹。"""
        from scipy.ndimage import label
        own = self.own_mask(net)
        st8 = np.ones((3, 3), int)
        labs = {L: label(own[L], structure=st8)[0] for L in 'FB'}
        links = [(self.xy_cell(x, y)) for x, y, dw, dh, pl, n in self.drills if pl and n == net]
        seeds = {L: set(np.unique(labs[L][tree[L] & own[L]])) - {0} for L in 'FB'}
        changed = True
        while changed:
            changed = False
            for i, j in links:
                a, b = labs['F'][i, j], labs['B'][i, j]
                if a and b:
                    if a in seeds['F'] and b not in seeds['B']: seeds['B'].add(b); changed = True
                    if b in seeds['B'] and a not in seeds['F']: seeds['F'].add(a); changed = True
        for L in 'FB':
            if seeds[L]:
                tree[L] |= np.isin(labs[L], list(seeds[L]))

    def _via_drill_ok(self, net):
        """過孔鑽孔要離其他鑽孔夠遠（孔壁 ≥ 0.4 mm）。"""
        m = np.ones((NY, NX), bool)
        for x, y, dw, dh, pl, n in self.drills:
            r = max(dw, dh) / 2 + VIA_DRILL / 2 + 0.4
            i, j = self.xy_cell(x, y)
            k = int(r / G) + 1
            for ii in range(max(i - k, 0), min(i + k + 1, NY)):
                for jj in range(max(j - k, 0), min(j + k + 1, NX)):
                    cx, cy = self.cell_xy(ii, jj)
                    if (cx - x) ** 2 + (cy - y) ** 2 < r * r: m[ii, jj] = False
        for kb in VIA_KEEPOUTS:
            i0, j0 = self.xy_cell(kb.bounds[0], kb.bounds[3]); i1, j1 = self.xy_cell(kb.bounds[2], kb.bounds[1])
            m[max(i0, 0):i1 + 1, max(j0, 0):j1 + 1] = False
        # 不在同網路的 SMD 焊墊上打孔（避免吃錫）；其他網路由距離場處理
        for f in self.feats:
            if f.kind == 'smd' and f.net == net:
                g = f.geom.buffer(VIA_PAD / 2)
                i0, j0 = self.xy_cell(g.bounds[0], g.bounds[3]); i1, j1 = self.xy_cell(g.bounds[2], g.bounds[1])
                m[max(i0, 0):i1 + 1, max(j0, 0):j1 + 1] = False
        return m

    def commit(self, net, w, path, free):
        # 依層切段，換層處放過孔
        segs, cur = [], [path[0]]
        for a in path[1:]:
            if a[0] != cur[-1][0]:
                segs.append(cur); cur = [a]
            else:
                cur.append(a)
        segs.append(cur)
        for k, sg in enumerate(segs):
            L = sg[0][0]
            ij = [(i, j) for _, i, j in sg]
            ij = self.simplify(ij, free[L])
            pts = [self.cell_xy(i, j) for i, j in ij]
            self.add_track(L, net, pts, w)
            if k > 0:
                x, y = self.cell_xy(sg[0][1], sg[0][2])
                self.add_via(x, y, net)

    # ----- GND -----
    def gnd_fanout(self, refs=None, w=None):
        """每個 GND 焊墊（正面）往外拉一小段，打一個過孔到背面的 GND 鋪銅。"""
        net = 'GND'
        done = 0
        for p in [p for p in B.PADS if p.net == 'GND' and p.kind == 'smd' and (refs is None or (p.ref, p.name) in refs or p.ref in refs)]:
            w = min(WIDTH['GND'], max(DEFAULT_W, min(p.w, p.h)))
            cf = self.clearance_field(net)
            free = {L: cf[L] >= w / 2 + CLR for L in 'FB'}
            viaok = (cf['F'] >= VIA_PAD / 2 + CLR) & (cf['B'] >= VIA_PAD / 2 + CLR) & self._via_drill_ok(net)
            g = pad_geom(p)
            # 大焊墊（模組 GND、插座）直接在焊墊旁邊找點
            i0, j0 = self.xy_cell(p.x, p.y)
            best = None
            # BFS（正面）
            from collections import deque
            q = deque([(i0, j0)]); seen = {(i0, j0): None}
            while q:
                i, j = q.popleft()
                x, y = self.cell_xy(i, j)
                if viaok[i, j] and not g.buffer(VIA_PAD / 2 + 0.02).contains(Point(x, y)):
                    best = (i, j); break
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    ii, jj = i + di, j + dj
                    if (ii, jj) in seen or not (0 <= ii < NY and 0 <= jj < NX): continue
                    xx, yy = self.cell_xy(ii, jj)
                    if not (free['F'][ii, jj] or g.contains(Point(xx, yy))): continue
                    if len(seen) > 40000: continue
                    seen[(ii, jj)] = (i, j); q.append((ii, jj))
            if best is None:
                print('  ✗ GND 扇出失敗', p.ref, p.name); continue
            path = []
            s = best
            while s is not None:
                path.append(s); s = seen[s]
            path = path[::-1]
            pts = [(p.x, p.y)] + [self.cell_xy(i, j) for i, j in self.simplify(path, free['F'] | self._pad_cells(g))][1:]
            self.add_track('F', net, pts, w)
            self.add_via(*pts[-1], net)
            done += 1
        print(f'  GND 扇出 {done} 個')

    def _pad_cells(self, g):
        m = np.zeros((NY, NX), bool)
        minx, miny, maxx, maxy = g.bounds
        i0, j0 = self.xy_cell(minx, maxy); i1, j1 = self.xy_cell(maxx, miny)
        for i in range(max(i0, 0), min(i1 + 1, NY)):
            for j in range(max(j0, 0), min(j1 + 1, NX)):
                if g.contains(Point(*self.cell_xy(i, j))): m[i, j] = True
        return m

    def pour(self, layer, net='GND', clr=0.25, min_area=0.6):
        """在某層鋪 GND：板內扣掉其他網路（加間距）、板邊、孔、天線區。"""
        others = unary_union([f.geom for f in self.feats if f.layer == layer and f.net != net]).buffer(clr, 12)
        area = B.BOARD.buffer(-EDGE_CLR - 0.05)
        area = area.difference(others)
        area = area.difference(unary_union([h.buffer(HOLE_CLR + 0.05) for h in self.hole_geoms]))
        area = area.difference(B.ANT_KEEPOUT.buffer(0.1))
        # 太細的頸部去掉（開閉運算）
        area = area.buffer(-0.12, 8).buffer(0.12, 8)
        own = unary_union([f.geom for f in self.feats if f.layer == layer and f.net == net])
        polys = list(area.geoms) if hasattr(area, 'geoms') else [area]
        keep = [pg for pg in polys if pg.area >= min_area and pg.intersects(own)]
        return unary_union(keep)

    def stitch(self, top, bot, pitch=3.0):
        """兩面都有 GND 鋪銅的地方，每隔 pitch 打一個縫合過孔。"""
        both = top.intersection(bot).buffer(-(VIA_PAD / 2 + 0.05))
        cnt = 0
        minx, miny, maxx, maxy = B.BOARD.bounds
        y = miny + pitch / 2
        while y < maxy:
            x = minx + pitch / 2
            while x < maxx:
                if both.contains(Point(x, y)):
                    okd = all(math.hypot(x - dx, y - dy) - max(dw, dh) / 2 - VIA_DRILL / 2 >= 0.5 for dx, dy, dw, dh, *_ in self.drills)
                    okh = all(Point(x, y).distance(h) > 0.6 for h in self.hole_geoms)
                    if okd and okh:
                        self.add_via(x, y, 'GND'); cnt += 1
                x += pitch
            y += pitch
        return cnt
