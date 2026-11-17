"""載板支柱（3D 列印）：取代原本的 ESP32 支架。
四根柱子位置、高度與原支架柱腳相同（機身頂面 z = 3 起算 8 mm），底部用 2 mm 高的框連在一起，方便對位。
柱子中心有 1.6 mm 貫穿孔：下面用原本的 M1.4×5 從機身底面鎖上來，上面再用 M1.4×5 把載板鎖下去。"""
import os
import numpy as np, trimesh
import manifold3d as mf
from design import MOUNT_HOLES

H, POST, BAR_W, BAR_H, HOLE = 8.0, 4.0, 2.0, 2.0, 1.6

def cube(x0, y0, z0, x1, y1, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

solid = mf.Manifold()
for x, y in MOUNT_HOLES:
    solid += cube(x - POST / 2, y - POST / 2, 0, x + POST / 2, y + POST / 2, H)
X, Y = 13.51, 17.5
solid += cube(-X, Y - BAR_W / 2, 0, X, Y + BAR_W / 2, BAR_H)
solid += cube(-X, -Y - BAR_W / 2, 0, X, -Y + BAR_W / 2, BAR_H)
solid += cube(X - BAR_W / 2, -Y, 0, X + BAR_W / 2, Y, BAR_H)
solid += cube(-X - BAR_W / 2, -Y, 0, -X + BAR_W / 2, Y, BAR_H)
for x, y in MOUNT_HOLES:
    solid -= mf.Manifold.cylinder(H + 2, HOLE / 2, HOLE / 2, 48).translate([x, y, -1])
m = solid.to_mesh()
mesh = trimesh.Trimesh(vertices=np.array(m.vert_properties)[:, :3], faces=np.array(m.tri_verts))
out = os.path.join(os.path.dirname(__file__), 'fab', 'carrier-posts.stl')
mesh.export(out)
print('watertight', mesh.is_watertight, 'volume %.0f mm3' % mesh.volume, 'bounds', mesh.bounds.round(2).tolist(), '≈ %.1f g PLA(100%%)' % (mesh.volume * 1.24e-3))
