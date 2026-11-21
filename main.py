#!/usr/bin/env python3
"""THE WORLD TODAY - Saturday 21 November 2026 (Full Day Edition).

A one-page newspaper summary image: 3 lead stories, 12 medium stories,
a world map with numbered pins, a BY THE NUMBERS strip, 33 ALSO TODAY
items and a markets ticker (Friday 20 Nov close - markets closed Saturday).

Pure Python 3.13 standard library only. No network, no external assets,
no clock, no randomness. Deterministic: two runs produce byte-identical
output. Writes one 1024x1024 PNG (entry.png) to $MAKEFUN_OUTPUT_DIR
(default /output).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)
INK = (26, 26, 26)
INK_SOFT = (74, 70, 62)
RED = (163, 30, 34)
BLUE = (31, 78, 121)
SKY = (176, 214, 232)
SEA = (64, 128, 168)
SAND = (226, 208, 170)
GREEN = (86, 130, 74)
DARK_GREEN = (46, 92, 52)
GRAY_LINE = (198, 192, 180)
LIGHT = (238, 233, 221)
WHITE = (255, 255, 255)
GOLD = (201, 162, 39)
ORANGE = (214, 110, 44)
NIGHT = (24, 38, 66)

# ---------------------------------------------------------------- canvas
canvas = bytearray(W * H * 3)
for _i in range(W * H):
    canvas[_i * 3] = PAPER[0]
    canvas[_i * 3 + 1] = PAPER[1]
    canvas[_i * 3 + 2] = PAPER[2]


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        o = (y * W + x) * 3
        canvas[o] = c[0]
        canvas[o + 1] = c[1]
        canvas[o + 2] = c[2]


def rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        o = (yy * W + x0) * 3
        for xx in range(x0, x1):
            canvas[o] = c[0]
            canvas[o + 1] = c[1]
            canvas[o + 2] = c[2]
            o += 3


def hline(x, y, w, c):
    rect(x, y, w, 1, c)


def vline(x, y, h, c):
    rect(x, y, 1, h, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, fill=True):
    if fill:
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            rect(cx - dx, cy + dy, dx * 2 + 1, 1, c)
    else:
        for a in range(360):
            import math
            px(cx + int(r * math.cos(a * 3.14159265 / 180)),
               cy + int(r * math.sin(a * 3.14159265 / 180)), c)


def disc(cx, cy, r, c):
    circle(cx, cy, r, c, fill=True)


def ring(cx, cy, r, c):
    circle(cx, cy, r, c, fill=False)


def triangle(x0, y0, x1, y1, x2, y2, c):
    ys = sorted([y0, y1, y2])
    for yy in range(ys[0], ys[2] + 1):
        xs = []
        for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                 (x2, y2, x0, y0)):
            if ay == by:
                continue
            if min(ay, by) <= yy <= max(ay, by):
                t = (yy - ay) / (by - ay)
                xs.append(ax + t * (bx - ax))
        if len(xs) >= 2:
            a, b = int(min(xs)), int(max(xs))
            rect(a, yy, b - a + 1, 1, c)


def border(x, y, w, h, c, t=1):
    rect(x, y, w, t, c)
    rect(x, y + h - t, w, t, c)
    rect(x, y, t, h, c)
    rect(x + w - t, y, t, h, c)

# ---------------------------------------------------------------- bitmap font
# 5x7 glyphs, '#' = ink. Designed for this page; ASCII only.
GLYPHS = {
'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
}

GLYPHS.update({
'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".###."),
'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
'c': (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".###."),
'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
'f': ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#..."),
'g': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
'i': ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
'j': ("...#.", ".....", "..##.", "...#.", "...#.", "...#.", "...#.", "##..."),
'k': ("#....", "#....", "#.#..", "#.#..", "##...", "#.#..", "#..#."),
'l': (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
'q': (".....", ".....", ".####", "#...#", "#...#", ".###.", "....#"),
'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
't': (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
'u': (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
'y': (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#"),
'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
})
# fix descenders that need an 8th row (g, j, p, q, y use row 7 already)
GLYPHS['g'] = (".....", ".....", ".####", "#...#", "#...#", ".####", "....#")
GLYPHS['j'] = ("...#.", ".....", "..##.", "...#.", "...#.", "...#.", "##...")
GLYPHS['p'] = (".....", ".....", "####.", "#...#", "#...#", "####.", "#....")
GLYPHS['q'] = (".....", ".....", ".####", "#...#", "#...#", ".###.", "....#")
GLYPHS['y'] = (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#")

GLYPHS.update({
'0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
'1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
'2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
'3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
'4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
'5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
'6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
'7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
'8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
'9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
'.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
'!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
'?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
"'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
'"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
'-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
'—': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
'(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
'/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
'%': (".##..", ".##..", "...#.", "..#..", ".#...", "..##.", "..##."),
'$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
'+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
'=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
'*': (".....", ".#.#.", ".###.", "#####", ".###.", ".#.#.", "....."),
'&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
})

# ---------------------------------------------------------------- text
CHAR_W = 6  # 5 px glyph + 1 px gap, at scale 1


def text_w(s, scale=1):
    return len(s) * CHAR_W * scale - scale


def draw_char(x, y, ch, scale, c):
    g = GLYPHS.get(ch)
    if g is None:
        return
    for r in range(7):
        row = g[r]
        for col in range(5):
            if row[col] == '#':
                rect(x + col * scale, y + r * scale, scale, scale, c)


def draw_text(x, y, s, scale=1, c=INK):
    cx = x
    for ch in s:
        draw_char(cx, y, ch, scale, c)
        cx += CHAR_W * scale
    return cx


def draw_text_center(x, y, w, s, scale=1, c=INK):
    tw = text_w(s, scale)
    draw_text(x + (w - tw) // 2, y, s, scale, c)


def wrap(s, max_w, scale=1):
    """Word-wrap s into lines fitting max_w px. Returns list of lines."""
    words = s.split(' ')
    lines = []
    cur = ''
    for wd in words:
        trial = wd if not cur else cur + ' ' + wd
        if text_w(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            # long single word: hard-split by characters
            while text_w(wd, scale) > max_w:
                n = max_w // (CHAR_W * scale)
                lines.append(wd[:n])
                wd = wd[n:]
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(x, y, s, max_w, scale=1, c=INK, lh=None, max_lines=None):
    """Draw wrapped paragraph. Returns y just below last line."""
    if lh is None:
        lh = 7 * scale + 2
    lines = wrap(s, max_w, scale)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        # trim last line with ellipsis if it was cut
        while lines and text_w(lines[-1] + '...', scale) > max_w:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1] + '...'
    for ln in lines:
        draw_text(x, y, ln, scale, c)
        y += lh
    return y

# ---------------------------------------------------------------- scenes
# Every scene draws inside rect (x, y, w, h) using 0..100 relative coords.


def draw_scene(kind, x, y, w, h):
    def X(f):
        return x + int(f * w / 100)
    def Y(f):
        return y + int(f * h / 100)
    def R(fx, fy, fw, fh, c):
        rect(X(fx), Y(fy), max(1, int(fw * w / 100)),
             max(1, int(fh * h / 100)), c)
    def D(fx, fy, fr, c):
        disc(X(fx), Y(fy), max(1, int(fr * min(w, h) / 100)), c)
    def L(fx0, fy0, fx1, fy1, c):
        line(X(fx0), Y(fy0), X(fx1), Y(fy1), c)
    def T(fx0, fy0, fx1, fy1, fx2, fy2, c):
        triangle(X(fx0), Y(fy0), X(fx1), Y(fy1), X(fx2), Y(fy2), c)
    big = w > 120

    if kind == 'cop':
        rect(x, y, w, h, SKY)
        D(82, 18, 10, GOLD)
        R(8, 42, 84, 48, (214, 196, 158))
        R(8, 42, 84, 7, (120, 96, 66))
        for i in range(6):
            R(14 + i * 13, 49, 4, 41, (120, 96, 66))
        R(38, 58, 24, 8, WHITE)
        L(39, 62, 61, 62, RED)
        for i, c in enumerate((BLUE, RED, GREEN, GOLD, (120, 60, 120), ORANGE)):
            R(12 + i * 13, 26, 9, 12, c)
        for i in range(8):
            D(20 + i * 8, 88, 3, (60, 60, 60))
            R(16 + i * 8, 92, 8, 3, (60, 60, 60))
    elif kind == 'france':
        rect(x, y, w, h, SKY)
        R(0, 78, 100, 22, (90, 90, 96))
        for r in range(3):
            for i in range(9):
                D(6 + i * 11 + (r % 2) * 5, 52 + r * 10, 4,
                  ((214, 110, 90), (240, 200, 120), (120, 150, 200),
                   (170, 120, 160))[ (i + r) % 4])
        R(18, 22, 16, 12, WHITE)
        R(60, 18, 16, 12, WHITE)
        L(26, 34, 26, 48, INK)
        L(68, 30, 68, 48, INK)
        for i in range(7):
            R(6 + i * 14, 80, 10, 16, (30, 48, 90))
            D(11 + i * 14, 78, 4, (30, 48, 90))
    elif kind == 'kryvyi':
        rect(x, y, w, h, (168, 168, 160))
        R(10, 30, 26, 62, (120, 110, 100))
        R(42, 42, 22, 50, (140, 128, 116))
        T(10, 30, 20, 18, 30, 30, (120, 110, 100))
        R(14, 38, 6, 6, INK)
        R(24, 38, 6, 6, INK)
        R(14, 52, 6, 6, INK)
        R(46, 50, 6, 6, INK)
        R(54, 50, 6, 6, INK)
        D(30, 16, 7, (200, 200, 196))
        D(38, 10, 9, (210, 210, 206))
        D(24, 8, 6, (200, 200, 196))
        R(66, 76, 28, 12, WHITE)
        R(66, 68, 10, 8, WHITE)
        R(76, 71, 4, 6, RED)
        R(74, 73, 8, 2, RED)
        D(71, 90, 3, INK)
        D(88, 90, 3, INK)
    elif kind == 'nato':
        rect(x, y, w, h, SKY)
        R(0, 82, 100, 18, GREEN)
        R(20, 14, 2, 60, INK)
        R(22, 14, 18, 11, WHITE)
        R(22, 19, 18, 6, RED)
        R(60, 14, 2, 60, INK)
        R(62, 14, 18, 11, BLUE)
        D(71, 19, 2, GOLD)
        T(38, 40, 62, 48, 38, 56, (150, 150, 150))
        R(52, 44, 34, 5, (150, 150, 150))
        T(78, 40, 88, 46, 78, 52, (150, 150, 150))
    elif kind == 'cricket':
        rect(x, y, w, h, GREEN)
        R(38, 8, 24, 84, (196, 164, 110))
        R(47, 8, 3, 12, GOLD)
        R(47, 80, 3, 12, GOLD)
        R(51, 8, 3, 12, GOLD)
        R(51, 80, 3, 12, GOLD)
        R(55, 8, 3, 12, GOLD)
        R(55, 80, 3, 12, GOLD)
        L(30, 70, 44, 46, (222, 190, 140))
        L(32, 72, 46, 48, (222, 190, 140))
        D(70, 55, 4, RED)
        if big:
            R(68, 6, 28, 16, WHITE)
            draw_text(X(70), Y(9), "486/4", 1, INK)
    elif kind == 'cartel':
        rect(x, y, w, h, SKY)
        D(80, 20, 9, GOLD)
        T(0, 62, 25, 22, 50, 62, (150, 110, 70))
        T(35, 62, 62, 16, 90, 62, (120, 88, 56))
        R(0, 62, 100, 38, (222, 196, 140))
        D(50, 76, 10, GOLD)
        D(50, 76, 4, (120, 80, 20))
    elif kind == 'wck':
        rect(x, y, w, h, SKY)
        R(0, 80, 100, 20, (140, 140, 132))
        R(14, 46, 44, 32, WHITE)
        R(58, 56, 18, 22, WHITE)
        R(60, 58, 8, 8, SKY)
        R(22, 52, 20, 12, GREEN)
        D(24, 80, 5, INK)
        D(48, 80, 5, INK)
        D(68, 80, 5, INK)
        R(78, 60, 16, 18, (180, 140, 90))
        R(80, 62, 12, 2, (120, 90, 50))
        R(80, 68, 12, 2, (120, 90, 50))
    elif kind == 'trade':
        rect(x, y, w, h, SKY)
        R(12, 16, 30, 20, BLUE)
        for a in range(8):
            import math
            D(27 + int(9 * math.cos(a * 0.785)), 26 + int(6 * math.sin(a * 0.785)), 1, GOLD)
        R(58, 16, 30, 20, WHITE)
        R(58, 16, 30, 10, RED)
        R(30, 58, 40, 26, WHITE)
        border(X(30), Y(58), max(1, int(40 * w / 100)), max(1, int(26 * h / 100)), INK)
        L(35, 66, 65, 66, INK_SOFT)
        L(35, 73, 60, 73, INK_SOFT)
        L(35, 80, 62, 80, INK_SOFT)
    elif kind == 'robots':
        rect(x, y, w, h, NIGHT)
        for (sx, sy) in ((12, 12), (30, 22), (70, 10), (88, 26), (55, 16), (20, 34)):
            D(sx, sy, 1, WHITE)
        R(28, 58, 44, 30, (120, 120, 130))
        for i in range(5):
            R(32 + i * 8, 64, 4, 24, (80, 80, 90))
        R(38, 44, 24, 10, (60, 60, 70))
        L(44, 44, 30, 30, (200, 200, 200))
        L(56, 44, 70, 30, (200, 200, 200))
        D(30, 30, 3, (200, 200, 200))
        D(70, 30, 3, (200, 200, 200))
        D(44, 52, 3, (200, 200, 200))
        D(56, 52, 3, (200, 200, 200))
    elif kind == 'hormuz':
        rect(x, y, w, int(h * 0.55), SKY)
        D(82, 16, 9, GOLD)
        rect(x, y + int(h * 0.55), w, h - int(h * 0.55), SEA)
        R(8, 52, 34, 10, (40, 40, 44))
        R(30, 42, 10, 10, (40, 40, 44))
        R(14, 40, 4, 12, (200, 60, 40))
        R(58, 58, 34, 10, (52, 52, 56))
        R(80, 48, 10, 10, (52, 52, 56))
        R(64, 46, 4, 12, (200, 60, 40))
        L(4, 72, 20, 72, WHITE)
        L(40, 80, 60, 80, WHITE)
        L(70, 70, 90, 70, WHITE)
    elif kind == 'riyadh':
        rect(x, y, w, h, NIGHT)
        for (sx, sy) in ((10, 14), (26, 8), (44, 18), (66, 10), (84, 20), (94, 8), (36, 30)):
            D(sx, sy, 1, WHITE)
        R(0, 82, 100, 18, (16, 24, 44))
        R(10, 58, 12, 24, (40, 52, 80))
        R(26, 48, 10, 34, (40, 52, 80))
        R(40, 62, 14, 20, (40, 52, 80))
        R(62, 40, 8, 42, (40, 52, 80))
        R(76, 56, 16, 26, (40, 52, 80))
        L(20, 12, 48, 44, (255, 220, 120))
        L(80, 10, 52, 42, (255, 220, 120))
        D(50, 44, 5, ORANGE)
        D(50, 44, 2, (255, 220, 120))
    elif kind == 'basra':
        rect(x, y, w, h, (226, 200, 160))
        D(84, 16, 9, GOLD)
        R(12, 40, 16, 44, (140, 130, 120))
        R(14, 34, 12, 6, (140, 130, 120))
        R(36, 46, 16, 38, (160, 148, 136))
        R(38, 40, 12, 6, (160, 148, 136))
        R(60, 52, 22, 32, (120, 112, 104))
        T(64, 84, 70, 62, 76, 84, ORANGE)
        T(72, 84, 78, 58, 84, 84, (240, 180, 40))
        T(76, 84, 82, 66, 88, 84, ORANGE)
        D(30, 22, 6, (190, 190, 186))
        D(40, 16, 8, (200, 200, 196))
        R(0, 84, 100, 16, (90, 86, 78))
    elif kind == 'budget':
        rect(x, y, w, h, SKY)
        R(8, 30, 34, 54, (190, 180, 150))
        for i in range(4):
            R(12 + i * 8, 38, 4, 46, (120, 110, 88))
        R(52, 62, 8, 22, BLUE)
        R(62, 52, 8, 32, BLUE)
        R(72, 42, 8, 42, BLUE)
        R(82, 32, 8, 52, GOLD)
        D(56, 20, 5, GOLD)
        D(66, 14, 5, GOLD)
        R(0, 84, 100, 16, GREEN)
    elif kind == 'plane':
        rect(x, y, w, h, SKY)
        D(84, 16, 8, GOLD)
        R(20, 44, 56, 10, WHITE)
        T(76, 44, 92, 49, 76, 54, WHITE)
        T(22, 44, 30, 34, 36, 44, WHITE)
        T(46, 54, 58, 70, 64, 54, WHITE)
        R(24, 46, 10, 3, SKY)
        R(40, 46, 10, 3, SKY)
        R(56, 46, 10, 3, SKY)
        R(0, 84, 100, 16, (90, 90, 96))
        T(64, 84, 82, 84, 82, 68, (240, 200, 40))
    elif kind == 'flood':
        rect(x, y, w, h, (150, 160, 170))
        L(12, 10, 20, 30, (220, 225, 230))
        L(30, 6, 38, 26, (220, 225, 230))
        L(70, 12, 78, 32, (220, 225, 230))
        R(8, 52, 22, 20, (190, 150, 110))
        T(6, 52, 19, 38, 32, 52, (140, 60, 50))
        R(58, 48, 26, 24, (170, 140, 110))
        T(56, 48, 71, 34, 86, 48, (140, 60, 50))
        rect(x, y + int(h * 0.66), w, h - int(h * 0.66), SEA)
        L(6, 76, 22, 76, WHITE)
        L(40, 82, 62, 82, WHITE)
        L(70, 74, 92, 74, WHITE)

# ---------------------------------------------------------------- content
# All stories verified Saturday 21 November 2026. Market figures are the
# Friday 20 November close (markets closed Saturday). VIX is 35.89, not 37.
# No final figures are claimed for anything still in progress.

LEADS = [
    dict(kind='cop', kicker='CLIMATE - ANTALYA, TURKEY',
         headline='COP31 IN OVERTIME: EU SAYS GOOD DEAL OR NO DEAL',
         body="Climate talks passed Friday's deadline with no third draft on "
         "the table, though one was promised for Saturday morning. The second "
         "draft dropped all mention of coal, oil and gas and cut the "
         "$120bn-a-year adaptation finance target, while still admitting "
         "warming is set to pass 1.5C. EU climate chief Wopke Hoekstra: "
         "'It's either going to be a good deal or it's going to be no deal.' "
         "Delegates slept in corridors as catering stands were dismantled "
         "around them."),
    dict(kind='france', kicker='FRANCE - PARIS',
         headline='ACTE VI: 70,000 POLICE AS FRANCE MARCHES AGAIN',
         body="France held its sixth cost-of-living protest wave on Saturday, "
         "eight years after the yellow-vest movement began on 17 November "
         "2018. One official Paris march ran at 14:00 from Place de la "
         "Republique to Place de la Nation. Interior Minister Laurent Nunez "
         "deployed about 70,000 police and gendarmes nationwide, with RAID, "
         "BRI and GIGN units on standby. Hundreds of coordinated actions "
         "took place across France and six other European countries."),
    dict(kind='kryvyi', kicker='UKRAINE - KRYVYI RIH',
         headline='RUSSIAN STRIKE ON KRYVYI RIH KILLS BOY, 7, AND PARAMEDIC',
         body="Russia fired 3 ballistic missiles and 148 drones at Ukraine "
         "overnight; air defences downed or suppressed 117 drones. Two "
         "missiles hit central Kryvyi Rih near a restaurant: a 7-year-old "
         "boy and a 20-year-old paramedic were killed, at least 58 to 60 "
         "people wounded, including 6 children. About 25 apartment blocks, "
         "a hospital and an ambulance were damaged. Kyiv was also hit; a "
         "drone wounded 11 in Solonytsivka, Kharkiv."),
]

MEDIUM = [
    dict(kind='nato', headline='RUTTE IN WARSAW: NATO WILL DEFEND EVERY INCH OF POLAND',
         body='Rutte told PM Tusk NATO will defend every inch of Polish territory.'),
    dict(kind='cricket', headline='RAHUL 136 PUTS INDIA 118 AHEAD IN WELLINGTON',
         body="Rahul's 136 took India to 486 for 4 at stumps, a lead of 118 over New Zealand."),
    dict(kind='cartel', headline='MEXICO CAPTURES FBI MOST-WANTED EL CHAPO ISIDRO',
         body='Troops in Sinaloa arrested Fausto Isidro Meza Flores and two other leaders.'),
    dict(kind='wck', headline='ISRAELI STRIKE KILLS 3 IN WCK VEHICLE IN GAZA',
         body='Three Palestinians were killed in a World Central Kitchen aid vehicle.'),
    dict(kind='trade', headline='EU-INDONESIA FREE-TRADE DEAL AFTER 10 YEARS',
         body='The deal opens markets for both sides amid tariff tensions.'),
    dict(kind='robots', headline='UN FAILS TO REGULATE KILLER ROBOTS',
         body="128 states agreed only to 'elaborate' rules on lethal autonomous weapons."),
    dict(kind='hormuz', headline='TWO TANKERS HIT NEAR STRAIT OF HORMUZ',
         body='Two tankers were reported hit near the strait, the UK Maritime Trade Office said.'),
    dict(kind='riyadh', headline='HOUTHI MISSILES AT RIYADH: ALL 3 INTERCEPTED',
         body='The Saudi-led coalition destroyed three Houthi missiles fired at Riyadh.'),
    dict(kind='basra', headline='FIRE AT BASRA POWER PLANT KILLS 4, WOUNDS 30',
         body='At least four were killed and 30 wounded in a fire at the Hartha plant.'),
    dict(kind='budget', headline='EU CHIEF PROPOSES EUR 40BN BUDGET CUT, DIGITAL TAX',
         body='Costa proposed cutting the 2028-2034 budget by EUR 40bn to EUR 1.582 trillion.'),
    dict(kind='plane', headline='AIR NIUGINI EMERGENCY LANDING IN DAVAO: ALL SAFE',
         body='All 137 passengers and 9 crew were evacuated unhurt via emergency slides.'),
    dict(kind='flood', headline='FLORIDA FLOODS: ST. JOHNS RIVER BREAKS 1953 RECORD',
         body='More than 24 inches of rain pushed the St. Johns River above its 1953 record.'),
]

ALSO_TODAY = [
    'Ex-Italian police chief De Gennaro dies at 78',
    'Wildberries chief Kim quits days after EU sanctions',
    'Colturi wins first World Cup ski race for Albania',
    'Man City held 1-1 by Fulham at the Etihad',
    'Alaves beat Deportivo La Coruna 3-1 in LaLiga',
    'Record Rs1.22 lakh crore flows into India stocks',
    'Iraq opens joint security HQ in Jurf al-Sakhar',
    'Nuseirat families unsheltered after Gaza operation',
    'Panama threatens to block weak COP31 deal',
    '25 nations now have fossil-fuel exit roadmaps',
    'Cost-of-living protests spread to 7 European nations',
    'US Democrats test new Senate leadership, plan agenda',
    'Ukraine retakes 14 settlements in northern Kharkiv',
    "Zelensky: Crimea bridge 'will not stand'",
    'Zelensky and Musk clash over Starshield in Ukraine',
    'Swedish Gripen pilots did not fire over Poland',
    'Zelensky calls Putin a murderer; Trump defends ties',
    'Philippines: Romualdez plunder case done in a year',
    "South Korea's Lee: speed is vital in the AI race",
    'Singapore, China finalise 20-plus summit deliverables',
    "Japan's Takaichi leaves Shenzhen without meeting Xi",
    'Kim Jong Un tours factories after apparent Trump snub',
    'Why Kim did not meet Trump - analysis',
    'Rohingya welcome ICJ verdict, but want to go home',
    'Endurance swimmer crosses Hormuz for wildlife cause',
    'US Christian nationalists see GOP losses as opening',
    'Australia backs Cummins unanimously as captain',
    'Harari warns Philippines on dependence on foreign AI',
    'China EV adoption forecast to pass 70%',
    'Swiss tariff-free China deal seen helping Hong Kong',
    'Singaporean extradited on US insider-trading charges',
    'Russia revives pre-war demands in Ukraine talks',
    'COP31 host Turkiye nets $26bn-plus in deals',
]

NUMBERS = [
    ('70,000', 'police and gendarmes deployed across France'),
    ('148', 'drones fired at Ukraine overnight; 117 downed'),
    ('136', 'runs by KL Rahul, his 13th Test century'),
    ('24.26 IN', 'rain near Cocoa Beach, Florida'),
    ('25', 'nations with fossil-fuel exit roadmaps'),
    ('146', 'people safe after Air Niugini landing'),
]

# World map: coarse continent outlines in (lon, lat).
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-80, 73), (-70, 62), (-60, 55), (-55, 47), (-65, 44), (-70, 42),
     (-75, 35), (-80, 32), (-81, 26), (-84, 30), (-90, 29), (-97, 26),
     (-97, 16), (-94, 17), (-90, 14), (-86, 13), (-83, 9), (-80, 8),
     (-79, 9), (-83, 10), (-90, 14), (-95, 16), (-105, 20), (-110, 23),
     (-114, 28), (-120, 34), (-125, 40), (-124, 48), (-130, 55),
     (-140, 60), (-155, 58), (-165, 60), (-168, 66)],
    [(-80, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-70, -52),
     (-68, -55), (-65, -55), (-62, -49), (-58, -38), (-52, -32),
     (-48, -27), (-41, -23), (-35, -9), (-35, -6), (-40, -3), (-44, -2),
     (-50, 0), (-55, 5), (-60, 8), (-70, 11), (-77, 8), (-80, 9)],
    [(-17, 15), (-17, 21), (-15, 27), (-10, 31), (-5, 35), (0, 36),
     (10, 37), (11, 34), (20, 32), (30, 31), (32, 31), (35, 28),
     (37, 22), (39, 18), (43, 12), (48, 11), (51, 12), (44, 5),
     (41, 0), (40, -5), (40, -12), (36, -18), (33, -26), (28, -33),
     (20, -35), (17, -32), (15, -27), (12, -18), (13, -12), (12, -6),
     (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 15)],
    [(-10, 36), (-9, 38), (-9, 43), (-2, 44), (-2, 48), (-5, 48),
     (-1, 50), (2, 51), (4, 53), (8, 55), (8, 57), (10, 59), (5, 60),
     (5, 62), (10, 64), (13, 66), (18, 69), (25, 71), (32, 70),
     (40, 68), (50, 69), (60, 70), (70, 72), (80, 73), (90, 75),
     (100, 77), (110, 74), (120, 73), (130, 72), (140, 72), (150, 70),
     (160, 69), (170, 67), (178, 65), (170, 60), (162, 56), (158, 52),
     (150, 59), (142, 55), (140, 50), (135, 43), (130, 42), (127, 40),
     (122, 38), (120, 32), (122, 28), (118, 25), (110, 20), (108, 12),
     (105, 9), (103, 7), (100, 8), (98, 12), (94, 17), (92, 21),
     (90, 22), (86, 20), (80, 15), (77, 8), (75, 12), (72, 20),
     (68, 23), (62, 25), (57, 26), (54, 27), (50, 29), (48, 30),
     (50, 26), (54, 24), (56, 26), (58, 23), (59, 22), (55, 17),
     (52, 15), (48, 14), (44, 13), (42, 15), (40, 20), (38, 22),
     (35, 28), (34, 31), (30, 36), (27, 37), (23, 36), (22, 37),
     (19, 40), (15, 44), (12, 44), (8, 44), (3, 42), (0, 40),
     (-2, 37), (-6, 36), (-9, 37), (-10, 36)],
    [(114, -22), (114, -30), (115, -35), (118, -35), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (150, -23),
     (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
     (132, -12), (130, -13), (126, -14), (122, -17), (118, -20),
     (114, -22)],
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
     (-3, 50), (-5, 50)],
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 37), (141, 39),
     (141, 41), (143, 42), (145, 44), (143, 44), (141, 42), (139, 38),
     (137, 35), (134, 34), (131, 33), (130, 31)],
    [(167, -45), (170, -43), (173, -41), (175, -38), (177, -38),
     (178, -37), (175, -40), (173, -41), (170, -44), (167, -46),
     (167, -45)],
]

# (number, lon, lat, display lon, display lat, legend label)
PINS = [
    (1, 30.7, 36.9, 30.7, 36.9, 'COP31 - Antalya'),
    (2, 2.35, 48.85, 2.35, 48.85, 'Paris protests'),
    (3, 33.4, 47.9, 33.4, 47.9, 'Kryvyi Rih'),
    (4, 21.0, 52.2, 21.0, 52.2, 'Warsaw - NATO'),
    (5, 174.8, -41.3, 174.8, -41.3, 'Wellington Test'),
    (6, -107.4, 24.8, -107.4, 24.8, 'Sinaloa, Mexico'),
    (7, 34.5, 31.5, 40.0, 27.0, 'Gaza City'),
    (8, 4.35, 50.85, -2.0, 54.5, 'Brussels - EU'),
    (9, 6.1, 46.2, 6.1, 41.0, 'Geneva - UN'),
    (10, 56.5, 26.5, 56.5, 26.5, 'Strait of Hormuz'),
    (11, 46.7, 24.6, 46.7, 24.6, 'Riyadh'),
    (12, 47.8, 30.5, 53.0, 33.0, 'Basra, Iraq'),
    (13, 125.6, 7.1, 125.6, 7.1, 'Davao, Philippines'),
    (14, -81.5, 28.5, -81.5, 28.5, 'Florida floods'),
]

TICKER_1 = 'MARKETS - FRI 20 NOV CLOSE (MARKETS CLOSED SATURDAY)'
TICKER_2 = ('DOW 48,147.33 -1.93% / S&P 500 6,910.39 -3.70% / '
            'NASDAQ 22,617.73 -5.28% / NASDAQ 100 25,028.98 -5.61% / '
            'FTSE 100 10,346.34 -1.02% / DAX 24,802.78 -2.60%')
TICKER_3 = ('NIKKEI 56,436.65 -5.06% / GOLD $3,515.40 -4.62% / '
            'BRENT $92.57 +0.64% / WTI $83.98 +0.93% / '
            'VIX 35.89 +26.20% / US 10-YEAR 4.93%')

# ---------------------------------------------------------------- layout
MX = 16
CW = 322  # lead / also-today column width


def section_head(y, text):
    draw_text(MX, y, text, 1, RED)
    hline(MX, y + 10, W - 2 * MX, GRAY_LINE)
    return y + 16


def build_page():
    # ---- masthead
    draw_text_center(0, 8, W, 'THE WORLD TODAY', 5, INK)
    rect(MX, 50, W - 2 * MX, 2, INK)
    draw_text_center(0, 56, W,
                     'SATURDAY 21 NOVEMBER 2026  —  FULL DAY EDITION  —  '
                     '48 STORIES FROM ONE DAY', 1, INK_SOFT)
    hline(MX, 68, W - 2 * MX, INK)
    hline(MX, 70, W - 2 * MX, INK)

    # ---- leads
    for i, ld in enumerate(LEADS):
        x = MX + i * (CW + 12)
        draw_scene(ld['kind'], x, 78, CW, 104)
        border(x, 78, CW, 104, GRAY_LINE)
        draw_text(x, 188, ld['kicker'], 1, RED)
        y = draw_para(x, 200, ld['headline'], CW, 2, INK, lh=17,
                      max_lines=3)
        max_lines = max(1, (344 - (y + 4)) // 9)
        draw_para(x, y + 4, ld['body'], CW, 1, INK, lh=9,
                  max_lines=max_lines)

    # ---- medium grid
    y = section_head(352, 'MORE FROM SATURDAY')
    pw = 240
    ph = 62
    for idx, md in enumerate(MEDIUM):
        r, c = divmod(idx, 4)
        x = MX + c * (pw + 10)
        yy = y + r * (ph + 7)
        draw_scene(md['kind'], x + 2, yy + 3, 56, 56)
        border(x + 2, yy + 3, 56, 56, GRAY_LINE)
        tx = x + 64
        tw = pw - 68
        y2 = draw_para(tx, yy + 2, md['headline'], tw, 1, INK, lh=9,
                       max_lines=2)
        draw_para(tx, y2 + 1, md['body'], tw, 1, INK_SOFT, lh=9,
                  max_lines=3)

    # ---- world map + pins + legend
    y = section_head(586, 'WHERE IT HAPPENED - 14 PLACES IN THE NEWS')
    map_x, map_y, map_w, map_h = MX, y, 380, 110
    rect(map_x, map_y, map_w, map_h, (232, 240, 244))
    border(map_x, map_y, map_w, map_h, GRAY_LINE)
    lat0, lat1 = 78.0, -58.0

    def proj(lon, lat):
        px_ = map_x + int((lon + 180.0) / 360.0 * map_w)
        py_ = map_y + int((lat0 - lat) / (lat0 - lat1) * map_h)
        return px_, py_

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        # light fill via horizontal scanlines, then outline on top
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for k in range(n):
                ax, ay = pts[k]
                bx, by = pts[(k + 1) % n]
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    t = (yy - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                a, b = int(xs[k]), int(xs[k + 1])
                if b > a:
                    rect(a, yy, b - a, 1, (206, 222, 196))
        for a, b in zip(pts, pts[1:]):
            line(a[0], a[1], b[0], b[1], (110, 140, 120))
    for (num, _lon, _lat, dlon, dlat, _lab) in PINS:
        cx, cy = proj(dlon, dlat)
        disc(cx, cy, 7, RED)
        ring(cx, cy, 7, WHITE)
        s = str(num)
        draw_text(cx - text_w(s, 1) // 2, cy - 3, s, 1, WHITE)
    # legend: 3 columns x 5 rows
    lx = map_x + map_w + 16
    col_w = (W - MX - lx) // 3
    for i, (num, _lon, _lat, _dlon, _dlat, lab) in enumerate(PINS):
        c = i // 5
        r = i % 5
        ex = lx + c * col_w
        ey = map_y + 4 + r * 21
        ns = str(num)
        draw_text(ex, ey, ns, 1, RED)
        draw_text(ex + len(ns) * 6 + 4, ey, lab, 1, INK)
    draw_text(lx, map_y + 4 + 5 * 21 - 8,
              'Pins nudged where places cluster.', 1, INK_SOFT)

    # ---- by the numbers
    y = section_head(724, 'BY THE NUMBERS')
    bw = 158
    for i, (big, lab) in enumerate(NUMBERS):
        x = MX + i * (bw + 8)
        border(x, y, bw, 54, GRAY_LINE)
        draw_text(x + 6, y + 6, big, 2, RED)
        draw_para(x + 6, y + 26, lab, bw - 12, 1, INK, lh=9,
                  max_lines=2)

    # ---- also today
    y = section_head(806, 'ALSO TODAY')
    for i, item in enumerate(ALSO_TODAY):
        c = i // 11
        r = i % 11
        x = MX + c * (CW + 12)
        yy = y + r * 12
        rect(x, yy + 1, 4, 4, RED)
        draw_text(x + 8, yy, item, 1, INK)

    # ---- markets ticker
    hline(MX, 958, W - 2 * MX, INK)
    draw_text(MX, 963, TICKER_1, 1, INK)
    draw_text(MX, 973, TICKER_2, 1, INK)
    draw_text(MX, 983, TICKER_3, 1, INK)

    # ---- footer
    hline(MX, 994, W - 2 * MX, GRAY_LINE)
    draw_text(MX, 999,
              'Sources: Reuters, AP, BBC, The Times, ESPNcricinfo, SCMP, '
              'Al Jazeera, NWS, INA and others.', 1, INK_SOFT)
    draw_text(MX, 1009,
              'All stories verified Saturday 21 November 2026. Market data: '
              'Friday 20 November 2026 close.', 1, INK_SOFT)


# ---------------------------------------------------------------- png
def png_bytes():
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw.extend(canvas[yy * W * 3:(yy + 1) * W * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        return out

    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', comp) + chunk(b'IEND', b''))


def main():
    import hashlib
    build_page()
    data = png_bytes()
    outdir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'entry.png')
    with open(path, 'wb') as f:
        f.write(data)
    print('wrote', path, len(data), 'bytes')
    print('sha256', hashlib.sha256(data).hexdigest())


if __name__ == '__main__':
    main()
