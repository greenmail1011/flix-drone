"""擺放預覽：外框、元件外框、焊墊（依網路著色）。"""
import sys
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box, Polygon
from shapely import affinity
import board as B
DP = 20
X0, Y1 = -26, 22
W, H = int(52 * DP), int(52 * DP)
def tr(x, y): return ((x - X0) * DP, (Y1 - y) * DP)
def padpoly(p):
    g = box(-p.w / 2, -p.h / 2, p.w / 2, p.h / 2)
    g = affinity.rotate(g, p.rot, origin=(0, 0))
    return affinity.translate(g, p.x, p.y)
def draw(fn, extra=None):
    im = Image.new('RGB', (W, H), (245, 245, 245)); d = ImageDraw.Draw(im)
    d.polygon([tr(*c) for c in B.BOARD.exterior.coords], fill=(30, 90, 50))
    d.polygon([tr(*c) for c in B.ANT_KEEPOUT.intersection(B.BOARD).exterior.coords], fill=(70, 70, 120))
    for x, y in B.MOUNT_HOLES:
        cx, cy = tr(x, y); r = B.MOUNT_D / 2 * DP; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0))
    if extra: extra(d, tr)
    for r, p in B.COURTS.items():
        d.line([tr(*c) for c in p.exterior.coords], fill=(255, 255, 0), width=1)
    font = ImageFont.load_default()
    for p in B.PADS:
        col = (200, 160, 60) if p.net and not p.net.startswith('NC') else (120, 120, 120)
        if p.net == 'GND': col = (60, 160, 230)
        if p.net in ('VBAT',): col = (230, 60, 60)
        if p.kind == 'npth': col = (0, 0, 0)
        d.polygon([tr(*c) for c in padpoly(p).exterior.coords], fill=col)
    for c in B.COMPS:
        d.text(tr(c['x'], c['y']), c['ref'], fill=(255, 255, 255), font=font)
    im.save(fn)
if __name__ == '__main__':
    draw(sys.argv[1] if len(sys.argv) > 1 else '/tmp/place.png')
