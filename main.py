#!/usr/bin/env python3
"""THE WORLD ON EDGE - Sunday 22 November 2026 in one image.

Pure Python 3 stdlib (zlib + struct only). No network, no randomness, no
time: two runs write byte-identical PNGs. Output: /output/entry.png
(1024x1024, well under 1 MiB).

Design: a dark "crisis desk" front page. One dominant hero - a stylised
map of the Persian Gulf, where the day's biggest story happened (Iran
striking US bases in Kuwait and Bahrain, tankers hit off Oman and in the
Strait of Hormuz) - plus five supporting stories with big numerals and a
live-wire ticker. All seven stories were verified against news sources
published 22 November 2026 (Al Jazeera, BBC, Euronews, France 24, NPR,
SCMP, Times of India, Jagran, ARY).
"""

import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
NAVY = (13, 27, 46)        # page background
PANEL = (18, 38, 63)       # story panels / map land
PANEL2 = (22, 46, 74)      # lighter panel
SEA = (16, 52, 84)         # gulf water
SEA2 = (20, 64, 100)       # gulf water highlight
INK = (242, 239, 230)      # warm off-white text
MUTE = (157, 180, 200)     # blue-grey secondary text
RED = (230, 57, 70)        # signal red
AMBER = (242, 165, 65)     # amber
LINE = (64, 96, 128)       # hairlines
COAST = (214, 226, 236)    # coastline

# ------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 cells, '#' = on. Uppercase + digits + punctuation.
FONT = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    '.': [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ',': [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    ':': [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    ';': [".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."],
    "'": ["..#..", "..#..", "..#..", ".....", ".....", ".....", "....."],
    '-': [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    '/': ["....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."],
    '(': ["...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"],
    ')': ["##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."],
    '&': [".###.", "#...#", "#...#", ".#.#.", "#.#..", "#.#.#", ".##.#"],
    '%': ["##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"],
    '+': [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    '!': ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    '=': [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    '"': [".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."],
}


def text_width(s, scale):
    """Pixel width of s rendered at scale (6 px per char cell, minus 1)."""
    return max(0, len(s) * 6 * scale - scale)


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns list of lines that fit max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def dashed(self, x0, y0, x1, y1, c, dash=7, gap=5):
        n = int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5)
        if n == 0:
            return
        on = True
        left = dash
        px, py = float(x0), float(y0)
        sx, sy = (x1 - x0) / n, (y1 - y0) / n
        for _ in range(n):
            if on:
                self.set(int(px), int(py), c)
            left -= 1
            if left == 0:
                on = not on
                left = dash if on else gap
            px += sx
            py += sy

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - t <= d <= r:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        """Scanline fill of a polygon (list of (x, y))."""
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.set(x, y, c)

    def polyline(self, pts, c):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c)

    def burst(self, cx, cy, r, c, spikes=10):
        """Starburst: radiating spikes + filled core."""
        import math
        for k in range(spikes):
            a = 2 * math.pi * k / spikes
            self.line(cx, cy, int(cx + r * math.cos(a)),
                      int(cy + r * math.sin(a)), c)
            a2 = a + math.pi / spikes
            self.line(cx, cy, int(cx + r * 0.45 * math.cos(a2)),
                      int(cy + r * 0.45 * math.sin(a2)), c)
        self.circle(cx, cy, max(3, r // 3), c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[' '])
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == '#':
                        self.fill_rect(cx + col * scale, y + r * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return cx

    def text_c(self, cx, y, s, scale, c):
        """Centred text."""
        return self.text(cx - text_width(s, scale) // 2, y, s, scale, c)

    def para(self, x, y, s, scale, c, max_w, leading=None):
        """Wrapped paragraph; returns y just below the last line."""
        lh = leading if leading is not None else 9 * scale
        for ln in wrap_text(s, scale, max_w):
            self.text(x, y, ln, scale, c)
            y += lh
        return y


# ------------------------------------------------------------------- png
def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ------------------------------------------------------------------ layout
def tanker(cv, x, y, c):
    """Tiny tanker glyph: hull, bow, bridge stack, mast."""
    cv.fill_rect(x, y, 34, 9, c)
    cv.poly([(x + 34, y), (x + 42, y + 4), (x + 34, y + 9)], c)
    cv.fill_rect(x + 6, y - 9, 7, 9, c)
    cv.line(x + 26, y, x + 26, y - 12, c)
    cv.fill_rect(x + 24, y - 14, 5, 3, c)


def map_label(cv, bx, by, name, sub, burst_xy):
    """Label box with a leader line to a burst point on the map."""
    w = max(text_width(name, 2), text_width(sub, 1)) + 16
    cv.fill_rect(bx, by, w, 36, PANEL2)
    cv.rect(bx, by, w, 36, LINE)
    cv.text(bx + 8, by + 5, name, 2, INK)
    cv.text(bx + 8, by + 23, sub, 1, AMBER)
    cv.line(bx + w // 2, by + 36, burst_xy[0], burst_xy[1], MUTE)


def build(path):
    cv = Canvas(W, H, NAVY)

    # ---- masthead -------------------------------------------------
    cv.fill_rect(0, 0, W, 8, RED)
    cv.text(16, 22, "THE WORLD ON EDGE", 6, INK)
    cv.text(16, 74, "SUNDAY, 22 NOVEMBER 2026", 2, AMBER)
    right = "ONE DAY - ONE PICTURE"
    cv.text(W - 16 - text_width(right, 2), 74, right, 2, MUTE)
    cv.hline(16, 104, W - 32, LINE, 2)

    # ---- hero: gulf map (left) ------------------------------------
    mx, my, mw, mh = 16, 118, 604, 474
    cv.fill_rect(mx, my, mw, mh, PANEL)
    cv.rect(mx, my, mw, mh, LINE)
    sea = [(150, 180), (260, 150), (420, 160), (540, 220), (560, 300),
           (500, 430), (380, 500), (240, 480), (140, 380), (110, 260)]
    cv.poly(sea, SEA)
    cv.poly([(170, 200), (260, 175), (420, 185), (520, 240), (530, 300),
             (480, 410), (380, 470), (260, 450), (170, 370), (140, 270)],
            SEA2)
    cv.polyline(sea, COAST)
    cv.text(468, 178, "IRAN", 2, MUTE)
    cv.text(210, 545, "ARABIA", 2, MUTE)
    cv.text(258, 428, "PERSIAN GULF", 2, MUTE)
    # compass
    cv.text(596, 128, "N", 2, INK)
    cv.line(602, 146, 602, 162, INK)
    cv.poly([(602, 142), (598, 152), (606, 152)], INK)
    # missile arcs from Iran
    cv.dashed(470, 175, 192, 200, RED)
    cv.dashed(470, 175, 300, 330, RED)
    cv.dashed(500, 200, 540, 285, AMBER)
    # tankers on the water
    tanker(cv, 250, 300, AMBER)
    tanker(cv, 400, 405, AMBER)
    # strike bursts
    cv.burst(190, 200, 15, RED)
    cv.burst(300, 330, 15, RED)
    cv.burst(540, 285, 19, RED)
    cv.burst(470, 470, 15, RED)
    cv.ring(190, 200, 22, RED)
    cv.ring(540, 285, 26, RED)
    # labels with leaders
    map_label(cv, 36, 132, "KUWAIT", "U.S. BASE STRUCK", (190, 200))
    map_label(cv, 36, 540, "BAHRAIN", "U.S. ASSETS HIT", (300, 330))
    map_label(cv, 436, 132, "HORMUZ", "TANKER HIT, 1 MISSING", (540, 285))
    map_label(cv, 436, 540, "OMAN", "2 TANKERS HIT", (470, 470))

    # ---- hero: headline (right) ------------------------------------
    hx, hw = 636, 372
    cv.fill_rect(hx, my, hw, mh, PANEL)
    cv.rect(hx, my, hw, mh, LINE)
    cv.text(hx + 20, my + 18, "THE GULF IGNITES", 2, RED)
    y = cv.para(hx + 20, my + 46, "IRAN HITS U.S. BASES ACROSS THE GULF",
                4, INK, hw - 40, leading=38)
    cv.hline(hx + 20, y + 8, hw - 40, RED, 3)
    y = cv.para(hx + 20, y + 26,
                "TEHRAN STRIKES KUWAIT AND BAHRAIN AS TANKERS BURN "
                "OFF OMAN. TRUMP PUSHES FOR A PERMANENT NUCLEAR DEAL.",
                2, INK, hw - 40, leading=18)
    # stat chips (stacked, full width)
    chips = ["2 U.S. BASES HIT", "3 TANKERS ATTACKED", "1 CREW MEMBER MISSING"]
    cy = y + 18
    for c in chips:
        cv.rect(hx + 20, cy, hw - 40, 30, AMBER, 2)
        cv.text(hx + 32, cy + 8, c, 2, AMBER)
        cy += 38
    cv.text(hx + 20, cy + 2, "HOUTHI STRIKES KEEP SAUDI ARABIA ON ALERT.",
            1, MUTE)

    # ---- live wire ticker ------------------------------------------
    ty = 606
    cv.fill_rect(16, ty, W - 32, 56, RED)
    cv.text(32, ty + 7, "LIVE WIRE:  ESTONIA SHUTS ITS RUSSIA BORDER - "
            "HONG KONG VOTES", 2, INK)
    cv.text(32, ty + 31, "MEXICO CARTEL BOSS HELD, 11 DEAD - BOLSONARO IN ICU",
            2, INK)

    # ---- five stories ----------------------------------------------
    stories = [
        ("UKRAINE", "400", RED,
         "DRONES, 110 MISSILES IN THE BIGGEST BARRAGE",
         "LVIV HIT, 2 DEAD, 10 HURT. A MISSILE LANDS IN POLAND."),
        ("SHENZHEN SUMMIT", "3", AMBER,
         "TRUMP, XI AND PUTIN MEET",
         "TRUMP CALLS IT MOMENTOUS. JAPAN CAUGHT IN THE MIDDLE."),
        ("TRADE", "98.5%", AMBER,
         "EU AND INDONESIA END TARIFFS",
         "AFTER 10 YEARS OF TALKS, A DEAL FOR 280 MILLION PEOPLE."),
        ("CLIMATE", "COP31", MUTE,
         "TALKS DEADLOCK OVER FOSSIL FUELS",
         "NO DEAL ON THE FUTURE OF OIL AS THE SUMMIT NEARS ITS END."),
        ("PERU", "6.9", RED,
         "QUAKE SHAKES THE ANDES",
         "MAGNITUDE 6.9. NO CASUALTIES REPORTED AT FIRST."),
    ]
    col_w, gap = 188, 13
    sy = 682
    for i, (kick, stat, col, head, dek) in enumerate(stories):
        x = 16 + i * (col_w + gap)
        cv.fill_rect(x, sy, col_w, 4, col)
        cv.text(x, sy + 14, kick, 2, col)
        cv.text(x, sy + 40, stat, 5, INK)
        y = cv.para(x, sy + 88, head, 2, INK, col_w, leading=18)
        cv.para(x, y + 8, dek, 2, MUTE, col_w, leading=18)

    # ---- closing line ------------------------------------------------
    cv.text_c(W // 2, 924,
              "A DAY OF STRIKES, SUMMITS AND DEADLOCKS - THE WORLD HELD "
              "ITS BREATH.", 2, MUTE)

    # ---- footer ------------------------------------------------------
    cv.hline(16, 962, W - 32, LINE, 2)
    cv.text(16, 978, "SOURCES: AL JAZEERA - BBC - EURONEWS - FRANCE 24 - "
            "NPR - SCMP - TIMES OF INDIA", 2, MUTE)
    cv.text(16, 1000, "EVERY STORY FROM SUNDAY 22 NOVEMBER 2026",
            2, AMBER)
    return write_png(cv, path)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/output/entry.png"
    n = build(out)
    print(f"wrote {out} ({n} bytes)")


if __name__ == "__main__":
    main()
