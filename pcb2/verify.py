"""獨立驗證：用 pygerber 把 Gerber 算成圖，和設計資料的銅箔逐像素比對；再合成上下視圖。"""
import os, sys, pickle
import numpy as np
from PIL import Image, ImageDraw
from pygerber.gerberx3.api.v2 import GerberFile, ColorScheme, PixelFormatEnum, ImageFormatEnum
from shapely.ops import unary_union
from scipy.ndimage import binary_erosion, label
import board as B
import export as E
import silk

DP = 20
BW, BH = E.FRAME[2] - E.FRAME[0], E.FRAME[3] - E.FRAME[1]
W, H = int(BW * DP), int(BH * DP)
G = E.GERB
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preview')
os.makedirs(P, exist_ok=True)

def raster_gerber(fn):
    path = os.path.join(G, f'{B.NAME}-{fn}')
    parsed = GerberFile.from_file(path).parse()
    info = parsed.get_info()
    tmp = os.path.join(P, '_tmp.png')
    parsed.render_raster(tmp, dpmm=DP, color_scheme=ColorScheme.COPPER_ALPHA, pixel_format=PixelFormatEnum.RGBA, image_format=ImageFormatEnum.PNG)
    a = np.array(Image.open(tmp).split()[3]) > 127
    full = np.zeros((H, W), bool)
    x0 = int(round(float(info.min_x_mm) * DP)); top = int(round((BH - float(info.max_y_mm)) * DP))
    h, w = a.shape
    hh, ww = min(h, H - top), min(w, W - x0)
    full[top:top + hh, x0:x0 + ww] |= a[:hh, :ww]
    return full

def raster_geom(geom):
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    def tr(c): return [((x + E.OFF[0]) * DP, (BH - (y + E.OFF[1])) * DP) for x, y in c]
    polys = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
    polys = [p for p in polys if p.geom_type == 'Polygon']
    polys.sort(key=lambda p: -p.envelope.area)
    for p in polys:
        d.polygon(tr(p.exterior.coords), fill=255)
        for r in p.interiors: d.polygon(tr(r.coords), fill=0)
    return np.array(im) > 127

def compare(name, a, b):
    diff = a ^ b
    core = binary_erosion(diff, iterations=1)
    lab, n = label(core)
    sizes = np.bincount(lab.ravel())[1:]
    big = int((sizes > 2).sum())
    print(f'{name}: 設計 {b.sum()} px，Gerber {a.sum()} px；超過 0.1 mm 的差異 {big} 處')
    return big

def main():
    R = pickle.load(open('/tmp/final.pkl', 'rb'))
    bad = 0
    from shapely.geometry import Point
    for layer, fn in (('F', 'F_Cu.gtl'), ('B', 'B_Cu.gbl')):
        a = raster_gerber(fn)
        geoms = [f.geom for f in R.feats if f.layer == layer]
        if layer == 'F': geoms += [Point(x, y).buffer(E.FID_CU / 2, 32) for x, y in E.FIDUCIALS]
        b = raster_geom(unary_union(geoms))
        bad += compare(fn, a, b)
    mat = E.material()
    for side, cu, mk, sk in (('top', 'F_Cu.gtl', 'F_Mask.gts', 'F_Silkscreen.gto'), ('bottom', 'B_Cu.gbl', 'B_Mask.gbs', 'B_Silkscreen.gbo')):
        board = raster_geom(mat)
        cuA, mkA, skA = raster_gerber(cu), raster_gerber(mk), raster_gerber(sk)
        img = np.zeros((H, W, 3), np.uint8); img[:] = (250, 250, 250)
        img[board] = (22, 92, 52)
        img[board & cuA] = (40, 130, 70)
        img[board & mkA & cuA] = (214, 180, 90)
        img[board & mkA & ~cuA] = (190, 170, 120)
        img[skA] = (245, 245, 245)
        hole = Image.new('L', (W, H), 0); d = ImageDraw.Draw(hole)
        holes = [(x, y, max(dw, dh)) for x, y, dw, dh, *_ in R.drills] + [(x, y, B.MOUNT_D) for x, y in B.MOUNT_HOLES]
        holes += [(x, y, E.TOOLING_D) for x, y in E.TOOLING] + [(x, y, E.BITE_D) for x, y in E.mouse_bites()]
        for x, y, dd in holes:
            cx, cy = (x + E.OFF[0]) * DP, (BH - (y + E.OFF[1])) * DP; r = dd / 2 * DP
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        img[np.array(hole) > 0] = (20, 20, 20)
        im = Image.fromarray(img)
        if side == 'bottom': im = im.transpose(Image.FLIP_LEFT_RIGHT)
        im.save(os.path.join(P, f'render_{side}.png'))
    os.remove(os.path.join(P, '_tmp.png'))
    print('比對結果：', '一致' if bad == 0 else f'有 {bad} 處不一致')
    return bad

if __name__ == '__main__':
    sys.exit(1 if main() else 0)
