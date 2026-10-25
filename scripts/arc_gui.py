"""
Project A.R.C - Mission Control dashboard.

A single 1280x720 window drawn entirely with OpenCV (no Qt/Tk dependency):
  * live camera view with target overlay
  * FSM state chips, telemetry cards, live power graph
  * target-position bar (p_target)
  * clickable colour presets + draggable HSV sliders + detector-mask preview

Keys:  1/2/3 = presets   M = mask overlay   Q = quit
"""
from collections import deque

import cv2
import numpy as np

W, H = 1280, 720

# ---- Palette (BGR) ---------------------------------------------------------
BG_TOP, BG_BOT = (30, 22, 18), (16, 11, 8)
CARD, CARD_HI, BORDER = (43, 31, 26), (58, 44, 36), (712800, 52, 44)
TEXT, MUTED, DIM = (242, 234, 230), (160, 142, 128), (96, 82, 72)
CYAN, GREEN, AMBER = (238, 211, 34), (153, 211, 52), (36, 191, 251)
RED, PURPLE, INK = (113, 113, 248), (250, 139, 167), (22, 16, 12)

FONT, FONT_B, AA = cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX, cv2.LINE_AA

STATES = ["IDLE", "ACQUIRE", "FORWARD", "CLEAN", "DOCK"]
STATE_COLORS = {"IDLE": MUTED, "ACQUIRE": AMBER, "FORWARD": CYAN,
                "CLEAN": GREEN, "DOCK": PURPLE}

# ---- Layout ----------------------------------------------------------------
VID_X, VID_Y, VID_W, VID_H = 20, 76, 640, 480
TGT = (20, 570, 640, 120)
RX, RW = 680, 580
SL_X0, SL_X1, SL_Y0, SL_DY = 985, 1195, 462, 36
SL_MAX = [179, 179, 255, 255, 255, 255]
SL_LABELS = ["H MIN", "H MAX", "S MIN", "S MAX", "V MIN", "V MAX"]
THUMB = (696, 430, 220, 165)
GRAPH_PLOT = (696, 264, 1244, 318)   # x0, y0, x1, y1
BAR_X0, BAR_X1, BAR_Y0, BAR_Y1 = 36, 644, 628, 644
HIST_LEN = 300


# ---- Drawing helpers -------------------------------------------------------
def _rrect(img, x, y, w, h, color, r=12):
    r = max(1, min(r, w // 2, h // 2))
    cv2.rectangle(img, (x + r, y), (x + w - r, y + h), color, -1)
    cv2.rectangle(img, (x, y + r), (x + w, y + h - r), color, -1)
    for cx, cy in ((x + r, y + r), (x + w - r, y + r),
                   (x + r, y + h - r), (x + w - r, y + h - r)):
        cv2.circle(img, (cx, cy), r, color, -1, AA)


def _card(img, x, y, w, h, fill=CARD, border=BORDER, r=14):
    _rrect(img, x, y, w, h, border, r)
    _rrect(img, x + 1, y + 1, w - 2, h - 2, fill, r - 1)


def _text(img, s, x, y, scale=0.5, color=TEXT, thick=1, font=FONT, align='l'):
    (tw, _), _ = cv2.getTextSize(s, font, scale, thick)
    if align == 'r':
        x -= tw
    elif align == 'c':
        x -= tw // 2
    cv2.putText(img, s, (int(x), int(y)), font, scale, color, thick, AA)
    return tw


def _alpha_rect(img, x, y, w, h, color, alpha=0.6):
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, img.shape[1]), min(y + h, img.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    roi = img[y0:y1, x0:x1]
    img[y0:y1, x0:x1] = cv2.addWeighted(roi, 1 - alpha, np.full_like(roi, color), alpha, 0)


class Dashboard:
    def __init__(self, presets, active, win="A.R.C Mission Control", headless=False):
        self.win = win
        self.presets = dict(presets)
        self.names = list(self.presets.keys())
        self.values = list(self.presets[active])
        self.active = active
        self.mask_overlay = False
        self.drag = None
        self.hist = deque(maxlen=HIST_LEN)
        self.btn_rects = [(696 + i * 140, 384, 130, 30) for i in range(len(self.names))]

        c0, c1 = np.array(PURPLE, float), np.array(CYAN, float)
        t = np.linspace(0, 1, BAR_X1 - BAR_X0)[:, None]
        strip = (c0 * (1 - t) + c1 * t).astype(np.uint8)
        self._strip = np.tile(strip[None], (BAR_Y1 - BAR_Y0, 1, 1))
        self._static = self._build_static()

        if not headless:
            cv2.namedWindow(win, cv2.WINDOW_GUI_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.resizeWindow(win, W, H)
            cv2.setMouseCallback(win, self._on_mouse)

    # ------------------------------------------------------------------ API
    def get_hsv(self):
        return tuple(self.values)

    def show(self, canvas):
        cv2.imshow(self.win, canvas)

    def handle_key(self, key):
        """Returns True when the user asked to quit."""
        k = key & 0xFF
        if k in (ord('q'), 27):
            return True
        if k == ord('m'):
            self.mask_overlay = not self.mask_overlay
        elif ord('1') <= k <= ord('9'):
            idx = k - ord('1')
            if idx < len(self.names):
                self.apply_preset(self.names[idx])
        return False

    def apply_preset(self, name):
        self.values = list(self.presets[name])
        self.active = name

    # ---------------------------------------------------------------- mouse
    def _set_slider(self, i, x):
        v = round((x - SL_X0) / (SL_X1 - SL_X0) * SL_MAX[i])
        self.values[i] = int(min(max(v, 0), SL_MAX[i]))
        self.active = next((n for n, p in self.presets.items()
                            if tuple(self.values) == tuple(p)), None)

    def _on_mouse(self, event, x, y, flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            for name, (bx, by, bw, bh) in zip(self.names, self.btn_rects):
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    self.apply_preset(name)
                    return
            for i in range(6):
                sy = SL_Y0 + i * SL_DY
                if SL_X0 - 12 <= x <= SL_X1 + 12 and abs(y - sy) <= 14:
                    self.drag = i
                    self._set_slider(i, x)
                    return
        elif event == cv2.EVENT_MOUSEMOVE and self.drag is not None \
                and (flags & cv2.EVENT_FLAG_LBUTTON):
            self._set_slider(self.drag, x)
        elif event == cv2.EVENT_LBUTTONUP:
            self.drag = None

    # --------------------------------------------------------- static layer
    def _build_static(self):
        t = np.linspace(0, 1, H)[:, None]
        grad = (np.array(BG_TOP) * (1 - t) + np.array(BG_BOT) * t).astype(np.uint8)
        img = np.empty((H, W, 3), np.uint8)
        img[:] = grad[:, None, :]

        # Header
        _text(img, "A.R.C", 24, 46, 1.0, CYAN, 2, FONT_B)
        _text(img, "AUTONOMOUS ROBOTIC CLEANER  |  HITL MISSION CONTROL", 138, 44, 0.45, MUTED)
        cv2.line(img, (20, 62), (W - 20, 62), BORDER, 1, AA)

        # Video frame border
        _rrect(img, VID_X - 2, VID_Y - 2, VID_W + 4, VID_H + 4, BORDER, 6)

        # Target card
        tx, ty, tw, th = TGT
        _card(img, tx, ty, tw, th)
        _text(img, "TARGET POSITION", tx + 16, ty + 26, 0.45, MUTED)
        cv2.rectangle(img, (BAR_X0, BAR_Y0), (BAR_X1, BAR_Y1), (60, 46, 38), -1)
        for pct in (0, 25, 50, 75, 100):
            x = BAR_X0 + int((BAR_X1 - BAR_X0) * pct / 100)
            cv2.line(img, (x, BAR_Y1 + 2), (x, BAR_Y1 + 8), DIM, 1)
            _text(img, f"{pct}", min(max(x, BAR_X0 + 8), BAR_X1 - 8), BAR_Y1 + 26,
                  0.38, DIM, 1, FONT, 'c')

        # Telemetry cards
        cw = (RW - 30) // 4
        for i, lab in enumerate(["VOLTAGE (V)", "CURRENT (mA)", "POWER (mW)", "GAIN"]):
            x = RX + i * (cw + 10)
            _card(img, x, 126, cw, 80)
            _text(img, lab, x + 14, 126 + 24, 0.4, MUTED)

        # Graph card
        _card(img, RX, 220, RW, 110)
        _text(img, "POWER OUTPUT (mW)", RX + 16, 244, 0.45, MUTED)
        gx0, gy0, gx1, gy1 = GRAPH_PLOT
        for gy in (gy0, (gy0 + gy1) // 2, gy1):
            cv2.line(img, (gx0, gy), (gx1, gy), BORDER, 1)

        # Control card
        _card(img, RX, 344, RW, 346)
        _text(img, "COLOR TARGET", RX + 16, 370, 0.45, MUTED)
        _text(img, "DETECTOR MASK", 696, 614, 0.4, MUTED)
        for i, lab in enumerate(SL_LABELS):
            _text(img, lab, 930, SL_Y0 + i * SL_DY + 5, 0.4, MUTED)
        hues = np.linspace(0, 179, SL_X1 - SL_X0).astype(np.uint8)
        hsv = np.zeros((1, hues.size, 3), np.uint8)
        hsv[0, :, 0], hsv[0, :, 1], hsv[0, :, 2] = hues, 200, 230
        rainbow = np.tile(cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR), (6, 1, 1))
        for i in (0, 1):
            y = SL_Y0 + i * SL_DY
            img[y - 3:y + 3, SL_X0:SL_X1] = rainbow

        _text(img, "[1][2][3] presets    [M] mask overlay    [Q] quit    "
                   "drag sliders to tune", 20, 710, 0.4, DIM)
        return img

    # --------------------------------------------------------------- render
    def render(self, frame, mask, contour, telem, status):
        c = self._static.copy()
        self._header(c, status)
        self._video(c, frame, mask, contour, status)
        self._target_bar(c, status)
        self._fsm_and_cards(c, telem)
        self._graph(c, telem)
        self._controls(c, mask, contour)
        return c

    def _badge(self, img, xr, text, dot):
        (tw, _), _ = cv2.getTextSize(text, FONT, 0.45, 1)
        w = tw + 36
        x = xr - w
        _card(img, x, 16, w, 28, CARD, BORDER, 12)
        cv2.circle(img, (x + 15, 30), 4, dot, -1, AA)
        _text(img, text, x + 27, 35, 0.45, TEXT)
        return x - 10

    def _header(self, c, st):
        xr = W - 20
        xr = self._badge(c, xr, "ESP32 LINK" if st.get('serial_ok') else "NO ESP32",
                         GREEN if st.get('serial_ok') else RED)
        tx = st.get('tx_hz', 0)
        if st.get('p_target') is None:
            xr = self._badge(c, xr, "TX IDLE", DIM)   # nothing to send without a target
        else:
            xr = self._badge(c, xr, f"TX {tx:.0f} Hz", GREEN if tx >= 9 else AMBER)
        fps = st.get('cam_fps', 0)
        self._badge(c, xr, f"CAM {fps:.0f} FPS", GREEN if fps >= 15 else AMBER)

    def _video(self, c, frame, mask, contour, st):
        vid = frame if frame.shape[:2] == (VID_H, VID_W) else cv2.resize(frame, (VID_W, VID_H))
        vid = vid.copy()
        mk = mask if mask.shape == (VID_H, VID_W) else cv2.resize(
            mask, (VID_W, VID_H), interpolation=cv2.INTER_NEAREST)

        if self.mask_overlay:
            tint = vid.copy()
            tint[mk > 0] = GREEN
            vid = cv2.addWeighted(tint, 0.45, vid, 0.55, 0)

        for yy in range(0, VID_H, 16):
            cv2.line(vid, (VID_W // 2, yy), (VID_W // 2, yy + 5), (190, 190, 190), 1)

        if contour is not None:
            x, y, w, h = cv2.boundingRect(contour)
            cx, cy = int(x + w / 2), int(y + h / 2)
            cv2.drawContours(vid, [contour], -1, CYAN, 2, AA)
            cv2.line(vid, (cx, 0), (cx, VID_H), CYAN, 1, AA)
            L = max(6, min(24, w // 3, h // 3))
            for px, py, dx, dy in ((x, y, 1, 1), (x + w, y, -1, 1),
                                   (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
                cv2.line(vid, (px, py), (px + dx * L, py), GREEN, 3, AA)
                cv2.line(vid, (px, py), (px, py + dy * L), GREEN, 3, AA)
            cv2.circle(vid, (cx, cy), 8, TEXT, 2, AA)
            cv2.circle(vid, (cx, cy), 3, RED, -1, AA)
            p = st.get('p_target')
            label = f"TARGET {p:.1f}%" if p is not None else "TARGET"
            ly = y - 30 if y > 36 else y + h + 8
            _alpha_rect(vid, x, ly, 140, 24, INK, 0.75)
            _text(vid, label, x + 8, ly + 17, 0.5, GREEN, 1)
        else:
            _alpha_rect(vid, 12, VID_H - 40, 150, 28, INK, 0.75)
            cv2.circle(vid, (28, VID_H - 26), 4, AMBER, -1, AA)
            _text(vid, "SEARCHING...", 40, VID_H - 21, 0.5, AMBER)

        _alpha_rect(vid, 12, 12, 112, 28, INK, 0.7)
        cv2.circle(vid, (28, 26), 5, RED, -1, AA)
        _text(vid, "LIVE 640x480", 40, 31, 0.42, TEXT)
        c[VID_Y:VID_Y + VID_H, VID_X:VID_X + VID_W] = vid

    def _target_bar(self, c, st):
        tx, ty, tw, th = TGT
        p, t_run = st.get('p_target'), st.get('t_run', 0.0)
        if p is None:
            _text(c, "no target", tx + tw - 16, ty + 26, 0.5, DIM, 1, FONT, 'r')
            return
        _text(c, f"{p:5.1f} %    t_run {t_run:.2f} s", tx + tw - 16, ty + 26,
              0.6, TEXT, 1, FONT_B, 'r')
        fw = int((BAR_X1 - BAR_X0) * min(max(p, 0), 100) / 100)
        if fw > 0:
            c[BAR_Y0:BAR_Y1, BAR_X0:BAR_X0 + fw] = self._strip[:, :fw]
        mx = BAR_X0 + fw
        cv2.line(c, (mx, BAR_Y0 - 2), (mx, BAR_Y1 + 2), TEXT, 2, AA)
        tri = np.array([[mx, BAR_Y0 - 4], [mx - 7, BAR_Y0 - 16], [mx + 7, BAR_Y0 - 16]], np.int32)
        cv2.fillPoly(c, [tri], TEXT, AA)

    def _fsm_and_cards(self, c, telem):
        state = telem.get('state', 'IDLE')
        cw = (RW - 32) // 5
        for i, name in enumerate(STATES):
            x = RX + i * (cw + 8)
            if name == state:
                col = STATE_COLORS[name]
                _rrect(c, x, 76, cw, 36, col, 10)
                _text(c, name, x + cw // 2, 99, 0.5, INK, 2, FONT, 'c')
            else:
                _card(c, x, 76, cw, 36, CARD, BORDER, 10)
                _text(c, name, x + cw // 2, 99, 0.45, DIM, 1, FONT, 'c')

        cw = (RW - 30) // 4
        vals = [(f"{telem.get('voltage_v', 0):.2f}", CYAN),
                (f"{telem.get('current_ma', 0):.0f}", AMBER),
                (f"{telem.get('power_mw', 0):.0f}", GREEN),
                (f"{telem.get('gain_pct', 0):.2f}%", PURPLE)]
        for i, (s, col) in enumerate(vals):
            _text(c, s, RX + i * (cw + 10) + 14, 126 + 62, 0.85, col, 1, FONT_B)

    def _graph(self, c, telem):
        self.hist.append(float(telem.get('power_mw', 0)))
        _text(c, f"{telem.get('power_mw', 0):.0f} mW", RX + RW - 16, 244, 0.6, GREEN, 1, FONT_B, 'r')
        n = len(self.hist)
        if n < 2:
            return
        gx0, gy0, gx1, gy1 = GRAPH_PLOT
        arr = np.array(self.hist)
        k = min(9, n)
        arr = np.convolve(np.pad(arr, (k // 2, k - 1 - k // 2), mode='edge'),
                          np.ones(k) / k, mode='valid')
        lo, hi = float(arr.min()), float(arr.max())
        if hi - lo < 50:
            mid = (hi + lo) / 2
            lo, hi = mid - 25, mid + 25
        step = (gx1 - gx0) / (HIST_LEN - 1)
        xs = gx1 - (n - 1 - np.arange(n)) * step
        ys = gy1 - (arr - lo) / (hi - lo) * (gy1 - gy0)
        pts = np.stack([xs, ys], 1).astype(np.int32)

        roi = c[gy0:gy1 + 1, gx0:gx1 + 1].copy()
        poly = np.vstack([pts - [gx0, gy0], [[gx1 - gx0, gy1 - gy0], [int(xs[0]) - gx0, gy1 - gy0]]])
        cv2.fillPoly(roi, [poly.astype(np.int32)], GREEN)
        c[gy0:gy1 + 1, gx0:gx1 + 1] = cv2.addWeighted(
            c[gy0:gy1 + 1, gx0:gx1 + 1], 0.82, roi, 0.18, 0)
        cv2.polylines(c, [pts], False, GREEN, 2, AA)
        _text(c, f"{hi:.0f}", gx0 + 2, gy0 - 4, 0.35, DIM)
        _text(c, f"{lo:.0f}", gx0 + 2, gy1 + 12, 0.35, DIM)

    def _controls(self, c, mask, contour):
        _text(c, "CUSTOM" if self.active is None else "PRESET",
              RX + RW - 16, 370, 0.42, MUTED if self.active is None else CYAN, 1, FONT, 'r')

        for name, (bx, by, bw, bh) in zip(self.names, self.btn_rects):
            on = name == self.active
            _card(c, bx, by, bw, bh, (60, 50, 30) if on else CARD_HI,
                  CYAN if on else BORDER, 10)
            _text(c, name.replace('_', ' ').upper(), bx + bw // 2, by + 20,
                  0.45, CYAN if on else MUTED, 1, FONT, 'c')

        tx, ty, tw, th = THUMB
        small = cv2.resize(mask, (tw, th), interpolation=cv2.INTER_NEAREST)
        thumb = (cv2.cvtColor(small, cv2.COLOR_GRAY2BGR) / 255.0 * np.array(GREEN)).astype(np.uint8)
        c[ty:ty + th, tx:tx + tw] = thumb
        cv2.rectangle(c, (tx - 1, ty - 1), (tx + tw, ty + th), BORDER, 1)

        if contour is not None:
            x, y, w, h = cv2.boundingRect(contour)
            _text(c, f"AREA  {cv2.contourArea(contour):,.0f} px", 696, 646, 0.45, TEXT)
            _text(c, f"BOX   {w} x {h}", 696, 668, 0.45, TEXT)
        else:
            _text(c, "AREA  --", 696, 646, 0.45, DIM)
            _text(c, "BOX   --", 696, 668, 0.45, DIM)

        for i, v in enumerate(self.values):
            y = SL_Y0 + i * SL_DY
            kx = SL_X0 + int(v / SL_MAX[i] * (SL_X1 - SL_X0))
            if i >= 2:
                cv2.line(c, (SL_X0, y), (SL_X1, y), (60, 46, 38), 4, AA)
                cv2.line(c, (SL_X0, y), (kx, y), CYAN, 4, AA)
            r = 10 if self.drag == i else 8
            cv2.circle(c, (kx, y), r, TEXT, -1, AA)
            cv2.circle(c, (kx, y), r, CYAN, 2, AA)
            _text(c, str(v), 1244, y + 5, 0.5, TEXT, 1, FONT, 'r')
