"""獨立驗證：用 pygerber 把輸出的 Gerber 算成圖，跟設計資料的銅箔逐像素比對；再合成上下視圖給人看。"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from pygerber.gerberx3.api.v2 import GerberFile, ColorScheme, PixelFormatEnum, ImageFormatEnum
from shapely.ops import unary_union
from design import *
import layout as L
import silk

DP = 20
BW, BH = 46.0, 45.5
W, H = int(BW * DP), int(BH * DP)
G = os.path.join(os.path.dirname(__file__), 'fab', 'gerber')
P = os.path.join(os.path.dirname(__file__), 'preview')
os.makedirs(P, exist_ok=True)

def raster_gerber(fn):
    path = os.path.join(G, f'fz-flix-carrier-{fn}')
    parsed = GerberFile.from_file(path).parse()
    info = parsed.get_info()
    tmp = os.path.join(P, '_tmp.png')
    parsed.render_raster(tmp, dpmm=DP, color_scheme=ColorScheme.COPPER_ALPHA, pixel_format=PixelFormatEnum.RGBA, image_format=ImageFormatEnum.PNG)
    a = np.array(Image.open(tmp).split()[3]) > 127
    full = np.zeros((H, W), bool)
    x0 = int(round(float(info.min_x_mm) * DP)); top = int(round((BH - float(info.max_y_mm)) * DP))
    h, w = a.shape
    full[top:top + h, x0:x0 + w] |= a[:H - top, :W - x0]
    return full

def raster_geom(geom):
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    def tr(c): return [((x + OFF[0]) * DP, (BH - (y + OFF[1])) * DP) for x, y in c]
    polys = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
    polys.sort(key=lambda p: -p.envelope.area)      # 大的先畫，洞裡的小塊後畫
    for p in polys:
        if p.geom_type != 'Polygon': continue
        d.polygon(tr(p.exterior.coords), fill=255)
        for r in p.interiors: d.polygon(tr(r.coords), fill=0)
    return np.array(im) > 127

def compare(name, a, b):
    diff = a ^ b
    # 邊緣 1 像素的差異是算圖取樣造成的，先侵蝕掉
    from scipy.ndimage import binary_erosion
    from scipy.ndimage import label
    core = binary_erosion(diff, iterations=1)
    lab, n = label(core)
    sizes = np.bincount(lab.ravel())[1:]
    big = int((sizes > 2).sum())          # 只算超過 2 像素（0.1 mm）的差異塊；單點是圓弧取樣誤差
    print(f'{name}: 設計 {b.sum()} px，Gerber {a.sum()} px；超過 0.1 mm 的差異 {big} 處（單點取樣誤差 {n - big} 個）')
    return big

def main():
    bad = 0
    for layer, fn in (('F', 'F_Cu.gtl'), ('B', 'B_Cu.gbl')):
        a = raster_gerber(fn)
        b = raster_geom(unary_union([f.geom for f in L.FEATS if f.layer == layer]))
        bad += compare(fn, a, b)
    for layer, fn in (('F', 'F_Silkscreen.gto'), ('B', 'B_Silkscreen.gbo')):
        bad += compare(fn, raster_gerber(fn), raster_geom(silk.clipped(layer)))
    # 合成圖（綠色防焊、金色焊墊、白色絲印、黑色孔）
    for side, cu, mk, sk in (('top', 'F_Cu.gtl', 'F_Mask.gts', 'F_Silkscreen.gto'), ('bottom', 'B_Cu.gbl', 'B_Mask.gbs', 'B_Silkscreen.gbo')):
        board = raster_geom(BOARD)
        cuA, mkA, skA = raster_gerber(cu), raster_gerber(mk), raster_gerber(sk)
        img = np.zeros((H, W, 3), np.uint8); img[:] = (250, 250, 250)
        img[board] = (22, 92, 52)
        img[board & cuA] = (40, 130, 70)
        img[board & mkA & cuA] = (214, 180, 90)
        img[board & mkA & ~cuA] = (190, 170, 120)
        img[skA] = (245, 245, 245)
        hole = Image.new('L', (W, H), 0); d = ImageDraw.Draw(hole)
        for x, y, dd, *_ in L.DRILLS + [(x, y, MOUNT_D) for x, y in MOUNT_HOLES]:
            cx, cy = (x + OFF[0]) * DP, (BH - (y + OFF[1])) * DP; r = dd / 2 * DP
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        img[np.array(hole) > 0] = (20, 20, 20)
        im = Image.fromarray(img)
        if side == 'bottom': im = im.transpose(Image.FLIP_LEFT_RIGHT)   # 從背面看
        im.save(os.path.join(P, f'render_{side}.png'))
    os.remove(os.path.join(P, '_tmp.png'))
    print('比對結果：', '一致' if bad == 0 else f'有 {bad} px 不一致')
    return bad

if __name__ == '__main__':
    sys.exit(1 if main() else 0)
