"""VELMARA - a travel poster for a place that isn't there.

A pure-stdlib Python program. It paints a 1024x1024 travel poster
entirely in code - sky gradient, low sun, turquoise sea, stepped
basalt terraces climbing out of the lagoon, and one lone white
watchtower on the highest step - and sets the invented place's name
into the picture with a hand-built stroke font. No PIL, no network,
no downloaded assets: the PNG is encoded here with zlib + struct.

Run:  python3 main.py        ->  writes /output/entry.png
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024
IMG = bytearray(W * H * 3)


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def hspan(y, x0, x1, rgb):
    """Fill one horizontal run of pixels on row y."""
    if y < 0 or y >= H:
        return
    x0 = _clamp(int(x0), 0, W)
    x1 = _clamp(int(x1), 0, W)
    if x1 <= x0:
        return
    row = y * W * 3
    IMG[row + x0 * 3: row + x1 * 3] = bytes(rgb) * (x1 - x0)


def rect(x0, y0, x1, y1, rgb):
    for y in range(int(y0), int(y1)):
        hspan(y, x0, x1, rgb)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(y0, y1, c0, c1):
    """Vertical colour gradient between two rows."""
    for y in range(int(y0), int(y1)):
        t = (y - y0) / max(1, (y1 - y0 - 1))
        hspan(y, 0, W, lerp(c0, c1, t))


def disc(cx, cy, r, rgb):
    r = int(r)
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        hspan(cy + dy, cx - dx, cx + dx + 1, rgb)


def ellipse(cx, cy, rx, ry, rgb):
    for dy in range(-int(ry), int(ry) + 1):
        t = dy / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
        hspan(cy + dy, cx - dx, cx + dx + 1, rgb)


def line(x0, y0, x1, y1, w, rgb):
    """Thick line drawn as a chain of stamped discs."""
    dx = x1 - x0
    dy = y1 - y0
    steps = int(max(abs(dx), abs(dy))) + 1
    r = max(1, int(w) // 2)
    for i in range(steps + 1):
        t = i / steps
        disc(int(round(x0 + dx * t)), int(round(y0 + dy * t)), r, rgb)


def polyline(pts, w, rgb):
    for a, b in zip(pts, pts[1:]):
        line(a[0], a[1], b[0], b[1], w, rgb)


def fill_poly(pts, rgb):
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            hspan(y, int(a), int(b) + 1, rgb)


def _chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(path, w, h, img):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += img[y * w * 3:(y + 1) * w * 3]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


# ---------------------------------------------------------------------------
# Stroke font. Every glyph is a list of strokes; every stroke is a list of
# points on a 5-wide by 7-tall grid (x 0..4, y 0..6, y grows downwards).
# Drawn as thick polylines, so the letters read as hand-set poster type.
# ---------------------------------------------------------------------------

FONT = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(1, 4), (3, 4)]],
    "B": [[(0, 0), (0, 6)],
          [(0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)],
          [(0, 3), (3, 3), (4, 4), (4, 5), (3, 6), (0, 6)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6)],
          [(0, 0), (3, 0), (4, 1), (4, 5), (3, 6), (0, 6)]],
    "E": [[(0, 0), (0, 6)], [(0, 0), (4, 0)],
          [(0, 3), (3, 3)], [(0, 6), (4, 6)]],
    "F": [[(0, 0), (0, 6)], [(0, 0), (4, 0)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6),
           (3, 6), (4, 5), (4, 3), (2, 3)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(2, 0), (2, 6)], [(0, 0), (4, 0)], [(0, 6), (4, 6)]],
    "J": [[(1, 0), (4, 0)], [(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3), (4, 6)]],
    "L": [[(0, 0), (0, 6)], [(0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2, 3), (4, 0), (4, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
}

# The rest of the alphabet, digits and punctuation (same 5x7 grid).
FONT.update({
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6),
           (0, 5), (0, 1), (1, 0)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "Q": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6),
           (0, 5), (0, 1), (1, 0)], [(3, 4), (4, 6)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)],
          [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3),
           (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1, 6), (2, 3), (3, 6), (4, 0)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    "0": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6),
           (0, 5), (0, 1), (1, 0)]],
    "1": [[(1, 1), (2, 0), (2, 6)], [(0, 6), (4, 6)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 3), (0, 6), (4, 6)]],
    "3": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3)],
          [(3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "4": [[(0, 0), (0, 3), (4, 3)], [(3, 0), (3, 6)]],
    "5": [[(4, 0), (0, 0), (0, 3), (3, 3), (4, 4), (4, 5),
           (3, 6), (1, 6), (0, 5)]],
    "6": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6),
           (3, 6), (4, 5), (4, 3), (1, 3)]],
    "7": [[(0, 0), (4, 0), (2, 6)]],
    "8": [[(1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3),
           (0, 2), (0, 1), (1, 0)],
          [(1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6),
           (0, 5), (0, 4), (1, 3)]],
    "9": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6),
           (0, 5), (0, 2), (1, 0)], [(0, 3), (4, 3)]],
    " ": [],
    "'": [[(2, 0), (2, 1)]],
    "-": [[(0, 3), (4, 3)]],
    ".": [[(2, 5), (2, 6)]],
})


def text_width(s, height, spacing):
    scale = height / 7.0
    return len(s) * (5 * scale + spacing) - spacing


def draw_text(s, cx, y_top, height, rgb, spacing=None):
    """Draw centred text with the stroke font."""
    scale = height / 7.0
    if spacing is None:
        spacing = max(2, int(height * 0.12))
    w = text_width(s, height, spacing)
    x = cx - w / 2.0
    sw = max(2, int(round(height * 0.13)))
    for ch in s:
        for stroke in FONT.get(ch.upper(), []):
            pts = [(x + gx * scale, y_top + gy * scale) for gx, gy in stroke]
            polyline(pts, sw, rgb)
        x += 5 * scale + spacing


# ---------------------------------------------------------------------------
# The poster. Palette: indigo dusk sky melting into coral and gold,
# turquoise lagoon, dark basalt steps, one white watchtower.
# Composition: name at the top, sun and tower on the right, the eye
# travels name -> tower -> sun -> horizon.
# ---------------------------------------------------------------------------

CREAM = (255, 244, 214)
DARK = (14, 22, 44)
GOLD = (252, 196, 110)


def draw_poster():
    # Sky: indigo -> steel blue -> mauve -> coral -> gold horizon.
    vgrad(0, 180, (14, 34, 64), (44, 78, 110))
    vgrad(180, 380, (44, 78, 110), (150, 96, 96))
    vgrad(380, 500, (150, 96, 96), (228, 138, 84))
    vgrad(500, 600, (228, 138, 84), GOLD)

    # Long warm clouds, soft flat ellipses in the sunset.
    ellipse(180, 340, 150, 16, (255, 196, 150))
    ellipse(240, 356, 110, 12, (250, 178, 132))
    ellipse(840, 300, 170, 18, (250, 170, 120))
    ellipse(780, 316, 120, 12, (244, 158, 112))
    ellipse(430, 420, 120, 12, (255, 200, 150))

    # Low sun with a halo, hanging over the lagoon.
    disc(700, 500, 128, (240, 150, 95))
    disc(700, 500, 92, (250, 182, 112))
    disc(700, 500, 56, (255, 226, 158))

    # Gulls, five small dark marks in the open sky.
    for gx, gy in [(300, 300), (340, 278), (382, 322), (760, 210), (802, 242)]:
        polyline([(gx - 9, gy + 4), (gx, gy), (gx + 9, gy + 4)], 3, (28, 30, 46))

    # Sea: turquoise at the horizon, deepening all the way down so the
    # terraces rise out of the lagoon instead of out of a black void.
    vgrad(600, 680, (38, 158, 168), (24, 138, 152))
    vgrad(680, 1024, (24, 138, 152), (8, 70, 92))
    rect(0, 598, W, 601, (255, 222, 150))

    # Sunlight shimmering on the water under the sun.
    for y, x0, x1 in [(612, 648, 752), (628, 656, 744), (646, 668, 736),
                      (664, 676, 728), (684, 684, 720), (706, 690, 714)]:
        rect(x0, y, x1, y + 5, (255, 214, 140))

    # Stepped basalt terraces climbing out of the lagoon, left to right.
    steps = [(0, 205, 960), (205, 410, 908), (410, 615, 856),
             (615, 820, 804), (820, 1024, 752)]
    for x0, x1, top in steps:
        rect(x0, top, x1, H, (46, 54, 74))
        rect(x0, top, x1, top + 20, (98, 106, 130))
        rect(x0, top, x1, top + 3, GOLD)

    # The watchtower on the highest step: white, one warm window,
    # a coral flag catching the last light.
    fill_poly([(850, 752), (858, 592), (860, 556),
               (920, 556), (922, 592), (930, 752)], (244, 238, 222))
    fill_poly([(902, 752), (906, 592), (920, 556), (922, 592), (930, 752)],
              (212, 204, 186))
    rect(860, 540, 874, 556, (244, 238, 222))
    rect(883, 540, 897, 556, (244, 238, 222))
    rect(906, 540, 920, 556, (244, 238, 222))
    rect(884, 640, 896, 668, (255, 190, 90))
    disc(890, 640, 6, (255, 190, 90))
    rect(882, 712, 898, 752, (40, 44, 58))
    line(890, 498, 890, 556, 3, (40, 44, 58))
    fill_poly([(890, 498), (932, 511), (890, 524)], (232, 96, 72))

    # The name, large, set into the sky with a soft dark offset.
    draw_text("VELMARA", 518, 96, 128, DARK, 10)
    draw_text("VELMARA", 512, 88, 128, CREAM, 10)
    # One short tagline under the name.
    draw_text("WHERE THE SEA CLIMBS THE STAIRS", 512, 238, 30,
              (255, 226, 170), 3)

    # Thin cream frame, the poster's edge.
    rect(26, 26, 998, 31, CREAM)
    rect(26, 993, 998, 998, CREAM)
    rect(26, 26, 31, 998, CREAM)
    rect(993, 26, 998, 998, CREAM)


def main():
    draw_poster()
    # Never remove /output: the grader mounts it. Just create and write.
    os.makedirs("/output", exist_ok=True)
    write_png("/output/entry.png", W, H, IMG)
    print("wrote /output/entry.png")


if __name__ == "__main__":
    main()
