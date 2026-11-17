import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { MESH, QS } from './meshes.js';
import { wiringSVG, wiringTableHTML } from './wiring.js';
import { PARTS, STEPS, WIRES, WIRE_GROUPS, MOTORS, MINI_COLS, MINI_PINS, COL_NAME, IMU_PINS, pinY, pinName, pinWhere, motorWires } from './data.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const P = Object.fromEntries(PARTS.map(p => [p.id, p]));
const FONT = '"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif';

// ---------- renderer / scene ----------
const view = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
const SMALL = Math.min(screen.width, screen.height) < 700;
renderer.setPixelRatio(Math.min(devicePixelRatio, SMALL ? 1.5 : 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
view.appendChild(renderer.domElement);
renderer.domElement.addEventListener('webglcontextlost', e => {
  e.preventDefault();
  const m = document.createElement('div'); m.className = 'lost';
  m.innerHTML = '3D 畫面被瀏覽器關掉了（通常是記憶體不足）。<button onclick="location.reload()">重新載入</button>';
  view.appendChild(m);
});

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xeef1f5);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const camera = new THREE.PerspectiveCamera(32, 1, 1, 4000);
camera.up.set(0, 0, 1);
camera.position.set(170, -210, 150);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 0, 0);

scene.add(new THREE.HemisphereLight(0xffffff, 0x9aa3ad, 0.6));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(90, -120, 260);
sun.castShadow = true;
sun.shadow.mapSize.set(SMALL ? 1024 : 2048, SMALL ? 1024 : 2048);
Object.assign(sun.shadow.camera, { left: -150, right: 150, top: 150, bottom: -150, near: 10, far: 600 });
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.4;
scene.add(sun);

const FLOOR = -15.05;
const ground = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), new THREE.ShadowMaterial({ opacity: 0.16 }));
ground.position.z = FLOOR; ground.receiveShadow = true; scene.add(ground);
const grid = new THREE.GridHelper(400, 40, 0xc3cad3, 0xd9dee5);
grid.rotation.x = Math.PI / 2; grid.position.z = FLOOR - 0.05; scene.add(grid);

// ---------- helpers ----------
const mat = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.05, ...o });
const metal = (color, r = 0.28) => mat(color, { metalness: 1, roughness: r });
function box(w, d, h, m, x = 0, y = 0, z = 0) { // z = 底面高度
  const o = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), m); o.position.set(x, y, z + h / 2); return o;
}
function cyl(r, h, m, x = 0, y = 0, z = 0, seg = 32, r2 = r) { // 沿 z 軸，z = 底面
  const g = new THREE.CylinderGeometry(r2, r, h, seg); g.rotateX(Math.PI / 2);
  const o = new THREE.Mesh(g, m); o.position.set(x, y, z + h / 2); return o;
}
function canvasTex(w, h, draw, px = 12) {
  const c = document.createElement('canvas'); c.width = w * px; c.height = h * px;
  const g = c.getContext('2d'); g.scale(px, px); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}
// 上表面貼圖的板子：box 的 +z 面用 canvas
function board(w, d, h, base, draw, x = 0, y = 0, z = 0, mOpt = {}) {
  const side = mat(base, { roughness: 0.6, ...mOpt });
  const top = new THREE.MeshStandardMaterial({ map: canvasTex(w, d, draw), roughness: 0.5, ...mOpt });
  const o = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), [side, side, side, side, top, side]);
  o.position.set(x, y, z + h / 2); return o;
}
function tube(pts, r, color) {
  const curve = new THREE.CatmullRomCurve3(pts.map(p => V(...p)), false, 'centripetal');
  return new THREE.Mesh(new THREE.TubeGeometry(curve, Math.max(24, pts.length * 14), r, 8, false),
    mat(color, { roughness: 0.45 }));
}
function stlMesh(key, m) {
  const d = MESH[key];
  const bin = s => Uint8Array.from(atob(s), c => c.charCodeAt(0)).buffer;
  const q = new Int16Array(bin(d.p)), pos = new Float32Array(q.length);
  for (let i = 0; i < q.length; i++) pos[i] = q[i] * QS;
  const ib = bin(d.i), idx = d.n < 65535 ? new Uint16Array(ib) : new Uint32Array(ib);
  let g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setIndex(new THREE.BufferAttribute(idx, 1));
  g = g.toNonIndexed(); g.computeVertexNormals();
  return new THREE.Mesh(g, m);
}

// ---------- geometry constants (from the official STL) ----------
const ARM = 42.43;               // 馬達管中心（Gazebo 模型 flix.sdf 也是 ±42.43 mm）
const IMU_HOLES = [[-1.25, -6.30], [-1.25, 8.94]];
const POSTS = [[13.51, 17.5], [-13.51, 17.5], [13.51, -17.5], [-13.51, -17.5]];
const HOLDER_Z = 11;             // 支架柱底 = 機身頂面 3 mm
const HOLDER_TOP = 12.6;
const TAPE_T = 1.0;
const BOARD_Z = HOLDER_TOP + TAPE_T;
const MINI_T = 1.0;              // MINI32 板厚
const UNDER = 10.2;              // 支架平台下方的走線高度（平台底 11 mm）

// ---------- part registry ----------
// item: {id, obj, base, ex (自由拆解位移), appear (出現的步驟), keys [[step, offset]], entry (進場位移)}
const items = [];
function add(id, obj, base, { ex = V(), step = 1, keys = null, entry = null, shadow = true } = {}) {
  obj.position.copy(base);
  obj.traverse(o => { o.userData.partId = id; if (o.isMesh) { o.castShadow = shadow; o.receiveShadow = true; } });
  scene.add(obj);
  const it = { id, obj, base: base.clone(), ex, appear: step, keys: keys || [[step, V()]], entry: entry || ex.clone().multiplyScalar(0.7), off: V() };
  items.push(it); return it;
}

// PCB：真的挖孔的板子。上下兩面各貼一張 canvas 貼圖（下面那張要左右鏡射畫）。
function pcb({ W, L, T, outline, holes, color, top, bottom, px = 24 }) {
  const shape = new THREE.Shape();
  outline.forEach(([x, y], i) => i ? shape.lineTo(x, y) : shape.moveTo(x, y));
  holes.forEach(([x, y, r]) => { const h = new THREE.Path(); h.absarc(x, y, r, 0, Math.PI * 2, true); shape.holes.push(h); });
  const g = new THREE.Group();
  const edge = mat(color, { roughness: 0.6 });
  const body = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: T, bevelEnabled: false, curveSegments: 16 }), [edge, edge]);
  g.add(body);
  const face = (draw, z, side) => {
    const t = canvasTex(W, L, draw, px); t.repeat.set(1 / W, 1 / L); t.offset.set(0.5, 0.5);
    const m = new THREE.Mesh(new THREE.ShapeGeometry(shape, 16), new THREE.MeshStandardMaterial({ map: t, roughness: 0.48, side }));
    m.position.z = z; g.add(m); return m;
  };
  if (top) face(top, T + 0.01, THREE.FrontSide);
  if (bottom) face((c, w, h) => { c.translate(w, 0); c.scale(-1, 1); bottom(c, w, h); }, -0.01, THREE.BackSide);
  return g;
}
const rectOutline = (W, L, ch = 0) => [[-W / 2 + ch, -L / 2], [W / 2 - ch, -L / 2], [W / 2, -L / 2 + ch], [W / 2, L / 2 - ch], [W / 2 - ch, L / 2], [-W / 2 + ch, L / 2], [-W / 2, L / 2 - ch], [-W / 2, -L / 2 + ch]];
function roundOutline(W, L, r, n = 6) {
  const pts = [];
  [[W / 2 - r, L / 2 - r, 0], [-W / 2 + r, L / 2 - r, 90], [-W / 2 + r, -L / 2 + r, 180], [W / 2 - r, -L / 2 + r, 270]].forEach(([cx, cy, a0]) => {
    for (let i = 0; i <= n; i++) { const a = (a0 + 90 * i / n) * Math.PI / 180; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
  });
  return pts;
}
// 常用 SMD 小零件
const smdR = (x, y, rot = 0, w = 1.6, d = 0.8, h = 0.45, body = 0x1e1e1e) => {
  const g = new THREE.Group();
  g.add(box(w - 0.5, d, h, mat(body, { roughness: 0.4 }), 0, 0, 0));
  [-1, 1].forEach(s => g.add(box(0.25, d, h, metal(0xd9dcdf, 0.3), s * (w / 2 - 0.125), 0, 0)));
  g.position.set(x, y, 0); g.rotation.z = rot; return g;
};
const smdC = (x, y, rot = 0, w = 1.6, d = 0.8) => smdR(x, y, rot, w, d, 0.8, 0xb59a6a);
function sot(x, y, rot, legsA, legsB, label = '', w = 2.9, d = 1.6) {
  const g = new THREE.Group();
  const top = board(w, d, 1.0, 0x161616, (c, ww, hh) => { c.fillStyle = '#1b1b1b'; c.fillRect(0, 0, ww, hh); c.fillStyle = '#9a9a9a'; c.font = `bold 0.6px ${FONT}`; c.textAlign = 'center'; c.fillText(label, ww / 2, hh / 2 + 0.2); }, 0, 0, 0.1, { roughness: 0.4 });
  g.add(top);
  const leg = (lx, ly) => g.add(box(0.4, 0.7, 0.15, metal(0xd9dcdf, 0.3), lx, ly, 0));
  legsA.forEach(lx => leg(lx, -d / 2 - 0.3)); legsB.forEach(lx => leg(lx, d / 2 + 0.3));
  g.position.set(x, y, 0); g.rotation.z = rot; return g;
}
function solder(x, y, z) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.75, 14, 10), metal(0xc9ccd0, 0.18)); s.scale.z = 0.55; s.position.set(x, y, z); return s; }

// ===== 1. 機身 =====
const PLA = mat(0xf3f1ea, { roughness: 0.72, side: THREE.DoubleSide });
const frame = stlMesh('frame', PLA);
add('frame', frame, V(), { step: 1, entry: V(0, 0, 40) });

// ===== 2. 支架 + 雙面膠 + ESP32（先在旁邊組好，第 7 步才移入）=====
const SIDE = V(92, 0, 18);
const holderMat = mat(0xeceae2, { roughness: 0.72, side: THREE.DoubleSide });
const holder = stlMesh('holder', holderMat);
add('holder', holder, V(0, 0, HOLDER_Z), { ex: V(0, 0, 58), step: 2, keys: [[2, SIDE], [7, V()]], entry: V(0, 0, 25) });
const tape2 = new THREE.Group();
tape2.add(box(17.5, 31, TAPE_T, mat(0xf4f0d8, { roughness: 0.95 })));
add('tape2', tape2, V(0, 0, HOLDER_TOP), { ex: V(0, 0, 66), step: 2, keys: [[2, SIDE], [7, V()]], entry: V(0, 0, 30) });

// --- MINI32（照官方照片 docs/img/esp32.jpg；腳位照 MiniKit 封裝）
const pinOverlays = [];
function makeMini32() {
  const g = new THREE.Group(), W = 31.4, L = 39, T = MINI_T;
  const holes = [];
  Object.entries(MINI_COLS).forEach(([col, x]) => { for (let r = 1; r <= 10; r++) holes.push([x, pinY(r), 0.45, col, r]); });
  const pad = (c, x, y, sq) => {        // canvas 座標
    c.fillStyle = '#e3c26b';
    if (sq) c.fillRect(x - 0.85, y - 0.85, 1.7, 1.7); else { c.beginPath(); c.arc(x, y, 0.85, 0, 7); c.fill(); }
  };
  const cx = x => x + W / 2, cy = y => L / 2 - y;
  const top = (c, w, h) => {
    c.fillStyle = '#1765a8'; c.fillRect(0, 0, w, h);
    c.strokeStyle = 'rgba(110,190,255,.28)'; c.lineWidth = 0.16;
    for (let i = 0; i < 14; i++) { c.beginPath(); c.moveTo(cx(-9), cy(-6.5 - i * 0.35)); c.lineTo(cx(-3 + i * 0.4), cy(-8 - i * 0.6)); c.lineTo(cx(-3 + i * 0.4), cy(-15)); c.stroke(); }
    for (let i = 0; i < 8; i++) { c.beginPath(); c.moveTo(cx(i < 4 ? -11.43 : 11.43), cy(pinY(i + 1) - 1.27)); c.lineTo(cx(i < 4 ? -9 : 9), cy(pinY(i + 1) - 1.27)); c.stroke(); }
    // 內排白色框（照片上的白邊）
    c.strokeStyle = '#eef3f7'; c.lineWidth = 0.32;
    [-11.43, 11.43].forEach(x => { c.beginPath(); c.roundRect(cx(x) - 1.45, cy(13.1), 2.9, 20.6, 1.45); c.stroke(); });
    holes.forEach(([x, y, , col, r]) => pad(c, cx(x), cy(y), (col === 'LI' && r === 10) || (col === 'RO' && r === 10)));
    c.fillStyle = '#f4f7fa'; c.textAlign = 'center';
    c.font = `bold 1.55px ${FONT}`; c.fillText('MINI32', cx(0), cy(-10.4));
    c.font = `bold 1.35px ${FONT}`; c.fillText('V1.0.0', cx(0), cy(-12.2));
    c.font = `bold 1.2px ${FONT}`; c.fillText('RST', cx(-11.5), cy(-12.6)); c.fillText('ON', cx(12.4), cy(-18.3));
    c.strokeStyle = '#f4f7fa'; c.lineWidth = 0.18; c.strokeRect(cx(11.0), cy(-12.9), 2.8, 4.6);
  };
  const back = (c, w, h) => {
    c.fillStyle = '#1765a8'; c.fillRect(0, 0, w, h);
    holes.forEach(([x, y, , col, r]) => pad(c, cx(x), cy(y), false));
    c.fillStyle = '#f4f7fa'; c.font = `bold 0.82px ${FONT}`;
    holes.forEach(([x, y, , col, r]) => {
      const name = MINI_PINS[col][r - 1]; c.textAlign = col[0] === 'L' ? (col === 'LO' ? 'left' : 'left') : 'right';
      const off = { LO: 1.1, LI: 1.1, RI: -1.1, RO: -1.1 }[col];
      if (col === 'LI' || col === 'RI') c.fillText(name, cx(x) + off, cy(y) + 0.3);
    });
    c.textAlign = 'center'; c.font = `bold 1.2px ${FONT}`; c.fillText('LIVE MINI KIT ESP32', cx(0), cy(16.6));
  };
  const outline = [[-W / 2, -L / 2], [W / 2, -L / 2], [W / 2, L / 2 - 2.2], [W / 2 - 2.2, L / 2], [-W / 2 + 2.2, L / 2], [-W / 2, L / 2 - 2.2]];
  g.add(pcb({ W, L, T, outline, holes, color: 0x145a96, top, bottom: back, px: 30 }));
  // ESP32-WROOM-32：黑色模組板 + 天線區 + 金屬殼
  const modY = 6.45;
  g.add(board(17.6, 24.9, 0.8, 0x111111, (c, w, h) => {
    c.fillStyle = '#121212'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#c99a3a';
    for (let i = 0; i < 14; i++) { c.fillRect(0, 7.3 + i * 1.27, 0.55, 0.85); c.fillRect(w - 0.55, 7.3 + i * 1.27, 0.55, 0.85); }
    for (let i = 0; i < 10; i++) c.fillRect(3.1 + i * 1.27, h - 0.55, 0.85, 0.55);
    c.fillStyle = '#4b3d78'; c.beginPath(); c.arc(4.3, 2.3, 0.9, 0, 7); c.fill();
    c.fillStyle = '#d6a23c'; c.beginPath(); c.arc(13.1, 5.3, 0.25, 0, 7); c.arc(14.5, 5.3, 0.25, 0, 7); c.fill();
    c.fillStyle = '#ddd'; c.font = `0.9px ${FONT}`; c.fillText('K', 9.3, 5.4);
  }, 0, modY, T));
  g.add(board(15.4, 17.1, 2.3, 0xbfc3c7, (c, w, h) => {
    c.fillStyle = '#cdd1d4'; c.fillRect(0, 0, w, h); c.fillStyle = '#4c5156'; c.textAlign = 'center';
    c.font = `bold 1.9px ${FONT}`; c.fillText('ESPRESSIF', w / 2, 2.5);
    c.font = `bold 1.35px ${FONT}`; c.fillText('ESP32-WROOM-32', w / 2, 4.6);
    c.font = `0.75px ${FONT}`; c.textAlign = 'left';
    ['R-CRM-es5-ESP-WROOM-32', 'CMIIT ID: 2016DP2463', 'IC: 21098-ESPWROOM32', 'FCC ID: 2AC7Z-ESPWROOM32'].forEach((t, i) => c.fillText(t, 1.1, 9 + i * 1.6));
    c.beginPath(); c.arc(1.6, h - 1.5, 0.5, 0, 7); c.fill();
  }, 0, 3.85, T + 0.8, { metalness: 0.85, roughness: 0.32 }));
  // 下半部元件（位置量自照片）
  const Z = T;
  const qfn = board(3.6, 3.6, 0.85, 0x1a1a1a, (c, w, h) => { c.fillStyle = '#1d1d1d'; c.fillRect(0, 0, w, h); c.fillStyle = '#8a8a8a'; c.font = `0.55px ${FONT}`; c.textAlign = 'center'; c.fillText('SiL', w / 2, 1.3); c.fillText('2104', w / 2, 2.0); c.fillText('F02ZC', w / 2, 2.7); }, -6.9, -9.7, Z, { roughness: 0.4 });
  g.add(qfn);
  const parts = new THREE.Group(); parts.position.z = Z; g.add(parts);
  [-1.8, -0.7, 0.4].forEach(x => parts.add(smdR(x, -9.1, Math.PI / 2)));
  parts.add(sot(3.5, -9.3, Math.PI / 2, [-0.95, 0, 0.95], [-0.95, 0, 0.95], 'CH', 2.9, 1.6));
  [[6.6, -10], [7.7, -10], [6.6, -11.9], [7.7, -11.9]].forEach(([x, y]) => parts.add(smdC(x, y, Math.PI / 2)));
  parts.add(sot(7.9, -15.7, 0, [-0.95, 0, 0.95], [-0.95, 0.95], '4A2D'));
  [[-7.7, -14.8], [-7.7, -15.9], [-7.7, -17.0], [-5.6, -14.2]].forEach(([x, y]) => parts.add(smdR(x, y, 0)));
  parts.add(box(1.5, 2.7, 1.0, mat(0x1d1d1d, { roughness: 0.4 }), 5.1, -13.3, 0));      // SOD-123 二極體
  [[12.4, -13.9], [12.4, -16.2]].forEach(([x, y], i) => {
    parts.add(box(1.6, 0.8, 0.5, mat(0xf2f2ea, { roughness: 0.3 }), x, y, 0));
    parts.add(box(0.7, 0.6, 0.12, mat(i ? 0xff3030 : 0x48ff60, { emissive: i ? 0xff2020 : 0x30ff50, emissiveIntensity: i ? 0.9 : 0.15 }), x, y, 0.5));
  });
  // Micro USB 母座
  const usb = new THREE.Group(); usb.position.set(0, -16.4, Z); parts.add(usb);
  usb.add(box(7.6, 5.4, 2.6, metal(0xc8ccd0, 0.22), 0, 0, 0));
  usb.add(box(6.6, 0.4, 1.7, mat(0x111111), 0, -2.55, 0.45));
  usb.add(box(4.6, 2.2, 0.35, mat(0x111111), 0, -1.4, 1.1));
  [-1, 1].forEach(s => usb.add(box(1.4, 1.8, 0.3, metal(0xc8ccd0, 0.25), s * 4.4, 1.2, 0)));
  // 側按 RST 鍵
  const sw = new THREE.Group(); sw.position.set(-11.6, -16, Z); parts.add(sw);
  sw.add(box(3.3, 4.6, 1.8, metal(0xd5d8dc, 0.3), 0, 0, 0));
  sw.add(box(1.4, 1.6, 1.2, mat(0x222222), -2.3, 0, 0.3));
  // 腳位名稱貼片（勾選「主板腳位名稱」才顯示）
  const lab = new THREE.Mesh(new THREE.PlaneGeometry(W + 12, L), new THREE.MeshBasicMaterial({ transparent: true, depthWrite: false, map: canvasTex(W + 12, L, (c, w, h) => {
    c.font = `bold 1.05px ${FONT}`; c.textBaseline = 'middle';
    holes.forEach(([x, y, , col, r]) => {
      const n = MINI_PINS[col][r - 1], X = x + w / 2, Yc = h / 2 - y, left = col[0] === 'L';
      const tx = { LO: X - 1.2, LI: X + 1.15, RI: X - 1.15, RO: X + 1.2 }[col];
      c.textAlign = (col === 'LO' || col === 'RI') ? 'right' : 'left';
      const tw = c.measureText(n).width;
      const bx = c.textAlign === 'right' ? tx - tw - 0.2 : tx - 0.2;
      const used = ['GND', 'VCC', '3V3', 'IO18', 'IO19', 'IO23', 'IO5', 'TDI', 'TCK', 'TMS', 'TDO'].includes(n);
      c.fillStyle = used ? 'rgba(255,214,10,.95)' : 'rgba(15,25,40,.82)'; c.fillRect(bx, Yc - 0.65, tw + 0.4, 1.3);
      c.fillStyle = used ? '#1a1a1a' : '#e8eef5'; c.fillText(n, tx, Yc + 0.05);
    });
  }, 30) }));
  lab.position.z = T + 3.4; lab.visible = false; lab.renderOrder = 5; lab.userData.noPick = true; pinOverlays.push(lab); g.add(lab);
  g.userData.dims = { W, L }; g.userData.pins = [];
  return g;
}
// --- NODEMCU-32S（購物車；尺寸取交接檔約 28 × 51 mm，排針列距假設 25.4 mm，待實測）
function makeNodeMCU() {
  const g = new THREE.Group(), W = 28, L = 51.5, T = 1.6;
  g.add(board(W, L, T, 0x16191d, (c, w, h) => {
    c.fillStyle = '#1b1e22'; c.fillRect(0, 0, w, h);
    for (let i = 0; i < 19; i++) { const y = 2.95 + i * 2.54; [1.3, w - 1.3].forEach(x => { c.fillStyle = '#d9b45a'; c.beginPath(); c.arc(x, y, 0.9, 0, 7); c.fill(); c.fillStyle = '#222'; c.beginPath(); c.arc(x, y, 0.45, 0, 7); c.fill(); }); }
    c.fillStyle = '#eee'; c.font = `bold 1.7px ${FONT}`; c.textAlign = 'center';
    c.fillText('NodeMCU-32S', w / 2, h - 15); c.font = `1.1px ${FONT}`; c.fillText('EN          BOOT', w / 2, h - 2.6);
  }));
  g.add(box(18, 25.5, 0.8, mat(0x161616), 0, L / 2 - 12.75, T));
  g.add(board(16.6, 17.8, 2.3, 0xbfc3c7, (c, w, h) => {
    c.fillStyle = '#c9cdd1'; c.fillRect(0, 0, w, h); c.fillStyle = '#5d6166'; c.textAlign = 'center';
    c.font = `bold 2.1px ${FONT}`; c.fillText('ESPRESSIF', w / 2, 3.2); c.font = `bold 1.4px ${FONT}`; c.fillText('ESP32-WROOM-32E', w / 2, 5.4);
  }, 0, L / 2 - 6.8 - 8.9, T + 0.8, { metalness: 0.85, roughness: 0.32 }));
  g.add(box(7.6, 5.6, 2.6, metal(0xc8ccd0, 0.25), 0, -L / 2 + 2.6, T));
  g.add(box(5, 5, 0.9, mat(0x1a1a1a), 0, -L / 2 + 11, T));
  g.add(box(6.5, 3.6, 1.6, mat(0x1a1a1a), -6, -L / 2 + 8, T));
  [-7.5, 7.5].forEach(x => g.add(box(4, 3, 1.5, mat(0xe9e9e9), x, -L / 2 + 3.5, T)));
  const pins = [];
  const hdrMat = mat(0x111111, { roughness: 0.7 });
  [-12.7, 12.7].forEach(x => {
    const hdr = box(2.5, 19 * 2.54, 2.5, hdrMat, x, 0, -2.5); g.add(hdr); pins.push(hdr);
    for (let i = 0; i < 19; i++) g.add(box(0.64, 0.64, 6, metal(0xd8b25a, 0.3), x, (i - 9) * 2.54, -8.5));
  });
  g.userData.dims = { W, L }; g.userData.pins = pins;
  return g;
}
const esp32Slot = new THREE.Group();
const espIt = add('esp32', esp32Slot, V(0, 0, BOARD_Z), { ex: V(0, 0, 82), step: 2, keys: [[2, SIDE], [7, V()]], entry: V(0, 0, 32) });
const clashMat = new THREE.MeshBasicMaterial({ color: 0xff2a2a, transparent: true, opacity: 0.82 });
function clashBoxes() {
  const g = new THREE.Group();
  [-1, 1].forEach(sx => [-1, 1].forEach(sy => { g.add(box(3.1, 4.6, 3.0, clashMat, sx * 12.7, sy * 17.5, -2.75)); }));
  return g;
}
let boardKind = 'mini';
function setBoard(kind) {
  boardKind = kind;
  esp32Slot.clear(); pinOverlays.length = 0;
  const b = kind === 'mini' ? makeMini32() : makeNodeMCU();
  b.traverse(o => { o.userData.partId = 'esp32'; if (o.isMesh) { o.castShadow = !o.userData.noPick; o.receiveShadow = true; } });
  esp32Slot.add(b); ghostOn = null;
  if (kind !== 'mini') { const c = clashBoxes(); c.traverse(o => o.userData.partId = 'esp32'); esp32Slot.add(c); }
  pinOverlays.forEach(o => o.visible = ui('pinNames').checked);
  document.getElementById('sizeWarn').hidden = kind === 'mini';
  highlight(selected);
}

// ===== 3. 墊片 =====
IMU_HOLES.forEach(([x, y], i) => add('washer', stlMesh('washer', mat(0xf3f1ea, { roughness: 0.72 })), V(x, y, 3), { ex: V(0, 0, 20 + i * 2), step: 3, entry: V(0, 0, 22) }));

// ===== 4. IMU（GY-91）+ M3 螺絲 =====
// 官方組裝照片：印字面（背面）朝上、晶片朝下。正面元件照 docs/img/gy-91.jpg 擺放。
const IMU_W = 14.3, IMU_L = 20.6, IMU_T = 1.0;
const imuCx = IMU_HOLES[0][0] + IMU_W / 2 - 2.35, imuCy = (IMU_HOLES[0][1] + IMU_HOLES[1][1]) / 2;
const IMU_Z = 5;
const imuPin = i => [IMU_W / 2 - 1.4, (3.5 - i) * 2.54];      // 板子局部座標，VIN 在 +y
function makeIMU() {
  const g = new THREE.Group(), W = IMU_W, L = IMU_L;
  const holes = IMU_HOLES.map(([hx, hy]) => [hx - imuCx, hy - imuCy, 1.55]);
  for (let i = 0; i < 8; i++) { const [x, y] = imuPin(i); holes.push([x, y, 0.5]); }
  const cx = x => x + W / 2, cy = y => L / 2 - y;
  const rings = c => {
    c.fillStyle = '#e0bd5f';
    holes.forEach(([x, y, r]) => { c.beginPath(); c.arc(cx(x), cy(y), r > 1 ? 2.35 : 0.95, 0, 7); c.fill(); });
  };
  const top = (c, w, h) => {      // 背面（朝上）：腳位名稱
    c.fillStyle = '#5b1f80'; c.fillRect(0, 0, w, h);
    c.strokeStyle = '#a8326f'; c.lineWidth = 0.2;
    for (let i = 0; i < 6; i++) { c.beginPath(); c.moveTo(cx(imuPin(i)[0]) - 1, cy(imuPin(i)[1])); c.lineTo(cx(1), cy(imuPin(i)[1]) + 0.6 * (i - 2.5)); c.lineTo(cx(-2), cy(0) + i); c.stroke(); }
    rings(c);
    c.fillStyle = '#fff'; c.font = `bold 0.95px ${FONT}`; c.textAlign = 'right';
    IMU_PINS.forEach((n, i) => { const [x, y] = imuPin(i); c.fillText(n === 'SDO/SAO' ? 'SDO/SAO' : n, cx(x) - 1.25, cy(y) + 0.35); });
    c.save(); c.translate(cx(-4.6), cy(0)); c.rotate(-Math.PI / 2); c.font = `bold 1.4px ${FONT}`; c.textAlign = 'center'; c.fillText('GY-91', 0, 0); c.restore();
  };
  const bottom = (c, w, h) => {   // 正面（朝下）
    c.fillStyle = '#5b1f80'; c.fillRect(0, 0, w, h);
    c.strokeStyle = '#c0367a'; c.lineWidth = 0.15;
    for (let i = 0; i < 8; i++) { c.beginPath(); c.moveTo(cx(imuPin(i)[0]), cy(imuPin(i)[1])); c.lineTo(cx(2), cy(imuPin(i)[1] * 0.7)); c.lineTo(cx(-1), cy(0)); c.stroke(); }
    rings(c);
  };
  g.add(pcb({ W, L, T: IMU_T, outline: roundOutline(W, L, 1.2), holes, color: 0x4a1766, top, bottom, px: 34 }));
  // 正面元件：照片座標 (u 由排針那側算起, v 由 VIN 那端算起) → 局部 x = W/2 - u, y = L/2 - v；元件朝 -z
  const P = new THREE.Group(); P.rotation.x = Math.PI; g.add(P);   // 翻面：局部 (x, y) → (x, -y)，z 朝下
  const at = (u, v) => [W / 2 - u, -(L / 2 - v)];
  const put = (o, u, v) => { const [x, y] = at(u, v); o.position.x = x; o.position.y = y; P.add(o); return o; };
  put(sot(0, 0, 0.35, [-0.95, 0.95], [-0.95, 0, 0.95], 'LDO'), 7.6, 2.4);
  const tan = new THREE.Group(); tan.add(board(3.2, 1.7, 1.4, 0xe39b1b, (c, w, h) => { c.fillStyle = '#e8a320'; c.fillRect(0, 0, w, h); c.fillStyle = '#5a3a08'; c.font = `bold 0.5px ${FONT}`; c.fillText('106A', 0.5, 0.75); c.fillText('C1P0', 0.5, 1.35); c.fillRect(0, 0, 0.45, h); }, 0, 0, 0, { roughness: 0.45 }));
  [-1, 1].forEach(s => tan.add(box(0.5, 1.2, 0.5, metal(0xd9dcdf, 0.3), s * 1.7, 0, 0))); tan.rotation.z = 0.35; put(tan, 6.4, 4.9);
  put(smdC(0, 0, Math.PI / 2 + 0.35), 4.4, 3.5); put(smdC(0, 0, 0.35), 11.6, 7.0); put(smdC(0, 0, 0.35), 12.0, 11.8, 2.0, 1.25);
  const bmp = new THREE.Group(); bmp.add(box(2.5, 2.0, 0.95, metal(0xc9cbcf, 0.3), 0, 0, 0)); bmp.add(box(0.4, 0.4, 0.05, mat(0x222222), 0.7, 0.4, 0.95)); bmp.rotation.z = 0.35; put(bmp, 9.2, 6.7);
  const mpu = board(3, 3, 0.9, 0x141414, (c, w, h) => { c.fillStyle = '#161616'; c.fillRect(0, 0, w, h); c.fillStyle = '#777'; c.font = `0.42px ${FONT}`; c.fillText('MPU-9250', 0.3, 1.2); c.beginPath(); c.arc(0.4, 0.4, 0.15, 0, 7); c.fill(); }, 0, 0, 0, { roughness: 0.35 });
  const mg = new THREE.Group(); mg.add(mpu); mg.rotation.z = 0.35; put(mg, 9.4, 10.4);
  put(sot(0, 0, 0.35, [-0.95, 0.95], [0], ''), 5.9, 9.5);
  [[6.3, 7.3, 0.35], [3.7, 8.6, Math.PI / 2 + 0.35], [4.6, 11.9, Math.PI / 2 + 0.35], [7.6, 12.5, 0.35], [6.4, 14.4, 0.35]].forEach(([u, v, r]) => put(smdR(0, 0, r), u, v));
  const led = new THREE.Group(); led.add(box(1.6, 0.8, 0.5, mat(0xf2f2ea, { roughness: 0.3 }))); led.add(box(0.6, 0.5, 0.1, mat(0x30ff50, { emissive: 0x30ff50, emissiveIntensity: 0.3 }), 0, 0, 0.5)); led.rotation.z = 0.35; put(led, 7.0, 15.9);
  [[6.9, 17.2], [7.3, 18.5], [7.7, 19.7]].forEach(([u, v]) => put(smdR(0, 0, 0.35), u, v));
  [[9.4, 14.2], [10.4, 14.9]].forEach(([u, v]) => put(smdC(0, 0, 0.35), u, v));
  return g;
}
const imu = makeIMU();
add('imu', imu, V(imuCx, imuCy, IMU_Z), { ex: V(0, 0, 36), step: 4, entry: V(0, 0, 30) });
function m3Screw() {
  const g = new THREE.Group(), blk = mat(0x1d1f22, { metalness: 0.6, roughness: 0.35 });
  g.add(cyl(2.75, 3, blk, 0, 0, 0, 32));
  g.add(cyl(1.3, 1.6, mat(0x050505), 0, 0, 1.45, 6));
  g.add(cyl(1.5, 5 + IMU_T, blk, 0, 0, -5 - IMU_T, 20));
  for (let i = 0; i < 9; i++) { const t = new THREE.Mesh(new THREE.TorusGeometry(1.45, 0.12, 6, 20), blk); t.position.z = -4.6 - IMU_T + i * 0.5; g.add(t); }
  return g;
}
IMU_HOLES.forEach(([x, y]) => add('m3', m3Screw(), V(x, y, IMU_Z + IMU_T), { ex: V(0, 0, 54), step: 4, entry: V(0, 0, 40) }));

// 機身座標（前左上）→ 3D 場景座標。機身 STL 的機頭在 +Y、左方在 -X：
// Gazebo 模型（機頭 +X）裡的電池槽與支架都比 STL 轉了 90°；官方 GY-91 座標圖是 VIN 端朝前、安裝孔朝左。
MOTORS.forEach(m => { m.mx = -m.sy; m.my = m.sx; });

// ===== 5. 馬達（8520：鋼殼、白色尾蓋、銅軸承）=====
function makeMotor(cw) {
  const g = new THREE.Group();
  const prof = [[0, -9], [4.1, -9], [4.3, -8.8], [4.3, -6.5], [4.25, -6.5], [4.25, 9.9], [4.05, 10.2], [3.3, 10.25], [3.3, 10.6], [1.3, 10.6], [1.3, 11.4], [0, 11.4]];
  const lathe = (pts, m) => { const lg = new THREE.LatheGeometry(pts.map(([r, z]) => new THREE.Vector2(r, z)), 48); lg.rotateX(Math.PI / 2); return new THREE.Mesh(lg, m); };
  g.add(lathe(prof.slice(5, 12).concat([[0, 9.9]]).map(p => p), metal(0xd2d5d9, 0.2)));
  g.add(cyl(4.25, 16.4, metal(0xd2d5d9, 0.24), 0, 0, -6.5, 48));
  g.add(lathe([[0, -9], [4.1, -9], [4.32, -8.75], [4.32, -6.4], [0, -6.4]], mat(0xf3f3f0, { roughness: 0.55 })));
  g.add(cyl(1.25, 0.8, metal(0xc7924a, 0.35), 0, 0, 10.6, 24));
  g.add(cyl(0.5, 5.6, metal(0xe7e9ec, 0.18), 0, 0, 10.2, 16));
  [0, Math.PI].forEach(a => g.add(box(0.5, 1.2, 0.3, mat(0x2a2a2a), 1.6 * Math.cos(a), 1.6 * Math.sin(a), -9.3)));
  return g;
}
const motorObjs = {};
MOTORS.forEach(m => {
  const o = makeMotor(m.cw); motorObjs[m.k] = o;
  add('motors', o, V(m.mx * ARM, m.my * ARM, 1), { ex: V(0, 0, 48), step: 5, entry: V(0, 0, 38) });
});

// ===== 6. MOSFET（TO-252）、10 kΩ 電阻 =====
const diag = m => V(m.mx, m.my, 0).normalize();
const sideOf = m => V(-m.my, m.mx, 0).normalize();
const atArm = (m, r, s, z) => diag(m).multiplyScalar(r).add(sideOf(m).multiplyScalar(s)).setZ(z);
const MOS_R = 33, MOS_Z = 3;
const LEAD_R = MOS_R - 5.6, LEAD_S = 2.28;   // 兩隻腳的焊點（G 在 +side，S 在 -side）
function makeMosfet() {
  const g = new THREE.Group();   // 局部 +y＝背面金屬片（D）朝外，-y＝腳朝內；局部 -x＝G、+x＝S
  g.add(box(6.6, 6.1, 0.5, metal(0xc9ccd0, 0.3), 0, 0.2, 0));               // 底部金屬焊盤（D）
  g.add(board(6.6, 6.1, 2.3, 0x1a1a1a, (c, w, h) => {
    c.fillStyle = '#1c1c1c'; c.fillRect(0, 0, w, h); c.fillStyle = '#bdbdbd'; c.textAlign = 'center';
    c.font = `bold 1.05px ${FONT}`; c.fillText('UMW', w / 2, 2.4); c.fillText('100N03A', w / 2, 3.8); c.font = `0.7px ${FONT}`; c.fillText('2324', w / 2, 5.0);
  }, 0, -0.3, 0.2, { roughness: 0.45 }));
  g.add(box(5.4, 1.6, 0.5, metal(0xc9ccd0, 0.3), 0, 3.6, 0.0));             // 外露的背面金屬片（D）
  [-LEAD_S, LEAD_S].forEach(x => { g.add(box(0.8, 2.3, 0.5, metal(0xc9ccd0, 0.3), x, -4.45, 0.55)); g.add(box(0.8, 0.9, 0.5, metal(0xc9ccd0, 0.3), x, -5.6, 0.1)); });
  g.add(box(0.8, 0.8, 0.5, metal(0xc9ccd0, 0.3), 0, -3.7, 0.55));            // 中間短腳
  return g;
}
// 1/4 W 色環電阻：棕黑橙金 = 10 kΩ；兩腳彎下去接到 G、S
function makeResistor(m) {
  const g = new THREE.Group();
  const s = sideOf(m), d = diag(m), c = atArm(m, LEAD_R - 3.4, 0, MOS_Z + 2.0);
  const bodyG = new THREE.CylinderGeometry(1.1, 1.1, 6.0, 20); const body = new THREE.Mesh(bodyG, mat(0xd8c39b, { roughness: 0.55 }));
  const q = new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), s); body.quaternion.copy(q); body.position.copy(c); g.add(body);
  [[-2.0, 0x7a4a1c], [-1.0, 0x111111], [0.0, 0xff7a00], [2.0, 0xd4af37]].forEach(([o, col]) => {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(1.13, 1.13, 0.5, 20), mat(col)); b.quaternion.copy(q); b.position.copy(c).addScaledVector(s, o); g.add(b);
  });
  [1, -1].forEach(k => {
    const e = c.clone().addScaledVector(s, k * 3.0), tip = atArm(m, LEAD_R, k * LEAD_S, MOS_Z + 0.75);
    g.add(tube([e.toArray(), e.clone().addScaledVector(s, k * 1.2).toArray(), tip.clone().addScaledVector(d, -1.0).setZ(MOS_Z + 1.6).toArray(), tip.toArray()], 0.22, 0xcfd2d6));
  });
  return g;
}
const tapeMat = new THREE.MeshPhysicalMaterial({ color: 0xffffff, transmission: 0.6, transparent: true, opacity: 0.32, roughness: 0.15, depthWrite: false });
MOTORS.forEach(m => {
  const ang = Math.atan2(m.my, m.mx);
  const mo = makeMosfet(); mo.rotation.z = ang - Math.PI / 2;
  add('mosfet', mo, atArm(m, MOS_R, 0, MOS_Z), { ex: V(0, 0, 26), step: 6, entry: V(0, 0, 22) });
  add('resistor', makeResistor(m), V(), { ex: V(0, 0, 30), step: 6, entry: V(0, 0, 24) });
  const t = box(9.6, 26, 0.12, tapeMat, 0, 0, 0); t.rotation.z = ang + Math.PI / 2;
  add('tape', t, atArm(m, 36, 0, 5.75), { ex: V(0, 0, 34), step: 10, entry: V(0, 0, 26), shadow: false });
});

// ===== 接線（每條線都接到真實的孔或腳）=====
const WI = Object.fromEntries(WIRES.map(w => [w.id, w]));
const hexN = h => h === '#f2f2f2' ? 0xd2d2d2 : parseInt(h.slice(1), 16);   // 白線在白色機身上改淡灰才看得到
const espHole = (col, row) => V(MINI_COLS[col], pinY(row), BOARD_Z);
const WIRE_R = 0.36;
function wire(group, info, pts, colorHex, r = WIRE_R) {
  const t = tube(pts.map(p => p.toArray ? p.toArray() : p), r, colorHex);
  t.userData.wire = info; group.add(t); return t;
}
// 從主板下方穿過支架鏤空、穿孔、上面一點焊錫
function toHole(col, row, from) {
  const h = espHole(col, row), sx = Math.sign(h.x);
  return [...from, V(sx * 9.6, h.y, UNDER), V(h.x - sx * 0.2, h.y, BOARD_Z - 2.6), V(h.x, h.y, BOARD_Z - 0.6), V(h.x, h.y, BOARD_Z + MINI_T + 0.25)];
}
const holeSolder = (g, col, row) => { const h = espHole(col, row); g.add(solder(h.x, h.y, BOARD_Z + MINI_T + 0.05)); };
function sleeve(g, a, b, colorHex, r = 1.15) {
  const d = b.clone().sub(a), len = d.length();
  const c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 20), mat(colorHex, { roughness: 0.5 }));
  c.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize()); c.position.copy(a).add(b).multiplyScalar(0.5); g.add(c); return c;
}
// 匯流點（熱縮套管包住的焊接點）
const JR = [V(-8.6, -9.5, 3.9), V(-8.6, -14.5, 3.9)];   // 紅：兩端
const JK = [V(-12.6, -6.5, 3.9), V(-12.6, -1.5, 3.9)];  // 黑
const mid = j => j[0].clone().add(j[1]).multiplyScalar(0.5);
// 機臂上的走道：繞過 IMU（x 在 -3.6～10.7、y 在 -9～11.6）
function armToCenter(m, r0, s, z, end) {
  const pts = [atArm(m, r0, s, z), atArm(m, 18, s, z)];
  if (m.mx > 0) pts.push(V(4, m.my * 15.2, z), V(-5.5, m.my * 13.8, z));
  else pts.push(atArm(m, 13, s, z));
  pts.push(end); return pts;
}

// --- 接線①：電源
const wPow = new THREE.Group();
sleeve(wPow, JR[0], JR[1], 0xd62828); sleeve(wPow, JK[0], JK[1], 0x161616);
// 電池插頭（MX2.0 母座）掛在機身後側下方
const CONN = V(-6, -39.2, -9.2);   // 母座底面；開口朝 +y 對著電池的公頭
const conn = new THREE.Group();
conn.add(box(5.8, 4.6, 4.4, mat(0xf3f3f3, { roughness: 0.6 }), CONN.x, CONN.y, CONN.z));
conn.add(box(4.6, 0.2, 3.2, mat(0x333333), CONN.x, CONN.y + 2.35, CONN.z + 0.6));
wire(conn, WI.P1, [V(CONN.x - 1, CONN.y - 2.3, CONN.z + 2.2), V(CONN.x - 1.5, CONN.y - 6.5, CONN.z + 4), V(-7, -32, 1), V(-8, -21, 4.2), JR[1].clone().setY(JR[1].y - 0.3)], 0xd62828, 0.42);
wire(conn, WI.P2, [V(CONN.x + 1, CONN.y - 2.3, CONN.z + 2.2), V(CONN.x + 1.5, CONN.y - 6.5, CONN.z + 4), V(-9, -31, 1), V(-13, -18, 4.2), V(-14, -10, 4.0), JK[0].clone().setY(JK[0].y - 0.3)], 0x161616, 0.42);
add('connector', conn, V(), { ex: V(0, -30, -6), step: 8, entry: V(0, -16, -8) });
wire(wPow, WI.P3, toHole('RI', 8, [mid(JR).setZ(4.3), V(-5, -12.6, 6.5), V(1, -12.8, UNDER)]), 0xd62828); holeSolder(wPow, 'RI', 8);
wire(wPow, WI.P4, toHole('RI', 7, [mid(JK).setZ(4.3), V(-11.5, -9, 7), V(-5, -12, UNDER - 0.2), V(3, -12.2, UNDER)]), 0x161616); holeSolder(wPow, 'RI', 7);
const motorPlus = [];   // 匯流點 → 機臂上的熱縮接點（馬達正極在 r=21 和它接上）
MOTORS.forEach(m => {
  const joint = atArm(m, 21, -3.7, 3.75);
  wire(wPow, WI.P5, armToCenter(m, 22.5, -3.7, 3.75, JR[0]), 0xd62828);
  sleeve(wPow, atArm(m, 19.5, -3.7, 3.75), atArm(m, 23, -3.7, 3.75), 0xd62828, 0.75);
  motorPlus.push(joint);
  wire(wPow, WI.P6, armToCenter(m, LEAD_R, -LEAD_S, 3.45, JK[1]).map((p, i) => i === 0 ? atArm(m, LEAD_R, -LEAD_S, MOS_Z + 0.75) : p), 0x161616);
  wPow.add(solder(...atArm(m, LEAD_R, -LEAD_S, MOS_Z + 0.85).toArray()));
});
add('wire', wPow, V(), { ex: V(), step: 8, entry: V(0, 0, 14) });

// --- 接線②：IMU（GY-91 排針 → 主板左邊兩排）
const wImu = new THREE.Group();
WIRES.filter(w => w.g === 'imu').forEach((w, k) => {
  const [lx, ly] = imuPin(w.imu), p = V(imuCx + lx, imuCy + ly, IMU_Z + IMU_T);
  const [col, row] = w.pin, h = espHole(col, row);
  const pts = [p.clone().setZ(p.z + 0.2), p.clone().setZ(p.z + 1.6), V(p.x + 1.6, p.y, p.z + 3.4), V(p.x - 1, p.y * 0.85 + h.y * 0.15, UNDER - 0.4 + k * 0.05)];
  wire(wImu, w, toHole(col, row, pts), hexN(w.hex));
  wImu.add(solder(p.x, p.y, p.z + 0.1)); holeSolder(wImu, col, row);
  if (w.tag) [p.clone().add(V(1.2, 0, 2.2)), espHole(col, row).add(V(0, 0, -3.6))].forEach(q => {
    const s = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.62, 1.6, 12), mat(0xf5f0e0, { roughness: 0.9 })); s.position.copy(q); s.userData.tag = w.tag; wImu.add(s);
  });
});
add('wire', wImu, V(), { ex: V(), step: 9, entry: V(0, 0, 12) });

// --- 接線③：馬達（GPIO → G、馬達負極 → D、馬達正極 → 紅色接點）
const wMot = new THREE.Group();
MOTORS.forEach((m, i) => {
  const R = ARM * Math.SQRT2, w = motorWires(m), [col, row] = m.pin;
  const gate = atArm(m, LEAD_R, LEAD_S, MOS_Z + 0.75);
  const pts = [gate, atArm(m, LEAD_R - 0.5, LEAD_S + 0.5, 5.0), atArm(m, 24.5, 2.4, 7.3), atArm(m, 20.5, 1.8, 7.4), atArm(m, 15, 1.0, UNDER - 0.6)];
  wire(wMot, WI[`M${m.no}a`], toHole(col, row, pts), 0xf2c200);
  wMot.add(solder(...gate.clone().setZ(gate.z + 0.1).toArray())); holeSolder(wMot, col, row);
  // 馬達兩條線從馬達底部經管壁開槽拉出
  const exit = s => [atArm(m, R - 1.0, s * 0.6, -8.3), atArm(m, R - 4.3, s * 0.6, -7.2), atArm(m, R - 4.6, s * 0.7, 1.5), atArm(m, R - 6.5, s * 2.4, 3.7)];
  wire(wMot, WI[`M${m.no}b`], [...exit(1), atArm(m, 42, 3.4, 3.7), atArm(m, 38.5, 1.8, 4.2), atArm(m, MOS_R + 3.5, 0, MOS_Z + 0.65)], hexN(w.negHex), 0.3);
  wMot.add(solder(...atArm(m, MOS_R + 3.5, 0, MOS_Z + 0.75).toArray()));
  wire(wMot, { ...WI.P5, from: `${m.name}馬達正極（${w.pos}線）`, to: '紅色匯流點（接點套熱縮套管）' }, [...exit(-1), atArm(m, 40, -3.9, 3.7), atArm(m, 30, -4.0, 3.7), atArm(m, 22.5, -3.7, 3.75)], hexN(w.posHex), 0.3);
});
add('wire', wMot, V(), { ex: V(), step: 10, entry: V(0, 0, 12) });

// ===== 7. M1.4 螺絲（由下往上）=====
function m14Screw() {
  const g = new THREE.Group(), s = metal(0x9da3aa, 0.3);
  g.add(cyl(1.25, 0.9, s, 0, 0, -0.9, 24)); g.add(box(0.3, 2.2, 0.35, mat(0x222), 0, 0, -1.0));
  g.add(cyl(0.7, 5, s, 0, 0, 0, 12)); return g;
}
POSTS.forEach(([x, y]) => add('m14', m14Screw(), V(x, y, 0), { ex: V(0, 0, -34), step: 7, entry: V(0, 0, -26) }));

// ===== 8. 電池（952540）+ MX2.0 公頭 =====
function makeBattery() {
  const g = new THREE.Group(), W = 25, L = 40, T = 9.5;
  const wrap = canvasTex(W, L, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, w, 0); gr.addColorStop(0, '#d7dbe0'); gr.addColorStop(0.5, '#eef0f2'); gr.addColorStop(1, '#c9ced4');
    c.fillStyle = gr; c.fillRect(0, 0, w, h);
    c.fillStyle = '#1f4f8a'; c.fillRect(0, h * 0.28, w, h * 0.44);
    c.fillStyle = '#fff'; c.textAlign = 'center';
    c.save(); c.translate(w / 2, h / 2); c.rotate(-Math.PI / 2);
    c.font = `bold 3px ${FONT}`; c.fillText('3.7V 1000mAh', 0, -1.4); c.font = `2.1px ${FONT}`; c.fillText('952540  25C  Li-Po', 0, 2.4); c.restore();
  });
  const side = mat(0xd0d4d9, { roughness: 0.35, metalness: 0.3, side: THREE.DoubleSide });
  const top = new THREE.MeshStandardMaterial({ map: wrap, roughness: 0.35, side: THREE.DoubleSide });
  const body = new THREE.Mesh(new THREE.BoxGeometry(W, L, T), [side, side, side, side, top, top]);
  body.position.z = T / 2; g.add(body);
  g.add(box(W - 2, 3.2, 1.2, mat(0xd8dcdf, { roughness: 0.35, metalness: 0.3 }), 0, -L / 2 - 1.5, T / 2 - 0.6)); // 封口
  g.add(box(16, 2.6, 2.2, mat(0x2b7a3a), 0, -L / 2 - 1.4, T / 2 - 1.7));                                     // 保護板
  g.add(tube([[-1.5, -L / 2 - 2.6, 4.2], [-4, -L / 2 - 7, 3.6], [-7, -L / 2 - 11.6, 3.0]], 0.5, 0xd62828));
  g.add(tube([[1.5, -L / 2 - 2.6, 4.2], [-2, -L / 2 - 7, 3.6], [-5, -L / 2 - 11.6, 3.0]], 0.5, 0x161616));
  g.add(box(4.8, 5, 3.4, mat(0xf3f3f3, { roughness: 0.6 }), -6, -L / 2 - 14.3, 1.3));  // MX2.0 公頭（插進母座）
  return g;
}
// 電池放在機身下方的槽裡；公頭對準母座 CONN
add('battery', makeBattery(), V(0, 0, -10), { ex: V(0, -70, -10), step: 11, entry: V(0, -70, 0) });

// ===== 9. 轉向箭頭 =====
const arrows = new THREE.Group(); scene.add(arrows);
MOTORS.forEach(m => {
  const col = m.cw ? 0xff8a00 : 0x1f7ae0, M = mat(col, { emissive: col, emissiveIntensity: 0.25 });
  const g = new THREE.Group(), R = 15, a0 = 0.5, a1 = 2 * Math.PI - 0.5;
  const arc = new THREE.Mesh(new THREE.TorusGeometry(R, 0.7, 8, 64, a1 - a0), M); arc.rotation.z = a0; g.add(arc);
  const tipA = m.cw ? a0 : a1, cone = new THREE.Mesh(new THREE.ConeGeometry(2.0, 5, 16), M);
  cone.position.set(R * Math.cos(tipA), R * Math.sin(tipA), 0);
  cone.rotation.z = tipA + (m.cw ? Math.PI : 0); g.add(cone);
  g.position.set(m.mx * ARM, m.my * ARM, 22); g.userData.m = m; arrows.add(g);
});
arrows.visible = false;

// ===== 10. 螺旋槳 =====
function bladeGeometry(ccw) {
  const NR = 34, NC = 12, r0 = 2.2, r1 = 27.5, pitch = 22;
  const pos = [], idx = [];
  for (let i = 0; i <= NR; i++) {
    const t = i / NR, r = r0 + (r1 - r0) * t;
    let c = 2.6 + 3.6 * Math.sin(Math.PI * Math.min(1, Math.pow(t, 0.75) * 1.02));
    if (t > 0.86) c *= Math.sqrt(Math.max(0.02, 1 - Math.pow((t - 0.86) / 0.14, 2)));
    c = Math.max(c, 0.35);
    const th = Math.min(0.42, Math.atan(pitch / (2 * Math.PI * r)));
    const tk = 0.75 - 0.4 * t;
    for (const surf of [1, -1]) for (let j = 0; j <= NC; j++) {
      const s = j / NC - 0.5;                              // 前緣 s=-0.5
      const thick = surf * tk * Math.sqrt(Math.max(0, 1 - 4 * s * s)) * 0.5 + 0.18 * (1 - 4 * s * s);
      const yy = s * c, zz = thick;
      let y = yy * Math.cos(th) - zz * Math.sin(th), z = -yy * Math.sin(th) + zz * Math.cos(th);
      if (ccw) y = -y;
      pos.push(r, y, z);
    }
  }
  const row = 2 * (NC + 1);
  for (let i = 0; i < NR; i++) for (const off of [0, NC + 1]) for (let j = 0; j < NC; j++) {
    const a = i * row + off + j, b = a + 1, c2 = a + row, d = c2 + 1; idx.push(a, c2, b, b, c2, d);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return g;
}
const propSpin = [];
function makeProp(type, ccw) {
  const g = new THREE.Group(), dark = type === 'A';
  const M = mat(dark ? 0x26282b : 0xf4f4f2, { roughness: 0.45, side: THREE.DoubleSide });
  const bg = bladeGeometry(ccw);
  [0, Math.PI].forEach(a => { const b = new THREE.Mesh(bg, M); b.rotation.z = a; g.add(b); });
  g.add(cyl(2.3, 4.6, M, 0, 0, -1.9, 24));
  const lab = new THREE.Mesh(new THREE.CircleGeometry(2.25, 32), new THREE.MeshBasicMaterial({
    map: canvasTex(4.5, 4.5, (c, w) => { c.fillStyle = dark ? '#26282b' : '#f4f4f2'; c.fillRect(0, 0, w, w); c.fillStyle = dark ? '#ffb347' : '#1f7ae0'; c.font = `bold 3.4px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(type, w / 2, w / 2 + 0.2); }, 30) }));
  lab.position.z = 2.72; g.add(lab);
  return g;
}
MOTORS.forEach(m => {
  const p = makeProp(m.cw ? 'A' : 'B', !m.cw);
  const it = add('props', p, V(m.mx * ARM, m.my * ARM, 14.2), { ex: V(0, 0, 105), step: 13, entry: V(0, 0, 30) });
  propSpin.push({ obj: p, dir: m.cw ? -1 : 1 });
});

// ---------- 尺寸標註 ----------
const dimGroup = new THREE.Group(); scene.add(dimGroup); dimGroup.visible = false;
const dimLabels = [];
function dimLine(a, b, text) {
  const g = new THREE.BufferGeometry().setFromPoints([V(...a), V(...b)]);
  dimGroup.add(new THREE.Line(g, new THREE.LineBasicMaterial({ color: 0x2c5fb3 })));
  [a, b].forEach(p => { const s = new THREE.Mesh(new THREE.SphereGeometry(0.9, 10, 8), new THREE.MeshBasicMaterial({ color: 0x2c5fb3 })); s.position.set(...p); dimGroup.add(s); });
  const el = document.createElement('div'); el.className = 'dim'; el.textContent = text; view.appendChild(el);
  dimLabels.push({ el, p: V(...a).add(V(...b)).multiplyScalar(0.5) });
}
dimLine([ARM, ARM, 26], [ARM, -ARM, 26], '相鄰軸距 84.9 mm');
dimLine([-ARM, -ARM, 40], [ARM, ARM, 40], '對角軸距 120 mm');
dimLine([ARM, -ARM - 27.5, 15], [ARM, -ARM + 27.5, 15], '槳徑 55 mm');
dimLine([-ARM, ARM - 27.5, 15], [-ARM, -ARM + 27.5, 15], '槳尖間距 ≈ 29.9 mm');
dimLine([-62, -62, FLOOR], [-62, -62, 17.4], '高約 32 mm（不含軸）');

// ---------- labels ----------
const labelIds = ['frame', 'holder', 'esp32', 'imu', 'washer', 'm3', 'motors', 'mosfet', 'resistor', 'm14', 'battery', 'connector', 'props'];
const labels = {};
const LOFF = { motors: V(0, 0, -4), battery: V(0, -8, 6), holder: V(0, -19, -6), esp32: V(0, 10, 8), m3: V(0, 0, 4), imu: V(-7, -12, 1), washer: V(0, 0, 3), connector: V(-6, -41, -4), mosfet: V(0, 0, 3), resistor: V(-17, 17, 6.5), m14: V(0, 0, -2) };
labelIds.forEach(id => {
  const el = document.createElement('div'); el.className = 'lbl'; el.textContent = P[id].name.replace(/（.*?）/g, '');
  el.onclick = () => select(id); view.appendChild(el); labels[id] = el;
});
const motorTags = MOTORS.map(m => {
  const el = document.createElement('div'); el.className = 'mtag ' + (m.cw ? 'cw' : 'ccw');
  el.innerHTML = `${m.name}<br><b>${m.cw ? '順時針 CW' : '逆時針 CCW'}</b><br>${m.cw ? 'A 槳・藍紅線' : 'B 槳・黑白線'}<br>GPIO${m.gpio}`;
  view.appendChild(el); return { el, m };
});
const frontTag = document.createElement('div'); frontTag.className = 'front'; frontTag.textContent = '▲ 機頭'; view.appendChild(frontTag);
const frontArrow = new THREE.Mesh(new THREE.ConeGeometry(4, 9, 3), new THREE.MeshBasicMaterial({ color: 0x2c5fb3 }));
frontArrow.position.set(0, 78, FLOOR + 0.3); scene.add(frontArrow);

// ---------- 腳位小標籤（接線步驟顯示）----------
const pinTags = [];
function pinTag(text, pos, steps, cls = '') {
  if (cls.includes('r')) pos = pos.clone().add(V(1.6, 0, 0));
  const el = document.createElement('div'); el.className = 'ptag ' + cls; el.textContent = text; view.appendChild(el);
  pinTags.push({ el, pos, steps });
}
const holeTop = (c, r) => V(MINI_COLS[c], pinY(r), BOARD_Z + MINI_T + 0.6);
pinTag('VCC', holeTop('RI', 8), [8], 'pw'); pinTag('GND', holeTop('RI', 7), [8], 'gnd');
WIRES.filter(w => w.g === 'imu').forEach(w => {
  const [lx, ly] = imuPin(w.imu), short = IMU_PINS[w.imu];
  pinTag(`${w.tag || ''}${short}`, V(imuCx + lx, imuCy + ly, IMU_Z + IMU_T + 0.4), [4, 9], (w.tag ? 'sig' : (w.id === 'I1' ? 'pw' : 'gnd')) + ' r');
  pinTag(`${w.tag || ''}${pinName(...w.pin).replace(/（.*）/, '')}`, holeTop(...w.pin), [9], w.tag ? 'sig' : (w.id === 'I1' ? 'pw' : 'gnd'));
});
MOTORS.forEach(m => pinTag(`GPIO${m.gpio}→${m.name}`, holeTop(...m.pin), [10], 'sig'));
MOTORS.filter(m => m.k === 'FR').forEach(m => {
  pinTag('G', atArm(m, LEAD_R, LEAD_S, MOS_Z + 1), [6, 10], 'sig');
  pinTag('S', atArm(m, LEAD_R, -LEAD_S, MOS_Z + 1), [6, 10], 'gnd');
  pinTag('D（背面金屬片）', atArm(m, MOS_R + 3.6, 0, MOS_Z + 1), [6, 10], 'd');
});
pinTag('紅色匯流點', mid(JR).setZ(5.2), [8], 'pw'); pinTag('黑色匯流點', mid(JK).setZ(5.2), [8], 'gnd');

// ---------- state & animation ----------
const ui = id => document.getElementById(id);
let mode = 'step';           // 'step' | 'free'
let step = STEPS.length;     // 目前步驟（1-based）
let anim = null;             // {t0, dur}
let free = 0;                // 0..1 自由拆解
const offAt = (it, s) => { let o = null; for (const [k, v] of it.keys) if (k <= s) o = v; return o; };
const ease = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
// 接線步驟：主板、支架、雙面膠畫成半透明，才看得到下面的線
let ghostOn = null;
function setGhost(on) {
  if (ghostOn === on) return; ghostOn = on;
  [esp32Slot, holder, tape2].forEach(root => root.traverse(o => {
    if (!o.isMesh || o.userData.noPick) return;
    (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => {
      if (m.userData.op0 === undefined) m.userData.op0 = { t: m.transparent, o: m.opacity, d: m.depthWrite };
      m.transparent = on || m.userData.op0.t; m.opacity = on ? 0.22 : m.userData.op0.o; m.depthWrite = on ? false : m.userData.op0.d; m.needsUpdate = true;
    });
  }));
}
function applyStep(s, u) {   // u：此步驟的動畫進度 0..1
  setGhost(!!STEPS[s - 1].wires);
  for (const it of items) {
    if (it.appear > s) { it.obj.visible = false; continue; }
    it.obj.visible = true;
    const to = offAt(it, s);
    const from = it.appear === s ? to.clone().add(it.entry) : offAt(it, s - 1);
    it.obj.position.copy(it.base).add(from.clone().lerp(to, ease(u)));
  }
  arrows.visible = s === 12;
}
function applyFree(t) {
  setGhost(false);
  const order = [...new Set(items.map(i => i.appear))].sort((a, b) => a - b);
  for (const it of items) {
    it.obj.visible = it.id !== 'wire' || t < 0.05;
    let k = t;
    if (ui('stagger').checked && order.length > 1) {
      const n = order.length, r = order.indexOf(it.appear);
      k = Math.min(1, Math.max(0, t * n - (n - 1 - r)));
    }
    it.obj.position.copy(it.base).addScaledVector(it.ex, ease(k));
  }
  arrows.visible = false;
}
let camGoal = null;
function goStep(s, animate = true) {
  mode = 'step'; step = Math.max(1, Math.min(STEPS.length, s));
  anim = animate ? { t0: performance.now(), dur: 1500 } : null;
  if (!animate) applyStep(step, 1);
  const c = STEPS[step - 1].cam, dir = V(c[3], c[4], c[5]).normalize();
  camGoal = { target: V(c[0], c[1], c[2]), pos: V(c[0], c[1], c[2]).addScaledVector(dir, c[6]) };
  renderStepPanel();
  document.querySelectorAll('.chip').forEach((b, i) => { b.classList.toggle('on', i + 1 === step); b.classList.toggle('done', i + 1 < step); });
  ui('free').value = 0; free = 0;
}
let playAll = null;
function startPlayAll() {
  stopPlayAll(); goStep(1);
  playAll = setInterval(() => { if (step >= STEPS.length) return stopPlayAll(); goStep(step + 1); }, 3600);
  ui('playAll').textContent = '■ 停止';
}
function stopPlayAll() { clearInterval(playAll); playAll = null; ui('playAll').textContent = '▶ 從頭播放'; }

// ---------- panels ----------
function renderStepPanel() {
  const st = STEPS[step - 1];
  ui('stepTitle').textContent = `步驟 ${step}／${STEPS.length}　${st.t}`;
  ui('stepHow').textContent = st.how;
  ui('stepCheck').innerHTML = st.check.map(c => `<li>${c}</li>`).join('');
  ui('stepParts').innerHTML = (st.parts.length ? '本步零件：' + st.parts.map(id => `<a href="#" data-p="${id}" title="${P[id].fn}">${P[id].name}</a>`).join('、') : '')
    + (st.wires ? `<table class="wt">${WIRES.filter(w => w.g === st.wires).map(w => `<tr data-w="${w.id}"><td><i class="sw" style="background:${w.hex}"></i>${w.color}</td><td>${w.from}<br>→ ${w.to}</td></tr>`).join('')}</table><p class="hint">點 3D 裡的電線也可以看它的用途。</p>` : '');
  ui('stepParts').querySelectorAll('tr[data-w]').forEach(r => r.onclick = () => selectWire(WIRES.find(w => w.id === r.dataset.w)));
  ui('stepParts').querySelectorAll('a').forEach(a => a.onclick = e => { e.preventDefault(); select(a.dataset.p); });
}
const money = n => 'NT$' + n.toLocaleString();
const badge = s => s === 'cart' ? '<span class="b cart">已在購物車</span>' : s === 'print' ? '<span class="b print">自行列印</span>' : '<span class="b todo">待購／待選</span>';
let selected = null;
function highlight(id) {
  scene.traverse(o => { if (o.isMesh && o.material && o.material.emissive && !o.userData.keepEmissive) {
    if (o.userData.e0 === undefined) o.userData.e0 = o.material.emissive.getHex();
    o.material.emissive.setHex(o.userData.partId === id && id ? 0x2a5fd0 : o.userData.e0);
    if (o.userData.partId === id && id) o.material.emissiveIntensity = 0.55; } });
}
function select(id) {
  wireHi.forEach(o => { o.material.emissive.setHex(0); }); wireHi = [];
  selected = id; highlight(id);
  document.querySelectorAll('tr[data-id]').forEach(r => r.classList.toggle('sel', r.dataset.id === id));
  const box = ui('info');
  if (!id) { box.innerHTML = '<p class="hint">點 3D 零件、名稱標籤或表格列，查看規格與購買連結。</p>'; return; }
  const p = P[id], tot = p.unit == null ? (p.status === 'print' ? '自備耗材' : '未定') : `${money(p.unit)} × ${p.n} = ${money(p.unit * p.n)}`;
  const st = items.find(i => i.id === id)?.appear;
  box.innerHTML = `<h3>${p.name} ${badge(p.status)}</h3><p class="en">${p.en}</p><p class="fn"><b>功能：</b>${p.fn}</p>${p.spec ? `<p>${p.spec}</p>` : ''}<p><b>組裝：</b>${p.note}</p><p><b>價格：</b>${tot}</p>`
    + (st ? `<p><a href="#" id="gostep">跳到步驟 ${st}：${STEPS[st - 1].t}</a></p>` : '')
    + (p.url ? `<p><a href="${p.url}" target="_blank" rel="noopener">開啟${p.url.includes('shopee') ? '蝦皮商品頁' : p.url.includes('github') ? ' Flix GitHub' : '商品頁'} ↗</a></p>` : '');
  const g = ui('gostep'); if (g) g.onclick = e => { e.preventDefault(); stopPlayAll(); goStep(st); };
}

// ---------- 電線資訊 ----------
const isShown = o => { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; };
let wireHi = [];
function selectWire(w, obj) {
  selected = 'wire'; highlight(null);
  wireHi.forEach(o => { o.material.emissive.setHex(0); o.material.emissiveIntensity = 1; }); wireHi = [];
  scene.traverse(o => { if (o.isMesh && o.userData.wire && o.userData.wire.id === w.id) { o.material = o.material.clone(); o.material.emissive.setHex(0x2a5fd0); o.material.emissiveIntensity = 0.7; o.userData.keepEmissive = true; wireHi.push(o); } });
  const wi = obj ? obj.userData.wire : w;
  document.querySelectorAll('tr[data-w]').forEach(r => r.classList.toggle('sel', r.dataset.w === w.id));
  ui('info').innerHTML = `<h3><i class="sw" style="background:${wi.hex}"></i>${WIRE_GROUPS[wi.g]}：${wi.color}線 <small>${wi.id}</small></h3>
    <p><b>從：</b>${wi.from}<br><b>到：</b>${wi.to}</p><p class="fn"><b>功能：</b>${wi.fn}</p>
    <p class="hint">完整清單見下方「接線圖與接線表」。</p>`;
}

// ---------- picking ----------
const ray = new THREE.Raycaster(), ptr = new THREE.Vector2(); let down = null;
renderer.domElement.addEventListener('pointerdown', e => down = [e.clientX, e.clientY]);
renderer.domElement.addEventListener('pointerup', e => {
  if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;
  const r = renderer.domElement.getBoundingClientRect();
  ptr.set((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ptr, camera);
  const hit = ray.intersectObjects(items.filter(i => i.obj.visible).map(i => i.obj), true).find(h => h.object.visible && h.object.userData.partId && !h.object.userData.noPick && isShown(h.object));
  if (hit && hit.object.userData.wire) return selectWire(hit.object.userData.wire, hit.object);
  select(hit ? hit.object.userData.partId : null);
});
controls.addEventListener('start', () => { camGoal = null; });

// ---------- toggles ----------
const clipPlane = new THREE.Plane(V(0, -1, 0), 0);
ui('section').onchange = e => { renderer.clippingPlanes = e.target.checked ? [clipPlane] : [];
  if (e.target.checked) camGoal = { target: V(0, 0, -2), pos: V(30, 125, 38) }; };
ui('xray').onchange = e => { [PLA, holderMat].forEach(m => { m.transparent = e.target.checked; m.opacity = e.target.checked ? 0.32 : 1; m.depthWrite = !e.target.checked; m.needsUpdate = true; }); };
ui('dims').onchange = e => { dimGroup.visible = e.target.checked; };
ui('pinNames').onchange = e => { pinOverlays.forEach(o => o.visible = e.target.checked); };
ui('free').oninput = e => { stopPlayAll(); mode = 'free'; free = +e.target.value / 100; anim = null; applyFree(free);
  document.querySelectorAll('.chip').forEach(b => b.classList.remove('on', 'done'));
  ui('stepTitle').textContent = free < 0.01 ? '已組裝完成' : '自由拆解模式'; ui('stepHow').textContent = '拖拉滑桿可以拆開或合起所有零件。點上方步驟按鈕回到組裝教學。'; ui('stepCheck').innerHTML = ''; ui('stepParts').innerHTML = ''; };
ui('stagger').onchange = () => mode === 'free' && applyFree(free);
ui('prev').onclick = () => { stopPlayAll(); goStep(step - 1); };
ui('next').onclick = () => { stopPlayAll(); goStep(step + 1); };
ui('playAll').onclick = () => playAll ? stopPlayAll() : startPlayAll();
ui('spin').onchange = () => mode === 'step' && applyStep(step, 1);
document.querySelectorAll('input[name=board]').forEach(r => r.onchange = e => setBoard(e.target.value));
const chips = ui('chips');
STEPS.forEach((s, i) => { const b = document.createElement('button'); b.className = 'chip'; b.innerHTML = `<i>${i + 1}</i>${s.t}`; b.onclick = () => { stopPlayAll(); goStep(i + 1); }; chips.appendChild(b); });

// ---------- table + thumbnails ----------
let thumbRT = null;
function thumb(id) {
  const objs = items.filter(i => i.id === id).map(i => i.obj).slice(0, 1);
  if (!objs.length) return '';
  const s = new THREE.Scene(); s.environment = scene.environment; s.add(new THREE.HemisphereLight(0xffffff, 0x99a, 0.9));
  const l = new THREE.DirectionalLight(0xffffff, 1.4); l.position.set(1, -1.5, 2.5); s.add(l);
  const g = new THREE.Group();
  objs.forEach(o => { const c = o.clone(true); c.position.copy(o.position); c.visible = true; c.traverse(k => k.visible = !(k.material === clashMat)); g.add(c); });
  s.add(g);
  const b = new THREE.Box3().setFromObject(g), ctr = b.getCenter(V()), size = b.getSize(V());
  const cam = new THREE.PerspectiveCamera(30, 4 / 3, 0.1, 3000); cam.up.set(0, 0, 1);
  const d = Math.max(size.x, size.y, size.z) * 2.2 + 6;
  cam.position.copy(ctr).add(V(1, -1.2, 0.95).normalize().multiplyScalar(d)); cam.lookAt(ctr);
  // 用主畫面的 renderer 畫到離屏目標再讀回像素：不另開 WebGL context（手機最多約 16 個，超過會把主畫面關掉）
  const TW = 168, TH = 126;
  thumbRT = thumbRT || new THREE.WebGLRenderTarget(TW, TH, { samples: 4 });
  thumbRT.texture.colorSpace = THREE.SRGBColorSpace;
  s.background = new THREE.Color(0xeef1f5);
  const prevClip = renderer.clippingPlanes; renderer.clippingPlanes = [];
  renderer.setRenderTarget(thumbRT); renderer.render(s, cam); renderer.setRenderTarget(null); renderer.clippingPlanes = prevClip;
  const px = new Uint8Array(TW * TH * 4); renderer.readRenderTargetPixels(thumbRT, 0, 0, TW, TH, px);
  const cv = document.createElement('canvas'); cv.width = TW; cv.height = TH;
  const ctx = cv.getContext('2d'), img = ctx.createImageData(TW, TH);
  for (let y = 0; y < TH; y++) img.data.set(px.subarray((TH - 1 - y) * TW * 4, (TH - y) * TW * 4), y * TW * 4);
  ctx.putImageData(img, 0, 0); return cv.toDataURL('image/png');
}
function renderTable() {
  let sum = 0;
  ui('rows').innerHTML = PARTS.map(p => {
    const sub = p.unit == null ? null : p.unit * p.n; if (p.status === 'cart' && sub != null) sum += sub;
    const t = thumb(p.id);
    return `<tr data-id="${p.id}"><td>${t ? `<img src="${t}" width="84" height="63" alt="">` : '<div class="noimg">—</div>'}</td>
      <td><b>${p.name}</b><br><small>${p.en}</small><small class="fn">${p.fn}</small></td><td class="n">${p.qty}</td>
      <td class="n">${p.unit == null ? '—' : money(p.unit)}</td><td class="n">${sub == null ? (p.status === 'print' ? '自印' : '未定') : money(sub)}</td>
      <td>${badge(p.status)}</td><td>${p.url ? `<a href="${p.url}" target="_blank" rel="noopener">連結 ↗</a>` : '—'}</td></tr>`;
  }).join('');
  ui('total').textContent = money(sum);
  document.querySelectorAll('tr[data-id]').forEach(r => r.onclick = e => { if (e.target.tagName !== 'A') select(r.dataset.id); });
}

// ---------- 接線圖與接線表 ----------
ui('wiringSvg').innerHTML = wiringSVG();
ui('wireRows').innerHTML = wiringTableHTML();
ui('wireRows').querySelectorAll('tr[data-w]').forEach(r => r.onclick = () => { const w = WIRES.find(x => x.id === r.dataset.w); const st = { power: 8, imu: 9, motor: 10 }[w.g]; stopPlayAll(); goStep(st); selectWire(w); ui('view').scrollIntoView({ behavior: 'smooth' }); });
ui('svgDl').href = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(wiringSVG());

// ---------- loop ----------
const tmp = V();
function place(el, p, show) {
  if (!show) { el.style.display = 'none'; return; }
  tmp.copy(p).project(camera);
  if (tmp.z > 1) { el.style.display = 'none'; return; }
  el.style.display = 'block';
  el.style.left = (tmp.x * 0.5 + 0.5) * view.clientWidth + 'px';
  el.style.top = (-tmp.y * 0.5 + 0.5) * view.clientHeight + 'px';
}
function resize() { const w = view.clientWidth, h = view.clientHeight; if (!w || !h) return; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize);
let last = performance.now();
function frameLoop(now) {
  if (!view.clientWidth) { last = now; requestAnimationFrame(frameLoop); return; }   // 切到別的頁籤時暫停
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  if (mode === 'step') {
    const u = anim ? Math.min(1, (now - anim.t0) / anim.dur) : 1;
    applyStep(step, u); if (u >= 1) anim = null;
  }
  if (camGoal) {
    const k = 1 - Math.pow(0.002, dt);
    controls.target.lerp(camGoal.target, k); camera.position.lerp(camGoal.pos, k);
    if (camera.position.distanceTo(camGoal.pos) < 0.3) camGoal = null;
  }
  const spinning = (mode === 'step' && (step === 12 || step === 13) && ui('spin').checked);
  propSpin.forEach(p => { if (spinning) p.obj.rotation.z += p.dir * dt * 7; });
  arrows.children.forEach(a => { a.rotation.z += (a.userData.m.cw ? -1 : 1) * dt * 1.4; });
  controls.update();
  grid.visible = ground.visible = frontArrow.visible = camera.position.z > FLOOR + 2;
  renderer.render(scene, camera);
  // labels
  const showL = ui('labels').checked;
  labelIds.forEach(id => {
    const it = items.find(i => i.id === id);
    const p = it.obj.getWorldPosition(V()).add(LOFF[id] || V());
    place(labels[id], p, showL && it.obj.visible && (mode === 'free' ? free > 0.12 : STEPS[step - 1].parts.includes(id)));
  });
  const showTags = (mode === 'step' && step >= 5) && ui('labels').checked;
  motorTags.forEach(({ el, m }) => place(el, V(m.mx * (ARM + 16), m.my * (ARM + 16), 30), showTags && (step === 5 || step === 12)));
  place(frontTag, V(0, 92, FLOOR), frontArrow.visible);
  pinTags.forEach(t => place(t.el, t.pos, mode === 'step' && ui('labels').checked && t.steps.includes(step) && !anim));
  dimLabels.forEach(d => place(d.el, d.p, dimGroup.visible));
  requestAnimationFrame(frameLoop);
}

// ---------- boot ----------
setBoard('mini');
resize();
applyStep(STEPS.length, 1);
renderTable();
select(null);
goStep(STEPS.length, false);
camera.position.copy(camGoal.pos); controls.target.copy(camGoal.target); camGoal = null;
requestAnimationFrame(frameLoop);
window.__fz = { goStep, setBoard, camera, controls, scene, get step() { return step; } };
