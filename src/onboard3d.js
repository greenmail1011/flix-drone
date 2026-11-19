// 一體板版的 3D 組裝動畫（頁籤 #onboard）。打開頁籤時才建立，和標準版共用官方 STL（meshes.js）。
// 座標：機身 STL 座標（mm），機頭 +Y、右 +X、上 +Z；機身頂面 z = 3。板子資料由 pcb2/export3d.py 產生。
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { MESH, QS } from './meshes.js';
import { MOTORS, motorWires } from './data.js';
import { OB } from './onboard_data.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const FONT = '"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif';
const ARM = 42.43, FRAME_TOP = 3, POST_H = 8, BOARD_Z = FRAME_TOP + POST_H, FLOOR = -15.05;
const POSTS = OB.holes;                       // 支柱位置 = 板子的 4 個孔 = 原 ESP32 支架柱腳
const T = OB.thick, TOP = BOARD_Z + T;
const SIDE = V(108, -10, 0);                    // 第 3 步：板子放在機身旁邊燒錄
const MOT = MOTORS.map(m => ({ ...m, mx: -m.sy, my: m.sx }));   // 和 app.js 相同的換算

export const OSTEPS = [
  { t: '機身與馬達', parts: ['frame', 'motors'],
    how: '3D 列印機身（flix-frame-1.1.stl）。把 4 顆 8520 馬達從上方壓進機臂末端的管子，馬達線先留在外面。',
    check: ['順時針馬達（藍紅線）裝右後 M1、左前 M3', '逆時針馬達（黑白線）裝左後 M0、右前 M2', '馬達壓到底，不會晃'],
    cam: [0, 0, 0, 0.6, -0.8, 0.75, 270] },
  { t: '鎖上支柱', parts: ['posts', 'screwB'],
    how: '列印 carrier-posts.stl（和載板版共用），放在機身中間，4 根柱子對準原本 ESP32 支架的 4 個孔，用 4 顆 M1.4×5 從機身底面鎖上來。',
    check: ['支柱的長邊朝前後', '4 顆螺絲都鎖進柱子', '不要鎖太緊，PLA 會滑牙'],
    cam: [0, 0, 4, 0.55, -0.9, 0.75, 150] },
  { t: '先燒錄、設定', parts: ['board', 'usb'],
    how: '一體板先不要裝上去，也不要插電池。USB-C 線接電腦，用 ESP32 Web Flasher 燒官方 flix.esp32.merged.bin（位址 0，不用按鍵），再在主控台輸入 p IMU_MODEL 4、p PWR_VOLT_PIN 33、p PWR_VOLT_LOW 3.5，重開機。',
    check: ['電腦看得到 CH340 序列埠', '燒錄成功，不用按任何按鍵', '輸入 imu，狀態正常'],
    cam: [100, -14, 14, 0.25, -0.85, 0.9, 125] },
  { t: '鎖上一體板', parts: ['board', 'screwT'],
    how: 'FRONT 箭頭朝機頭（ESP32 天線朝前、USB-C 在左後方），把板子放在支柱上，用 4 顆 M1.4×5 從上面鎖進支柱。',
    check: ['FRONT 箭頭朝機頭', '板子放平、不會晃', '螺絲頭沒有壓到旁邊的零件'],
    cam: [0, 0, 10, 0.35, -0.85, 1.0, 140] },
  { t: '插馬達插頭', parts: ['plugs'],
    how: '每顆馬達的插頭插到最近的插座：M0 左後、M1 右後、M2 右前、M3 左前（板上絲印有寫）。線順著機臂拉，用膠帶貼好，不要伸進槳的範圍。',
    check: ['4 個插頭都插到底', '每顆馬達插在自己那一角', '馬達線貼在機臂上'],
    cam: [0, 0, 8, 0.15, -0.55, 1.0, 175] },
  { t: '裝電池、插電池插頭', parts: ['battery'],
    how: '電池從機尾推進機身下方的電池槽，電池線往上繞到後方凸片，插進 PH2.0 插座。插之前先確認電池插頭的紅線對板上的 +（PH2.0 電池正負極各家不一定一樣）。',
    check: ['紅線對 +、黑線對 −', '插上後沒有零件發燙', '電池線不會碰到槳'],
    cam: [0, -18, 2, 0.45, -1.0, 0.4, 150] },
  { t: '（選配）插感測器線 J8', parts: ['sensor'],
    how: '要做定高時才需要。J8 是直立的 4P 插座（JST SH 1.0 mm），在板子右後方、安裝孔旁邊。插之前先用三用電表確認 MTF-02 附的線是「直通線」（兩端 1 號腳相通）。插頭從上往下插到底，再點一點熱熔膠固定，線沿著機身後方往下拉到電池下面的感測器。J8 的 5V 平常是關的，程式把 IO4 拉高才會有電。',
    check: ['附線是直通線（1↔1、4↔4）', '插頭插到底、有熱熔膠固定', '線不會碰到槳，也不會被電池壓住'],
    cam: [10, -16, 10, 0.3, -0.85, 0.7, 75] },
  { t: '校正、測試、裝槳', parts: ['props'],
    how: '先拆槳，接上電池，用 QGroundControl 連線，ca 校正；用 mfl、mfr、mrl、mrr 測四顆馬達的位置和轉向。轉向反了就把那顆插頭的兩條線對調。都正確再裝槳：A 槳（黑）裝 M1、M3，B 槳（藍）裝 M0、M2。',
    check: ['四顆馬達位置、轉向都對', 'QGroundControl 轉動機身，姿態方向正確', '槳裝對型號、鎖緊'],
    cam: [0, 0, 0, 0.6, -0.8, 0.75, 270] },
];
const LABEL = { frame: '機身', motors: '馬達 ×4', posts: '支柱（carrier-posts）', screwB: 'M1.4×5 ×4（從底面）', board: '一體板', usb: 'USB-C 線（接電腦）',
  screwT: 'M1.4×5 ×4（從上面）', plugs: '馬達插頭 ×4', battery: '電池（PH2.0 插頭）', sensor: '感測器線（J8，選配）', props: '槳 ×4' };
const STEP_SENSOR = OSTEPS.findIndex(s => s.parts.includes('sensor')) + 1, STEP_PROPS = OSTEPS.length;

let inited = false;
export function initOnboard3D() {
  if (inited) return; inited = true;
  const view = document.getElementById('oView');
  const ui = id => document.getElementById(id);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  const SMALL = Math.min(screen.width, screen.height) < 700;
  renderer.setPixelRatio(Math.min(devicePixelRatio, SMALL ? 1.5 : 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  view.appendChild(renderer.domElement);
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0xeef1f5);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  const camera = new THREE.PerspectiveCamera(32, 1, 1, 4000); camera.up.set(0, 0, 1); camera.position.set(170, -210, 150);
  const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x9aa3ad, 0.6));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6); sun.position.set(90, -120, 260); sun.castShadow = true;
  sun.shadow.mapSize.set(SMALL ? 1024 : 2048, SMALL ? 1024 : 2048);
  Object.assign(sun.shadow.camera, { left: -150, right: 150, top: 150, bottom: -150, near: 10, far: 600 });
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.4; scene.add(sun);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), new THREE.ShadowMaterial({ opacity: 0.16 }));
  ground.position.z = FLOOR; ground.receiveShadow = true; scene.add(ground);
  const grid = new THREE.GridHelper(400, 40, 0xc3cad3, 0xd9dee5); grid.rotation.x = Math.PI / 2; grid.position.z = FLOOR - 0.05; scene.add(grid);

  // ---------- helpers ----------
  const mat = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.05, ...o });
  const metal = (color, r = 0.28) => mat(color, { metalness: 1, roughness: r });
  const box = (w, d, h, m, x = 0, y = 0, z = 0) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), m); o.position.set(x, y, z + h / 2); return o; };
  const cyl = (r, h, m, x = 0, y = 0, z = 0, seg = 32) => { const g = new THREE.CylinderGeometry(r, r, h, seg); g.rotateX(Math.PI / 2); const o = new THREE.Mesh(g, m); o.position.set(x, y, z + h / 2); return o; };
  const tube = (pts, r, color) => new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts.map(p => V(...p)), false, 'centripetal'), 64, r, 8, false), mat(color, { roughness: 0.45 }));
  function canvasTex(w, h, draw, px = 12) {
    const c = document.createElement('canvas'); c.width = w * px; c.height = h * px;
    const g = c.getContext('2d'); g.scale(px, px); draw(g, w, h);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
  }
  function stlMesh(key, m) {
    const d = MESH[key], bin = s => Uint8Array.from(atob(s), c => c.charCodeAt(0)).buffer;
    const q = new Int16Array(bin(d.p)), pos = new Float32Array(q.length);
    for (let i = 0; i < q.length; i++) pos[i] = q[i] * QS;
    const ib = bin(d.i), idx = d.n < 65535 ? new Uint16Array(ib) : new Uint32Array(ib);
    let g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setIndex(new THREE.BufferAttribute(idx, 1));
    g = g.toNonIndexed(); g.computeVertexNormals(); return new THREE.Mesh(g, m);
  }
  const items = [];
  function add(id, obj, base, { step, entry = V(0, 0, 30), keys = null, until = 99 }) {
    obj.position.copy(base);
    obj.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(obj);
    const it = { id, obj, base: base.clone(), appear: step, until, entry, keys: keys || [[step, V()]] };
    items.push(it); return it;
  }
  const offAt = (it, s) => { let o = V(); for (const [k, v] of it.keys) if (s >= k) o = v; return o.clone(); };

  // ---------- 1. 機身、馬達 ----------
  const PLA = mat(0xf3f1ea, { roughness: 0.72, side: THREE.DoubleSide });
  add('frame', stlMesh('frame', PLA), V(), { step: 1, entry: V(0, 0, 40) });
  function makeMotor() {
    const g = new THREE.Group();
    g.add(cyl(4.25, 16.4, metal(0xd2d5d9, 0.24), 0, 0, -6.5, 48));
    g.add(cyl(4.3, 2.6, mat(0xf3f3f0), 0, 0, -9, 48));
    g.add(cyl(3.3, 0.7, metal(0xd2d5d9, 0.2), 0, 0, 9.9, 32));
    g.add(cyl(1.25, 0.8, metal(0xc7924a, 0.35), 0, 0, 10.6, 24));
    g.add(cyl(0.5, 5.6, metal(0xe7e9ec, 0.18), 0, 0, 10.2, 16));
    return g;
  }
  MOT.forEach(m => add('motors', makeMotor(), V(m.mx * ARM, m.my * ARM, 1), { step: 1, entry: V(0, 0, 38) }));

  // ---------- 2. 支柱（照 pcb/posts.py）+ 底面螺絲 ----------
  const posts = new THREE.Group();
  POSTS.forEach(([x, y]) => posts.add(box(4, 4, POST_H, PLA, x, y, 0)));
  const PX = 13.51, PY = 17.5;
  posts.add(box(2 * PX, 2, 2, PLA, 0, PY, 0)); posts.add(box(2 * PX, 2, 2, PLA, 0, -PY, 0));
  posts.add(box(2, 2 * PY, 2, PLA, PX, 0, 0)); posts.add(box(2, 2 * PY, 2, PLA, -PX, 0, 0));
  add('posts', posts, V(0, 0, FRAME_TOP), { step: 2, entry: V(0, 0, 30) });
  function m14(flip) {
    const g = new THREE.Group(), s = metal(0x9da3aa, 0.3);
    g.add(cyl(1.25, 0.9, s, 0, 0, -0.9, 24)); g.add(box(0.3, 2.2, 0.35, mat(0x222222), 0, 0, -1.0));
    g.add(cyl(0.7, 5, s, 0, 0, 0, 12)); if (flip) g.rotation.x = Math.PI; return g;
  }
  POSTS.forEach(([x, y]) => add('screwB', m14(false), V(x, y, 0), { step: 2, entry: V(0, 0, -26) }));

  // ---------- 3. 一體板（Gerber 算圖貼圖 + 零件）----------
  const [X0, X1, Y0, Y1] = OB.bbox, BW = X1 - X0, BL = Y1 - Y0;
  const shape = new THREE.Shape();
  OB.outline.forEach(([x, y], i) => i ? shape.lineTo(x, y) : shape.moveTo(x, y));
  POSTS.forEach(([x, y]) => { const h = new THREE.Path(); h.absarc(x, y, OB.holeD / 2, 0, Math.PI * 2, true); shape.holes.push(h); });
  const loader = new THREE.TextureLoader();
  const tex = src => { const t = loader.load(src); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.repeat.set(1 / BW, 1 / BL); t.offset.set(-X0 / BW, -Y0 / BL); return t; };
  const pcb = new THREE.Group();
  const edge = mat(0x1d5a34, { roughness: 0.6 });
  pcb.add(new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: T, bevelEnabled: false, curveSegments: 16 }), [edge, edge]));
  const faceTop = new THREE.Mesh(new THREE.ShapeGeometry(shape, 16), new THREE.MeshStandardMaterial({ map: tex(OB.texTop), roughness: 0.45 }));
  faceTop.position.z = T + 0.01; pcb.add(faceTop);
  const faceBot = new THREE.Mesh(new THREE.ShapeGeometry(shape, 16), new THREE.MeshStandardMaterial({ map: tex(OB.texBottom), roughness: 0.45, side: THREE.BackSide }));
  faceBot.position.z = -0.01; pcb.add(faceBot);
  const BLK = mat(0x1b1c1f, { roughness: 0.5 }), TIN = metal(0xc9ccd0, 0.25), CREAM = mat(0xf2eee2, { roughness: 0.6 }), TAN = mat(0xb08a5a, { roughness: 0.6 });
  const label = (w, d, lines, bg = '#1b1c1f', fg = '#d8dade', size = 1.0) => new THREE.MeshStandardMaterial({ roughness: 0.5, map: canvasTex(w, d, (c, W, H) => {
    c.fillStyle = bg; c.fillRect(0, 0, W, H); c.fillStyle = fg; c.textAlign = 'center'; c.textBaseline = 'middle';
    lines.forEach((t, i) => { c.font = `${i ? '' : 'bold '}${size * (i ? 0.8 : 1)}px ${FONT}`; c.fillText(t, W / 2, H / 2 + (i - (lines.length - 1) / 2) * size * 1.3); });
  }, 30) });
  const topBox = (w, d, h, side, topM, x, y, z = 0) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), [side, side, side, side, topM, side]); o.position.set(x, y, z + h / 2); return o; };
  for (const c of OB.comps) {
    const [bx0, bx1] = c.bx, [by0, by1] = c.by, w = bx1 - bx0, d = by1 - by0, cx = (bx0 + bx1) / 2, cy = (by0 + by1) / 2, long = Math.max(w, d), alongX = w >= d;
    const g = new THREE.Group(); g.position.z = T;
    if (c.part === 'ESP32') {
      g.add(box(w, d, 0.8, mat(0x23262b), cx, cy, 0));
      const sl = 17.6, sw = w - 1.4;
      g.add(topBox(sw, sl, 2.3, metal(0xc6cacf, 0.3), label(sw, sl, ['ESP32-WROOM-32E', 'ESPRESSIF'], '#c9cdd2', '#4a4f57', 1.6), cx, by0 + 0.7 + sl / 2, 0.8));
      g.add(box(w - 2, 0.25, 0.05, metal(0xb8963c, 0.3), cx, by1 - 1.5, 0.8));   // 天線走線示意
    } else if (c.part === 'IMU') {
      g.add(topBox(3, 3, 0.91, BLK, label(3, 3, ['40609'], '#1b1c1f', '#8a8f96', 0.7), cx, cy));
    } else if (c.part === 'CH340C') {
      g.add(topBox(long, 3.9, 1.5, BLK, label(long, 3.9, ['CH340C'], '#1b1c1f', '#8a8f96', 1.0), cx, cy, 0.1));
      for (let i = 0; i < 8; i++) for (const s of [-1, 1]) g.add(box(0.42, 1.2, 0.25, TIN, cx - 4.445 + i * 1.27, cy + s * 2.45, 0));
    } else if (['AO3400A', 'AO3401A', 'MMBT3904', 'LDO'].includes(c.part)) {
      const bw = alongX ? 2.9 : 1.3, bd = alongX ? 1.3 : 2.9;
      g.add(box(bw, bd, 1.0, BLK, cx, cy, 0.05));
      const n = c.part === 'LDO' ? [3, 2] : [2, 1];
      [[-1, n[0]], [1, n[1]]].forEach(([s, k]) => { for (let i = 0; i < k; i++) { const t = k === 1 ? 0 : (i - (k - 1) / 2) * 1.9 / (k - 1) * (k === 3 ? 1 : 1); g.add(alongX ? box(0.4, 0.9, 0.2, TIN, cx + t, cy + s * 0.95, 0) : box(0.9, 0.4, 0.2, TIN, cx + s * 0.95, cy + t, 0)); } });
    } else if (c.part === 'B5819W') {
      g.add(box(1.6, 2.7, 1.1, BLK, cx, cy, 0)); g.add(box(1.62, 0.45, 1.12, mat(0x9aa0a8), cx, cy - 0.95, 0));
    } else if (c.part === 'LED') {
      g.add(box(1.6, 0.8, 0.6, mat(0xff3b30, { transparent: true, opacity: 0.85, emissive: 0x550000 }), cx, cy, 0));
    } else if (c.part === 'USBC') {
      g.add(box(w, d, 3.2, metal(0xc9cdd2, 0.22), cx, cy, 0));
      const hole = box(0.2, 8.2, 2.4, mat(0x111111), bx0 - 0.05, cy, 0.4); g.add(hole);
    } else if (c.part === 'TLV61070A') {   // SOT-23-6
      const bw = alongX ? 2.9 : 1.6, bd = alongX ? 1.6 : 2.9;
      g.add(box(bw, bd, 1.1, BLK, cx, cy, 0.05));
      for (const sd of [-1, 1]) for (const t of [-0.95, 0, 0.95]) g.add(alongX ? box(0.4, 0.8, 0.2, TIN, cx + t, cy + sd * 1.1, 0) : box(0.8, 0.4, 0.2, TIN, cx + sd * 1.1, cy + t, 0));
    } else if (c.part === 'L1u') {         // 2016 功率電感
      g.add(box(alongX ? 1.4 : 1.6, alongX ? 1.6 : 1.4, 1.0, mat(0x3a3d42, { roughness: 0.7 }), cx, cy, 0));
      for (const sd of [-1, 1]) g.add(alongX ? box(0.3, 1.6, 1.0, TIN, cx + sd * 0.85, cy, 0) : box(1.6, 0.3, 1.0, TIN, cx, cy + sd * 0.85, 0));
    } else if (c.part === 'SH4V') {        // JST SH 4P 立式（J8）：插頭從上面插
      g.add(box(w, d, 4.25, CREAM, cx, cy, 0));
      g.add(box(alongX ? 4.4 : 1.4, alongX ? 1.4 : 4.4, 0.2, mat(0x3a3a3a), cx, cy, 4.2));
    } else if (c.part === 'PH2' || c.part === 'PICO2' || c.part === 'SH4') {
      const h = c.part === 'PH2' ? 4.6 : c.part === 'SH4' ? 2.95 : 3.4;
      g.add(box(w, d, h, CREAM, cx, cy, 0));
      const open = c.part === 'PH2' ? box(5.6, 0.2, h - 1.2, mat(0x3a3a3a), cx, by0 - 0.05, 0.6) : box(0.2, c.part === 'SH4' ? 4.0 : 4.4, h - 1.0, mat(0x3a3a3a), c.x < 0 ? bx0 - 0.05 : bx1 + 0.05, cy, 0.5);
      g.add(open);
    } else {   // 0402 / 0603 / 0805 被動元件
      const isC = /[nuμ]$/.test(c.part) || /u$/.test(c.part), isR = !isC;
      const big = long > 1.8, tiny = long < 1.3, h = isR ? (tiny ? 0.35 : 0.45) : (big ? 1.25 : 0.8);
      const bl = big ? 2.0 : tiny ? 1.0 : 1.6, bw2 = big ? 1.25 : tiny ? 0.5 : 0.8;
      g.add(alongX ? box(bl - 0.6, bw2, h, isR ? BLK : TAN, cx, cy, 0) : box(bw2, bl - 0.6, h, isR ? BLK : TAN, cx, cy, 0));
      for (const s of [-1, 1]) g.add(alongX ? box(0.3, bw2, h, TIN, cx + s * (bl / 2 - 0.15), cy, 0) : box(bw2, 0.3, h, TIN, cx, cy + s * (bl / 2 - 0.15), 0));
    }
    pcb.add(g);
  }
  add('board', pcb, V(0, 0, BOARD_Z), { step: 3, entry: V(0, 0, 30), keys: [[3, SIDE], [4, V()]] });

  // USB-C 線（只在第 3 步）
  const usb = new THREE.Group();
  const j1 = OB.comps.find(c => c.ref === 'J1'), ux = j1.bx[0], uy = (j1.by[0] + j1.by[1]) / 2, uz = BOARD_Z + T + 1.6;
  usb.add(box(6.5, 8.6, 2.6, metal(0xc9cdd2, 0.22), ux - 2.6, uy, uz - 1.3));
  usb.add(box(12, 11, 6, mat(0x2b2d31), ux - 11.8, uy, uz - 3));
  usb.add(tube([[ux - 17.8, uy, uz], [ux - 30, uy - 4, uz - 6], [ux - 44, uy - 20, FLOOR + 3 - SIDE.z], [ux - 70, uy - 30, FLOOR + 1.5 - SIDE.z]], 1.9, 0x2b2d31));
  add('usb', usb, SIDE.clone(), { step: 3, until: 3, entry: V(-30, 0, 0) });

  POSTS.forEach(([x, y]) => add('screwT', m14(true), V(x, y, TOP + 0.9), { step: 4, entry: V(0, 0, 28) }));

  // ---------- 5. 馬達插頭與線 ----------
  const conn = { RL: 'J3', RR: 'J4', FR: 'J5', FL: 'J6' };
  const plugTags = [];
  MOT.forEach(m => {
    const c = OB.comps.find(k => k.ref === conn[m.k]), s = Math.sign(c.x), cy = (c.by[0] + c.by[1]) / 2;
    const face = s > 0 ? c.bx[1] : c.bx[0], wc = motorWires(m), g = new THREE.Group();
    const px = face + s * 2.4, z0 = TOP + 0.3;
    g.add(box(5.2, 4.0, 2.9, mat(0xf7f5ee, { roughness: 0.55 }), px, cy, z0));
    const end = px + s * 2.6, tip = V(m.mx * ARM, m.my * ARM, 0), dir = V(m.mx, m.my, 0).normalize();
    [[-0.62, wc.negHex], [0.62, wc.posHex]].forEach(([o, hex], i) => {
      const side = V(-dir.y, dir.x, 0).multiplyScalar(o * 1.6);
      const a = V(m.mx * 30, m.my * 30, 4.4).add(side), b = V(m.mx * 37, m.my * 37, 4.0).add(side), e = tip.clone().addScaledVector(dir, -6.2).add(side).setZ(-7);
      g.add(tube([[end, cy + o, z0 + 1.45], [end + s * 4, cy + o, z0 + 0.6], [a.x, a.y, a.z], [b.x, b.y, b.z], [e.x, e.y, 2], [e.x, e.y, e.z]], 0.42, parseInt(hex.slice(1), 16)));
    });
    add('plugs', g, V(), { step: 5, entry: V(s * 16, 0, 10) });
    plugTags.push({ m, p: V(px + s * 6, cy, z0 + 8) });
  });

  // ---------- 6. 電池 + PH2.0 插頭 ----------
  const bat = new THREE.Group();
  const wrap = canvasTex(25, 40, (c, w, h) => {
    c.fillStyle = '#e2e5e9'; c.fillRect(0, 0, w, h); c.fillStyle = '#1f4f8a'; c.fillRect(0, h * 0.28, w, h * 0.44);
    c.fillStyle = '#fff'; c.textAlign = 'center'; c.save(); c.translate(w / 2, h / 2); c.rotate(-Math.PI / 2);
    c.font = `bold 3px ${FONT}`; c.fillText('3.7V 1S Li-Po', 0, -1.4); c.font = `2.1px ${FONT}`; c.fillText('PH2.0 插頭', 0, 2.4); c.restore();
  });
  const bs = mat(0xd0d4d9, { roughness: 0.35, metalness: 0.3 }), bt = new THREE.MeshStandardMaterial({ map: wrap, roughness: 0.35 });
  const body = new THREE.Mesh(new THREE.BoxGeometry(25, 40, 9.5), [bs, bs, bs, bs, bt, bt]); body.position.z = 4.75; bat.add(body);
  bat.add(box(16, 2.6, 2.2, mat(0x2b7a3a), 0, -21.4, 3.0));
  const j2 = OB.comps.find(c => c.ref === 'J2'), py = j2.by[0] - 2.8, pz = TOP + 0.4 - (-10);   // 插頭（相對電池原點 z=-10）
  bat.add(box(5.8, 6.0, 3.8, mat(0xf7f5ee, { roughness: 0.55 }), 0, py, pz));
  [[-1, 0xd62828], [1, 0x161616]].forEach(([s, col]) => bat.add(tube([[s * 1.0, -22.6, 4.2], [s * 1.0, -30, 6], [s * 1.0, -34, 14], [s * 1.0, py - 6, pz + 3.5], [s * 1.0, py - 3, pz + 1.9]], 0.5, col)));
  add('battery', bat, V(0, 0, -10), { step: 6, entry: V(0, -70, 0) });

  // ---------- 7.（選配）J8 感測器插頭與線（示意：線往後、往下到電池下面的感測器）----------
  const sen = new THREE.Group();
  const j8 = OB.comps.find(c => c.ref === 'J8'), sx = (j8.bx[0] + j8.bx[1]) / 2, sy = (j8.by[0] + j8.by[1]) / 2, sz = TOP + 4.25;
  sen.add(box(1.9, 5.9, 2.9, mat(0xf7f5ee, { roughness: 0.55 }), sx, sy, sz));
  sen.add(box(2.4, 6.4, 0.8, mat(0xfff8d8, { roughness: 0.3, transparent: true, opacity: 0.75 }), sx, sy, sz + 2.6));   // 熱熔膠
  [[-1.5, 0x161616], [-0.5, 0xd62828], [0.5, 0xe8c21c], [1.5, 0x2e9e4f]].forEach(([o, col]) =>
    sen.add(tube([[sx, sy + o, sz + 2.9], [sx + 1, sy + o, sz + 7], [sx + 6, sy + o - 6, sz + 6], [sx + 9, -30, 4], [sx + 7, -32, -6], [4 + o * 0.6, -24, -12.5]], 0.32, col)));
  add('sensor', sen, V(), { step: STEP_SENSOR, entry: V(0, 0, 22) });

  // ---------- 8. 槳 ----------
  function blade(ccw) {
    const NR = 30, NC = 10, r0 = 2.2, r1 = 27.5, pos = [], idx = [];
    for (let i = 0; i <= NR; i++) {
      const t = i / NR, r = r0 + (r1 - r0) * t; let c = 2.6 + 3.6 * Math.sin(Math.PI * Math.min(1, Math.pow(t, 0.75) * 1.02));
      if (t > 0.86) c *= Math.sqrt(Math.max(0.02, 1 - Math.pow((t - 0.86) / 0.14, 2)));
      const th = Math.min(0.42, Math.atan(22 / (2 * Math.PI * r))), tk = 0.75 - 0.4 * t;
      for (const surf of [1, -1]) for (let j = 0; j <= NC; j++) {
        const s = j / NC - 0.5, thick = surf * tk * Math.sqrt(Math.max(0, 1 - 4 * s * s)) * 0.5 + 0.18 * (1 - 4 * s * s), yy = Math.max(c, 0.35) * s;
        let y = yy * Math.cos(th) - thick * Math.sin(th); const z = -yy * Math.sin(th) + thick * Math.cos(th); if (ccw) y = -y; pos.push(r, y, z);
      }
    }
    const row = 2 * (NC + 1);
    for (let i = 0; i < NR; i++) for (const off of [0, NC + 1]) for (let j = 0; j < NC; j++) { const a = i * row + off + j, b = a + 1, c2 = a + row, d = c2 + 1; idx.push(a, c2, b, b, c2, d); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals(); return g;
  }
  const spin = [];
  MOT.forEach(m => {
    const A = m.cw, M = mat(A ? 0x26282b : 0x1f6fd1, { roughness: 0.45, side: THREE.DoubleSide }), g = new THREE.Group(), bg = blade(!m.cw);
    [0, Math.PI].forEach(a => { const b = new THREE.Mesh(bg, M); b.rotation.z = a; g.add(b); });
    g.add(cyl(2.3, 4.6, M, 0, 0, -1.9, 24));
    add('props', g, V(m.mx * ARM, m.my * ARM, 14.2), { step: STEP_PROPS, entry: V(0, 0, 30) });
    spin.push({ g, dir: m.cw ? -1 : 1 });
  });

  // ---------- 標籤 ----------
  const tags = {};
  const mk = (cls, html) => { const el = document.createElement('div'); el.className = cls; el.innerHTML = html; el.style.display = 'none'; view.appendChild(el); return el; };
  Object.entries(LABEL).forEach(([id, t]) => { if (id !== 'plugs') tags[id] = mk('lbl', t); });   // 插頭用下面的 M0～M3 標籤
  const LOFF = { frame: V(30, -38, 4), motors: V(0, 0, 14), posts: V(0, -18, 10), screwB: V(0, 0, -3), board: V(0, 6, 8), usb: V(-48, -16, 4), screwT: V(0, 0, 3), plugs: V(0, 0, 0), battery: V(0, -8, 12), sensor: V(10, -14, 14), props: V(0, 0, 6) };
  const mtag = MOT.map(m => ({ m, el: mk('mtag ' + (m.cw ? 'cw' : 'ccw'), `<b>M${m.no} ${m.name}</b><br>${m.cw ? '順時針' : '逆時針'}・${m.cw ? 'A 槳' : 'B 槳'}`) }));
  const ptag = plugTags.map(t => ({ ...t, el: mk('mtag ' + (t.m.cw ? 'cw' : 'ccw'), `<b>M${t.m.no}</b> 插這裡`) }));
  const batTag = mk('mtag cw', '<b>紅線 → +</b><br>先對極性再插');
  const frontTag = mk('front', '▲ 機頭');
  const tmp = V();
  function place(el, p, show) {
    if (!show) { el.style.display = 'none'; return; }
    tmp.copy(p).project(camera); if (tmp.z > 1) { el.style.display = 'none'; return; }
    el.style.display = 'block'; el.style.left = (tmp.x * 0.5 + 0.5) * view.clientWidth + 'px'; el.style.top = (-tmp.y * 0.5 + 0.5) * view.clientHeight + 'px';
  }

  // ---------- 步驟 ----------
  let step = OSTEPS.length, anim = null, camGoal = null, playAll = null;
  const ease = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  function applyStep(s, u) {
    for (const it of items) {
      if (it.appear > s || s > it.until) { it.obj.visible = false; continue; }
      it.obj.visible = true;
      const to = offAt(it, s), from = it.appear === s ? to.clone().add(it.entry) : offAt(it, s - 1);
      it.obj.position.copy(it.base).add(from.lerp(to, ease(u)));
    }
  }
  const chips = ui('oChips');
  chips.innerHTML = OSTEPS.map((s, i) => `<button class="ochip" data-s="${i + 1}"><i>${i + 1}</i>${s.t}</button>`).join('');
  chips.querySelectorAll('button').forEach(b => b.onclick = () => { stop(); go(+b.dataset.s); });
  function go(s, animate = true) {
    step = Math.max(1, Math.min(OSTEPS.length, s));
    anim = animate ? { t0: performance.now(), dur: 1400 } : null; if (!animate) applyStep(step, 1);
    const c = OSTEPS[step - 1].cam, dir = V(c[3], c[4], c[5]).normalize();
    camGoal = { target: V(c[0], c[1], c[2]), pos: V(c[0], c[1], c[2]).addScaledVector(dir, c[6]) };
    const st = OSTEPS[step - 1];
    ui('oTitle').textContent = `步驟 ${step}／${OSTEPS.length}　${st.t}`;
    ui('oHow').textContent = st.how;
    ui('oCheck').innerHTML = st.check.map(t => `<li>${t}</li>`).join('');
    chips.querySelectorAll('button').forEach((b, i) => { b.classList.toggle('on', i + 1 === step); b.classList.toggle('done', i + 1 < step); });
  }
  function stop() { clearInterval(playAll); playAll = null; ui('oPlay').textContent = '▶ 從頭播放'; }
  ui('oPrev').onclick = () => { stop(); go(step - 1); };
  ui('oNext').onclick = () => { stop(); go(step + 1); };
  ui('oPlay').onclick = () => { if (playAll) return stop(); go(1); ui('oPlay').textContent = '■ 停止'; playAll = setInterval(() => { if (step >= OSTEPS.length) return stop(); go(step + 1); }, 3600); };
  ui('oXray').onchange = e => { PLA.transparent = e.target.checked; PLA.opacity = e.target.checked ? 0.3 : 1; PLA.depthWrite = !e.target.checked; PLA.needsUpdate = true; };

  function resize() { const w = view.clientWidth, h = view.clientHeight; if (!w || !h) return; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
  addEventListener('resize', resize);
  let last = performance.now();
  function loop(now) {
    requestAnimationFrame(loop);
    if (!view.clientWidth) { last = now; return; }
    if (renderer.domElement.width !== Math.round(view.clientWidth * renderer.getPixelRatio())) resize();
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    const u = anim ? Math.min(1, (now - anim.t0) / anim.dur) : 1; applyStep(step, u); if (u >= 1) anim = null;
    if (camGoal) { const k = 1 - Math.pow(0.002, dt); controls.target.lerp(camGoal.target, k); camera.position.lerp(camGoal.pos, k); if (camera.position.distanceTo(camGoal.pos) < 0.3) camGoal = null; }
    if (step === STEP_PROPS && !anim && ui('oSpin').checked) spin.forEach(p => { p.g.rotation.z += p.dir * dt * 7; });
    controls.update(); renderer.render(scene, camera);
    const showL = ui('oLabels').checked && !anim, parts = OSTEPS[step - 1].parts;
    Object.entries(tags).forEach(([id, el]) => {
      const it = items.find(i => i.id === id);
      place(el, it ? it.obj.getWorldPosition(V()).add(LOFF[id] || V()).add(id === 'plugs' ? V(-34, -4, 16) : V()) : V(), showL && it && it.obj.visible && parts.includes(id));
    });
    mtag.forEach(({ m, el }) => place(el, V(m.mx * (ARM + 16), m.my * (ARM + 16), 26), showL && (step === 1 || step === STEP_PROPS)));
    ptag.forEach(({ p, el }) => place(el, p, showL && step === 5));
    place(batTag, V(0, -40, 26), showL && step === 6);
    place(frontTag, V(0, 64, FRAME_TOP), ui('oLabels').checked);
  }
  resize(); go(1, false); requestAnimationFrame(loop);
  window.__fzo = { go: (n, a = false) => go(n, a), get step() { return step; } };
}

function check() { if (location.hash === '#onboard') initOnboard3D(); }
addEventListener('hashchange', check);
check();
