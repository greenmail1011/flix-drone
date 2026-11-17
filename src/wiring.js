// 中文接線圖（SVG）與接線表。只依賴 data.js，瀏覽器和 node 都能用。
import { WIRES, WIRE_GROUPS, MOTORS, MINI_COLS, MINI_PINS, IMU_PINS, motorWires } from './data.js';

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const FONT = "'Noto Sans TC','PingFang TC','Microsoft JhengHei',sans-serif";

export function wiringSVG() {
  const W = 1140, H = 810;
  const out = [];
  const t = (x, y, s, o = {}) => out.push(`<text x="${x}" y="${y}" font-size="${o.size || 13}" ${o.anchor ? `text-anchor="${o.anchor}"` : ''} ${o.bold ? 'font-weight="700"' : ''} fill="${o.fill || '#1d2430'}">${esc(s)}</text>`);
  const line = (pts, color, w = 3.2, outline = false) => {
    const d = 'M' + pts.map(p => p.join(',')).join(' L');
    out.push(`<path d="${d}" fill="none" stroke="#fff" stroke-width="${w + 4}" stroke-linejoin="round"/>`);
    if (outline) out.push(`<path d="${d}" fill="none" stroke="#8a8f96" stroke-width="${w + 1.6}" stroke-linejoin="round"/>`);
    out.push(`<path d="${d}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"/>`);
  };
  const dot = (x, y, c, r = 4.5) => out.push(`<circle cx="${x}" cy="${y}" r="${r}" fill="${c}" stroke="#fff" stroke-width="1.5"/>`);
  const badge = (x, y, s) => { out.push(`<circle cx="${x}" cy="${y}" r="9" fill="#fff8d6" stroke="#b08c00" stroke-width="1.4"/>`); t(x, y + 4.5, s, { size: 12, anchor: 'middle', bold: true, fill: '#6b5400' }); };
  const rowY = r => 150 + (r - 1) * 38;
  const colX = { LO: 470, LI: 530, RI: 640, RO: 700 };
  const used = {};
  WIRES.forEach(w => { if (w.pin) used[w.pin.join()] = w.hex; });

  out.push(`<rect width="${W}" height="${H}" fill="#fbfcfd"/>`);
  t(30, 38, 'FutureZebra 程控無人機（Flix）接線圖', { size: 22, bold: true });
  t(30, 62, '主板 MINI32 以「正面（元件面）朝上、天線朝上」來看。紅＝正極、黑＝接地、黃＝訊號；①～④ 是黃線的編號貼紙。', { size: 13, fill: '#4a5563' });

  // ---- MINI32
  out.push(`<rect x="440" y="92" width="290" height="456" rx="10" fill="#1765a8"/>`);
  out.push(`<rect x="500" y="98" width="170" height="30" rx="3" fill="#15191d"/>`);
  t(585, 118, 'ESP32 模組（天線端）', { size: 12, anchor: 'middle', fill: '#e6edf5' });
  t(585, 532, 'USB 端　MINI32', { size: 12, anchor: 'middle', fill: '#e6edf5', bold: true });
  Object.entries(colX).forEach(([col, x]) => {
    for (let r = 1; r <= 10; r++) {
      const y = rowY(r), name = MINI_PINS[col][r - 1], c = used[[col, r].join()];
      out.push(`<circle cx="${x}" cy="${y}" r="7" fill="${c || '#e3c26b'}" stroke="${c ? '#fff' : '#b9952f'}" stroke-width="${c ? 2.5 : 1}"/>`);
      if (!c) out.push(`<circle cx="${x}" cy="${y}" r="2.8" fill="#123f66"/>`);
      const left = col === 'LO' || col === 'LI';
      t(left ? x + 12 : x - 12, y + 4.5, name, { size: 11.5, anchor: left ? 'start' : 'end', bold: !!c, fill: c ? '#ffe14d' : '#cfe0f0' });
    }
  });
  t(470, 86, '左外排', { size: 11, anchor: 'middle', fill: '#4a5563' }); t(530, 86, '左內排', { size: 11, anchor: 'middle', fill: '#4a5563' });
  t(640, 86, '右內排', { size: 11, anchor: 'middle', fill: '#4a5563' }); t(700, 86, '右外排', { size: 11, anchor: 'middle', fill: '#4a5563' });
  // 列號
  for (let r = 1; r <= 10; r++) t(436, rowY(r) + 4, r, { size: 10, anchor: 'end', fill: '#8a94a3' });

  // ---- GY-91（印字面朝上）
  out.push(`<rect x="70" y="122" width="160" height="318" rx="10" fill="#5b1f80"/>`);
  t(150, 112, 'GY-91（IMU）印字面朝上', { size: 13, anchor: 'middle', bold: true, fill: '#5b1f80' });
  IMU_PINS.forEach((n, i) => {
    const y = rowY(i + 1), w = WIRES.find(x => x.imu === i);
    out.push(`<circle cx="230" cy="${y}" r="7" fill="${w ? w.hex : '#e0bd5f'}" stroke="#fff" stroke-width="${w ? 2.5 : 1}"/>`);
    t(216, y + 4.5, w ? n : `（不接）${n}`, { size: 12, anchor: 'end', bold: !!w, fill: w ? '#fff' : '#d6b8e6' });
  });
  // IMU 六條線：先水平出去、走自己的直巷、再從兩排孔之間進去
  const lane = { I2: 262, I1: 284, I3: 330, I4: 350, I5: 370, I6: 390 };
  WIRES.filter(w => w.g === 'imu').forEach(w => {
    const y0 = rowY(w.imu + 1), [col, r] = w.pin, x1 = colX[col], y1 = rowY(r), lx = lane[w.id];
    const pts = col === 'LO' ? [[237, y0], [lx, y0], [lx, y1], [x1 - 8, y1]] : [[237, y0], [lx, y0], [lx, y1 - 19], [x1, y1 - 19], [x1, y1 - 8]];
    line(pts, w.hex);
    if (w.tag) { badge(252, y0 - 12, w.tag); badge(x1 - 18, y1 - 19, w.tag); }
  });

  // ---- 馬達通道
  const chan = (m, bx, by) => {
    const w = motorWires(m);
    out.push(`<rect x="${bx}" y="${by}" width="300" height="172" rx="10" fill="#fff" stroke="#c9d1dc"/>`);
    t(bx + 12, by + 22, `馬達 ${m.no}　${m.name}`, { size: 14, bold: true });
    t(bx + 12, by + 40, `GPIO${m.gpio}　${m.cw ? '順時針・A 槳' : '逆時針・B 槳'}　馬達線：${w.neg}${w.pos}`, { size: 11.5, fill: '#4a5563' });
    const G = [bx, by + 105];
    // 電阻（G 到 S 之間）
    out.push(`<path d="M${bx + 62},${by + 105} L${bx + 62},${by + 116} l7,4 l-14,6 l14,6 l-14,6 l14,6 l-7,4 L${bx + 62},${by + 155}" fill="none" stroke="#8a6a3c" stroke-width="2.4"/>`);
    t(bx + 74, by + 140, '10 kΩ', { size: 11, fill: '#6b4f22' });
    // MOSFET
    out.push(`<rect x="${bx + 112}" y="${by + 72}" width="78" height="66" rx="6" fill="#26292d"/>`);
    t(bx + 151, by + 101, 'MOSFET', { size: 11.5, anchor: 'middle', fill: '#fff', bold: true });
    t(bx + 151, by + 116, '100N03A', { size: 10.5, anchor: 'middle', fill: '#c9ced6' });
    t(bx + 117, by + 132, 'G', { size: 11, fill: '#ffd84d', bold: true }); t(bx + 151, by + 84, 'D', { size: 11, anchor: 'middle', fill: '#ffd84d', bold: true }); t(bx + 176, by + 132, 'S', { size: 11, fill: '#ffd84d', bold: true });
    line([[bx + 4, by + 105], [bx + 112, by + 105]], '#f2c200');
    line([[bx + 151, by + 138], [bx + 151, by + 155], [bx + 62, by + 155]], '#1b1b1b');
    line([[bx + 151, by + 155], [bx + 288, by + 155]], '#1b1b1b');
    dot(bx + 62, by + 105, '#8a6a3c', 3.5); dot(bx + 151, by + 155, '#1b1b1b', 3.5);
    t(bx + 288, by + 168, '接黑色匯流點', { size: 11, anchor: 'end', fill: '#4a5563' });
    // 馬達
    line([[bx + 151, by + 72], [bx + 151, by + 58], [bx + 206, by + 58]], w.negHex, 3.2, w.negHex === '#f2f2f2');
    out.push(`<circle cx="${bx + 226}" cy="${by + 58}" r="18" fill="#dfe3e8" stroke="#7d8590" stroke-width="2"/>`);
    t(bx + 226, by + 63, 'M', { size: 15, anchor: 'middle', bold: true });
    t(bx + 202, by + 50, '−', { size: 14, anchor: 'end', bold: true }); t(bx + 250, by + 50, '+', { size: 14, bold: true });
    line([[bx + 246, by + 58], [bx + 288, by + 58]], w.posHex, 3.2, w.posHex === '#f2f2f2');
    t(bx + 290, by + 96, '接紅色匯流點', { size: 11, anchor: 'end', fill: '#b01e1e' });
    return G;
  };
  const M = Object.fromEntries(MOTORS.map(m => [m.no, m]));
  const g0 = chan(M[0], 800, 96), g3 = chan(M[3], 800, 296), g1 = chan(M[1], 800, 496), g2 = chan(M[2], 60, 470);
  line([[colX.RO + 8, rowY(5)], [756, rowY(5)], [756, g0[1]], g0], '#f2c200');
  line([[colX.RI, rowY(9) - 8], [colX.RI, rowY(9) - 19], [772, rowY(9) - 19], [772, g3[1]], g3], '#f2c200');
  line([[colX.LI, rowY(9) + 8], [colX.LI, rowY(9) + 19], [786, rowY(9) + 19], [786, g1[1]], g1], '#f2c200');
  line([[colX.LO - 8, rowY(7)], [420, rowY(7)], [420, 452], [40, 452], [40, g2[1]], g2], '#f2c200');
  [[g0, 'GPIO12'], [g3, 'GPIO15'], [g1, 'GPIO13'], [g2, 'GPIO14']].forEach(([g, s]) => t(g[0] + 8, g[1] - 8, s, { size: 11, bold: true, fill: '#8a6d00' }));

  // ---- 電源
  const py = 610;
  out.push(`<rect x="390" y="${py - 30}" width="390" height="210" rx="10" fill="#fff" stroke="#c9d1dc"/>`);
  t(404, py - 8, '電源（兩個匯流點：焊在一起後套熱縮套管）', { size: 14, bold: true });
  out.push(`<rect x="408" y="${py + 30}" width="96" height="120" rx="8" fill="#d7dbe0" stroke="#9aa3ad"/>`);
  out.push(`<rect x="408" y="${py + 62}" width="96" height="52" fill="#1f4f8a"/>`);
  t(456, py + 85, '1S 鋰電池', { size: 12, anchor: 'middle', fill: '#fff', bold: true }); t(456, py + 102, '3.7V', { size: 11, anchor: 'middle', fill: '#fff' });
  t(456, py + 22, 'MX2.0 插頭', { size: 11, anchor: 'middle', fill: '#4a5563' });
  line([[504, py + 48], [560, py + 48]], '#d62828', 3.6); line([[504, py + 132], [560, py + 132]], '#1b1b1b', 3.6);
  t(520, py + 42, '+', { size: 14, bold: true, fill: '#d62828' }); t(520, py + 126, '−', { size: 14, bold: true });
  dot(566, py + 48, '#d62828', 8); dot(566, py + 132, '#1b1b1b', 8);
  t(584, py + 40, '紅色匯流點 →', { size: 12.5, bold: true, fill: '#b01e1e' });
  t(584, py + 58, '主板 VCC（右內排第 8 孔）', { size: 12 }); t(584, py + 75, '4 顆馬達的正極（白線、紅線）', { size: 12 });
  t(584, py + 124, '黑色匯流點 →', { size: 12.5, bold: true });
  t(584, py + 142, '主板 GND（右內排第 7 孔）', { size: 12 }); t(584, py + 159, '4 顆 MOSFET 的 S 腳', { size: 12 });
  // 主板上 VCC/GND 兩孔旁的提示
  t(640, 566, '↑ VCC、GND 接電源匯流點', { size: 11.5, anchor: 'middle', fill: '#b01e1e', bold: true });

  // ---- 注意
  t(30, 700, '注意', { size: 13, bold: true, fill: '#b01e1e' });
  ['先焊好、量過不短路，才接電池。', '插著 USB 時不要轉馬達，要用電池供電。', 'MOSFET：G＝左腳、S＝右腳（字面朝上、腳朝自己），', '　D＝背面大散熱片（接馬達負極）。', '腳位來源：Flix 官方 README／assembly.md、', '　MH-ET LIVE MiniKit 腳位圖。'].forEach((s, i) => t(30, 720 + i * 16, s, { size: 11.5, fill: '#4a5563' }));
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" font-family="${FONT}">${out.join('')}</svg>`;
}

export function wiringTableHTML() {
  return Object.entries(WIRE_GROUPS).map(([g, name]) =>
    `<tr class="grp"><th colspan="5">${name}</th></tr>` + WIRES.filter(w => w.g === g).map(w =>
      `<tr data-w="${w.id}"><td>${w.id}</td><td><i class="sw" style="background:${w.hex}"></i>${w.color}</td><td>${w.from}</td><td>${w.to}</td><td>${w.fn}</td></tr>`).join('')).join('');
}
