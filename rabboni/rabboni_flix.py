#!/usr/bin/env python3
"""
Rabboni 體感遙控器 → Flix 無人機

手拿 Rabboni 往前傾，無人機就往前飛；往右傾就往右飛。
油門、解鎖、降落用鍵盤控制（Rabboni 的按鍵不會傳到電腦）。

連線路徑：Rabboni ──藍牙 BLE──▶ 這支程式 ──Wi-Fi (MAVLink)──▶ Flix

安裝：
    pip install bleak pyflix

執行：
    python rabboni_flix.py              # 正式飛行（電腦要先連上 Wi-Fi「flix」）
    python rabboni_flix.py --no-drone   # 只看 Rabboni 傾斜，不連無人機（第一次一定先跑這個）
    python rabboni_flix.py --selftest   # 不用任何硬體，檢查換算公式

鍵盤：
    A        解鎖（油門必須是 0）
    ↑ / ↓    油門加減（W / S 也可以）
    ← / →    原地左轉 / 右轉（按住才轉）
    L        自動降落：油門慢慢降到 0，再上鎖
    空白鍵   緊急停止：馬達立刻停（飛機會掉下來，只在離地很低時用）
    C        重新校正

資料來源：
    Rabboni BLE 協定取自官方 PyPI 套件 Rabboni 2.0 與 rabboni-multi-python-sdk：
    資料特徵值 00001601-...，每包前 12 bytes 是 加速度 X/Y/Z、角速度 X/Y/Z（int16，大端序）。
    Flix 控制介面取自 pyflix（MIT 授權）：set_controls() 就是給「自訂遙控器」用的。
"""

import argparse
import asyncio
import json
import math
import os
import struct
import sys
import threading
import time

DATA_UUID = '00001601-0000-1000-8000-00805f9b34fb'
CONF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rabboni_calib.json')

# ---------- 安全設定（可以改，但請先不裝槳試過）----------
SEND_HZ = 20            # 每秒送幾次控制指令（Flix 超過 1 秒沒收到會自動降落）
DEADZONE_DEG = 5        # 傾斜小於這個角度當作沒傾斜，手抖不會亂飄
FULL_TILT_DEG = 35      # Rabboni 傾斜到這個角度＝搖桿推到底
THROTTLE_STEP = 0.02    # 每按一下 ↑↓ 油門變多少
THROTTLE_MAX = 0.8
LAND_SECONDS = 4        # 按 L 後幾秒內把油門降到 0
STALE_SECONDS = 0.6     # Rabboni 超過這麼久沒資料 → 視為斷線，自動降落


# ---------- 向量小工具 ----------
def norm(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n > 1e-9 else [0.0, 0.0, 0.0]

def dot(a, b):
    return sum(x * y for x, y in zip(a, b))

def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def parse_packet(data: bytes):
    """Rabboni 一包資料 → (加速度 xyz, 角速度 xyz)，單位是原始數值（只用方向，不必換算 g）"""
    ax, ay, az, gx, gy, gz = struct.unpack('>6h', bytes(data[:12]))
    return [ax, ay, az], [gx, gy, gz]


class Calibration:
    """
    兩步校正，Rabboni 怎麼拿都可以：
      1. 拿平不動：記下「上方」在 Rabboni 裡的方向 up
      2. 往前傾約 30 度：重力偏移的方向就是「前」fwd
      「右」用外積算：right = fwd × up
    之後任何時刻：前後傾角 = asin(a·fwd)、左右傾角 = asin(a·right)
    """
    def __init__(self, up=None, fwd=None):
        self.up, self.fwd = up, fwd
        self.right = norm(cross(fwd, up)) if up and fwd else None

    @classmethod
    def from_samples(cls, level, forward):
        up = norm(level)
        f = norm(forward)
        shift = [f[i] - dot(f, up) * up[i] for i in range(3)]
        if math.sqrt(dot(shift, shift)) < 0.2:      # 傾斜不到約 12 度，分不出方向
            raise ValueError('往前傾的角度太小，請傾斜約 30 度再按一次')
        return cls(up, norm(shift))

    def ok(self):
        return self.right is not None

    def angles(self, acc):
        """回傳 (前傾角, 右傾角)，單位度；往前、往右為正"""
        a = norm(acc)
        clamp = lambda x: max(-1.0, min(1.0, x))
        return math.degrees(math.asin(clamp(dot(a, self.fwd)))), math.degrees(math.asin(clamp(dot(a, self.right))))

    def save(self, path=CONF_FILE):
        with open(path, 'w') as f:
            json.dump({'up': self.up, 'fwd': self.fwd}, f)

    @classmethod
    def load(cls, path=CONF_FILE):
        try:
            with open(path) as f:
                d = json.load(f)
            return cls(d['up'], d['fwd'])
        except (OSError, KeyError, ValueError):
            return cls()


def stick(deg, max_out):
    """傾斜角 → 搖桿量 [-max_out, max_out]，含死區"""
    s = 1 if deg >= 0 else -1
    d = abs(deg)
    if d < DEADZONE_DEG:
        return 0.0
    x = min(1.0, (d - DEADZONE_DEG) / (FULL_TILT_DEG - DEADZONE_DEG))
    return s * x * max_out


# ---------- Rabboni（藍牙，背景執行緒）----------
class RabboniReader:
    def __init__(self, address=None):
        self.address = address
        self.acc = None           # 低通濾波後的加速度
        self.last = 0.0           # 最後收到資料的時間
        self.rate = 0.0           # 每秒幾包
        self.status = '尋找 Rabboni 中…'
        self._n, self._t0 = 0, time.time()
        self._stop = False
        threading.Thread(target=lambda: asyncio.run(self._run()), daemon=True).start()

    def _on_data(self, _sender, data):
        try:
            acc, _ = parse_packet(data)
        except struct.error:
            return
        if self.acc is None:
            self.acc = [float(x) for x in acc]
        else:
            k = 0.35                                      # 低通濾波：越小越平順、越慢
            self.acc = [p + k * (x - p) for p, x in zip(self.acc, acc)]
        self.last = time.time()
        self._n += 1
        if self.last - self._t0 >= 1:
            self.rate, self._n, self._t0 = self._n / (self.last - self._t0), 0, self.last

    async def _run(self):
        try:
            from bleak import BleakScanner, BleakClient
        except ImportError:
            self.status = '缺少 bleak：請先執行 pip install bleak'
            return
        while not self._stop:
            try:
                dev = self.address
                if not dev:
                    self.status = '掃描藍牙中…（按 Rabboni 右鍵 1 秒，綠燈閃爍）'
                    found = await BleakScanner.discover(timeout=6)
                    cands = [d for d in found if d.name and 'RABBONI' in d.name.upper()]
                    if not cands:
                        self.status = '找不到 Rabboni：按右鍵 1 秒讓綠燈閃爍，或用 --address 指定'
                        continue
                    dev = cands[0]
                self.status = '連線中…'
                async with BleakClient(dev, timeout=10) as client:
                    await client.start_notify(DATA_UUID, self._on_data)
                    self.status = f'已連線 {getattr(dev, "address", dev)}'
                    while client.is_connected and not self._stop:
                        await asyncio.sleep(0.5)
                self.status = 'Rabboni 斷線，重新連線中…'
            except Exception as e:                      # noqa: BLE001  藍牙錯誤種類很多，一律重試
                self.status = f'藍牙錯誤：{e}，3 秒後重試'
                await asyncio.sleep(3)

    def fresh(self):
        return self.acc is not None and time.time() - self.last < STALE_SECONDS


# ---------- Flix（Wi-Fi，背景執行緒）----------
class Drone:
    def __init__(self, enabled=True):
        self.flix = None
        self.status = '不連無人機（--no-drone）' if not enabled else '等待 Flix…（電腦要連上 Wi-Fi「flix」）'
        if enabled:
            threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self):
        try:
            from pyflix import Flix
        except ImportError:
            self.status = '缺少 pyflix：請先執行 pip install pyflix'
            return
        try:
            self.flix = Flix()
            self.status = '已連上 Flix'
            if self.flix.mode != 'STAB':
                self.flix.set_mode('STAB')
        except Exception as e:  # noqa: BLE001
            self.status = f'連不上 Flix：{e}'

    @property
    def ready(self):
        return self.flix is not None and self.flix.connected

    def send(self, roll, pitch, yaw, throttle):
        if self.ready:
            self.flix.set_controls(roll=roll, pitch=pitch, yaw=yaw, throttle=throttle)

    def arm(self, on):
        if self.ready:
            self.flix.set_armed(on)


# ---------- 視窗 ----------
def run_gui(args):
    import tkinter as tk

    rab = RabboniReader(args.address)
    drone = Drone(not args.no_drone)
    cal = Calibration.load()
    st = {'thr': 0.0, 'yaw': 0.0, 'landing': False, 'calib': None, 'level': None, 'msg': ''}

    root = tk.Tk()
    root.title('Rabboni 體感遙控 × Flix')
    FONT = ('PingFang TC', 14) if sys.platform == 'darwin' else ('Microsoft JhengHei', 12)
    top = tk.Label(root, justify='left', anchor='w', font=FONT); top.pack(fill='x', padx=12, pady=(10, 4))
    cv = tk.Canvas(root, width=520, height=320, bg='#f4f6f9', highlightthickness=0); cv.pack(padx=12)
    info = tk.Label(root, justify='left', anchor='w', font=FONT, fg='#b01e1e'); info.pack(fill='x', padx=12)
    help_ = tk.Label(root, justify='left', anchor='w', font=(FONT[0], FONT[1] - 2), fg='#4a5563', text=(
        'A 解鎖　↑↓ 油門　←→ 轉向（按住）　L 自動降落　空白鍵 緊急停止　C 重新校正\n'
        f'傾斜上限：搖桿最多推到 {int(args.max * 100)}%（約 {args.max * 30:.0f} 度）。用 --max 調整。'))
    help_.pack(fill='x', padx=12, pady=(4, 10))

    def start_calib():
        st['calib'], st['level'] = 'level', None
        st['msg'] = '校正①：把 Rabboni 拿在平常握的位置、拿平不動，按 Enter'

    def on_key(e):
        k = e.keysym.lower()
        if st['calib']:
            if k == 'return':
                if not rab.fresh():
                    st['msg'] = '還沒收到 Rabboni 資料'
                elif st['calib'] == 'level':
                    st['level'], st['calib'] = list(rab.acc), 'fwd'
                    st['msg'] = '校正②：往前傾約 30 度（像要讓飛機往前飛）不動，按 Enter'
                else:
                    try:
                        c = Calibration.from_samples(st['level'], rab.acc)
                    except ValueError as err:
                        st['msg'] = str(err); return
                    cal.__init__(c.up, c.fwd); cal.save(); st['calib'] = None
                    st['msg'] = '校正完成。往右傾，畫面上的點要往右；不對就按 C 重來'
            return
        if k == 'space':
            drone.arm(False); st.update(thr=0.0, landing=False); st['msg'] = '緊急停止：已上鎖'
        elif k == 'a':
            if st['thr'] > 0.001:
                st['msg'] = '油門要先降到 0 才能解鎖'
            elif not cal.ok():
                st['msg'] = '還沒校正，先按 C'
            elif not rab.fresh():
                st['msg'] = 'Rabboni 沒有資料，不能解鎖'
            else:
                drone.arm(True); st['msg'] = '已解鎖：用 ↑ 慢慢加油門'
        elif k in ('up', 'w'):
            st['landing'] = False; st['thr'] = min(THROTTLE_MAX, st['thr'] + THROTTLE_STEP)
        elif k in ('down', 's'):
            st['thr'] = max(0.0, st['thr'] - THROTTLE_STEP)
        elif k == 'left':
            st['yaw'] = -0.5
        elif k == 'right':
            st['yaw'] = 0.5
        elif k == 'l':
            st['landing'] = True; st['msg'] = '自動降落中…'
        elif k == 'c':
            start_calib()

    def on_release(e):
        if e.keysym.lower() in ('left', 'right'):
            st['yaw'] = 0.0

    root.bind('<KeyPress>', on_key)
    root.bind('<KeyRelease>', on_release)
    if not cal.ok():
        start_calib()

    def tick():
        roll = pitch = 0.0
        p_deg = r_deg = 0.0
        if st['landing']:
            st['thr'] = max(0.0, st['thr'] - THROTTLE_MAX / (LAND_SECONDS * SEND_HZ))
            if st['thr'] == 0.0:
                drone.arm(False); st['landing'] = False; st['msg'] = '已降落並上鎖'
        if rab.fresh() and cal.ok() and not st['calib']:
            p_deg, r_deg = cal.angles(rab.acc)
            pitch, roll = stick(p_deg, args.max), stick(r_deg, args.max)
        elif st['thr'] > 0 and not st['landing']:
            st['landing'] = True; st['msg'] = 'Rabboni 斷線 → 自動降落'
        drone.send(roll, pitch, st['yaw'], st['thr'])

        # 畫面
        top.config(text=f'Rabboni：{rab.status}（{rab.rate:.0f} 筆/秒）\n無人機：{drone.status}')
        info.config(text=st['msg'])
        cv.delete('all')
        cx, cy, R = 170, 160, 130
        cv.create_oval(cx - R, cy - R, cx + R, cy + R, outline='#c9d1dc', width=2)
        dz = R * DEADZONE_DEG / FULL_TILT_DEG
        cv.create_oval(cx - dz, cy - dz, cx + dz, cy + dz, outline='#dfe5ec', dash=(3, 3))
        cv.create_line(cx - R, cy, cx + R, cy, fill='#dfe5ec'); cv.create_line(cx, cy - R, cx, cy + R, fill='#dfe5ec')
        cv.create_text(cx, cy - R - 10, text='前', font=FONT); cv.create_text(cx + R + 12, cy, text='右', font=FONT)
        x = cx + R * max(-1, min(1, r_deg / FULL_TILT_DEG)); y = cy - R * max(-1, min(1, p_deg / FULL_TILT_DEG))
        col = '#2c5fb3' if rab.fresh() else '#9aa3ad'
        cv.create_oval(x - 11, y - 11, x + 11, y + 11, fill=col, outline='')
        cv.create_text(cx, cy + R + 14, text=f'前後 {p_deg:+5.1f}°　左右 {r_deg:+5.1f}°', font=FONT)
        bx, by, bh = 380, 30, 260
        cv.create_rectangle(bx, by, bx + 40, by + bh, outline='#c9d1dc', width=2)
        h = bh * st['thr'] / THROTTLE_MAX
        cv.create_rectangle(bx + 2, by + bh - h, bx + 38, by + bh - 1, fill='#d62828' if st['landing'] else '#2f9e44', outline='')
        cv.create_text(bx + 20, by + bh + 16, text=f'油門 {st["thr"]:.2f}', font=FONT)
        armed = drone.ready and drone.flix.armed
        cv.create_text(470, 60, text='已解鎖' if armed else '上鎖', fill='#d62828' if armed else '#4a5563', font=(FONT[0], FONT[1] + 2, 'bold'))
        if drone.ready and not math.isnan(drone.flix.voltage or float('nan')):
            cv.create_text(470, 92, text=f'電池 {drone.flix.voltage:.2f}V', font=FONT)
        cv.create_text(470, 124, text=f'送出 roll {roll:+.2f}\n     pitch {pitch:+.2f}', font=(FONT[0], FONT[1] - 2))
        root.after(int(1000 / SEND_HZ), tick)

    tick()
    root.mainloop()


# ---------- 不用硬體的自我檢查 ----------
def selftest(trials=300):
    """模擬學生用任意角度握 Rabboni：校正後，往前傾要得到正的前後角、往右傾要得到正的左右角"""
    import random

    def mat(axis, deg):
        a = math.radians(deg); c, s = math.cos(a), math.sin(a)
        return {'x': [[1, 0, 0], [0, c, -s], [0, s, c]],
                'y': [[c, 0, s], [0, 1, 0], [-s, 0, c]],
                'z': [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis]

    def mul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

    def reading(W, M):            # 機身座標＝前左上（FLU）；加速度計量到「上方」在 Rabboni 裡的方向
        D = mul(W, M)
        return [D[2][i] * 16384 for i in range(3)]   # = Dᵀ · (0,0,1)

    I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    for _ in range(trials):
        M = mul(mat('z', random.uniform(-180, 180)), mul(mat('y', random.uniform(-70, 70)), mat('x', random.uniform(-70, 70))))
        c = Calibration.from_samples(reading(I, M), reading(mat('y', 30), M))   # 繞左軸正轉＝機頭朝下＝往前
        p, r = c.angles(reading(mat('x', 20), M))                               # 繞前軸正轉＝右邊朝下＝往右
        assert abs(p) < 0.6 and abs(r - 20) < 0.6, (p, r)
        p, r = c.angles(reading(mat('y', -15), M))                              # 往後 15 度
        assert abs(p + 15) < 0.6 and abs(r) < 0.6, (p, r)
    assert stick(3, 0.5) == 0 and abs(stick(FULL_TILT_DEG, 0.5) - 0.5) < 1e-9 and stick(-90, 0.5) == -0.5
    pkt = struct.pack('>6h', 100, -200, 16384, 1, 2, 3) + b'\x00\x01\x00\x02'
    assert parse_packet(pkt)[0] == [100, -200, 16384]
    print(f'自我檢查通過：{trials} 種握法，往前傾、往右傾、往後傾的角度和正負號都正確。')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Rabboni 體感遙控 Flix 無人機')
    ap.add_argument('--no-drone', action='store_true', help='只看 Rabboni 傾斜，不連無人機')
    ap.add_argument('--address', help='Rabboni 的藍牙位址（Mac 上是一串 UUID）；不填就自動找')
    ap.add_argument('--max', type=float, default=0.5, help='搖桿最大量 0.1–1（預設 0.5，約 15 度）')
    ap.add_argument('--selftest', action='store_true', help='不用硬體，檢查換算公式')
    a = ap.parse_args()
    if a.selftest:
        selftest()
    else:
        a.max = max(0.1, min(1.0, a.max))
        run_gui(a)
