"""產生教學頁 3D 用的一體板資料：板子外形、正反面貼圖（由 Gerber 算出的 preview 裁切）、每個零件的位置與尺寸。
輸出 ../src/onboard_data.js（產生的檔案，要進 repo，重建頁面時不用再跑這支）。
先跑 verify.py 產生 preview/render_top.png、render_bottom.png。"""
import os, io, json, base64
from PIL import Image
import board as B
import export as E

HERE = os.path.dirname(os.path.abspath(__file__))
DP = 20
X0, X1 = min(x for x, _ in B.OUTLINE), max(x for x, _ in B.OUTLINE)
Y0, Y1 = min(y for _, y in B.OUTLINE), max(y for _, y in B.OUTLINE)


def crop(name, flip):
    im = Image.open(os.path.join(HERE, 'preview', name)).convert('RGB')
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)   # render_bottom 是從背面看（鏡射），轉回機身座標
    fx0, fy1 = E.FRAME[0], E.FRAME[3]
    box = (round((X0 - fx0) * DP), round((fy1 - Y1) * DP), round((X1 - fx0) * DP), round((fy1 - Y0) * DP))
    im = im.crop(box)
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=88)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


comps = []
for c in B.COMPS:
    segs = B.FABS.get(c['ref']) or []
    pts = [p for s in segs for p in s]
    if not pts:
        continue
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    comps.append(dict(ref=c['ref'], part=c['part'], fp=c['fp'], x=round(c['x'], 3), y=round(c['y'], 3), rot=c['rot'],
                      bx=[round(min(xs), 3), round(max(xs), 3)], by=[round(min(ys), 3), round(max(ys), 3)], note=c['note']))

data = dict(outline=[[round(x, 3), round(y, 3)] for x, y in B.OUTLINE], holes=B.MOUNT_HOLES, holeD=B.MOUNT_D,
            thick=B.BOARD_T, bbox=[X0, X1, Y0, Y1], comps=comps,
            texTop=crop('render_top.png', False), texBottom=crop('render_bottom.png', True))
out = os.path.join(HERE, '..', 'src', 'onboard_data.js')
with open(out, 'w', encoding='utf-8') as f:
    f.write('// 由 pcb2/export3d.py 產生，請勿手改\nexport const OB = ' + json.dumps(data, ensure_ascii=False) + ';\n')
print(out, os.path.getsize(out), 'bytes,', len(comps), 'comps')
for c in comps:
    print(c['ref'], c['part'], c['rot'], 'w=%.2f d=%.2f' % (c['bx'][1] - c['bx'][0], c['by'][1] - c['by'][0]), 'at', (c['x'], c['y']))
