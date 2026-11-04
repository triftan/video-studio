"""83 video effects implemented with OpenCV/NumPy on top of face/hand/pose/segmentation data.

Effects are tuned for a working frame whose short side is about 720 px; apply_effects.py resizes for you.

Every effect is fx(img, c) -> img, where img is a BGR uint8 frame and c is a Ctx with:
  c.t (seconds into the effect), c.p (0..1 progress), c.k (frame index in segment), c.g (global source frame),
  c.face (478x2 px), c.fmat (4x4 head pose), c.hands (list of 21x2 px), c.pose (33x3 px+vis),
  c.cat (HxW category mask: 0 bg, 1 hair, 2 body skin, 3 face skin, 4 clothes, 5 other), c.person (HxW float 0..1)
"""
import math
import os
import sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PLUGIN_ROOT = Path(__file__).resolve().parents[3]

# Fonts: first existing candidate wins (macOS, Windows, Linux). Stickers fall back to Pillow's default font.
_CJK_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc", "/Library/Fonts/Arial Unicode.ttf",
    "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
]
_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _first(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


FONT_BOLD = os.environ.get("VS_FONT_BOLD") or _first(_BOLD_CANDIDATES)
FONT_CJK = os.environ.get("VS_FONT_CJK") or _first(_CJK_CANDIDATES) or FONT_BOLD
_fonts = {}


def font(path, size):
    key = (path, size)
    if key not in _fonts:
        try:
            _fonts[key] = ImageFont.truetype(path, size) if path else ImageFont.load_default(size)
        except (OSError, TypeError):
            _fonts[key] = ImageFont.load_default()
    return _fonts[key]


# ---------------------------------------------------------------- helpers
def clamp8(a):
    return np.clip(a, 0, 255).astype(np.uint8)


def lum(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def checker(h, w, s=24):
    y, x = np.mgrid[0:h, 0:w]
    m = ((x // s + y // s) % 2).astype(np.uint8)
    return np.dstack([np.where(m, 205, 160)] * 3).astype(np.uint8)


def over(bg, fg, a):
    a = a[..., None] if a.ndim == 2 else a
    return clamp8(bg * (1 - a) + fg * a)


def screen(a, b):
    return clamp8(255 - (255 - a.astype(np.float32)) * (255 - b.astype(np.float32)) / 255)


def add_glow(img, layer, blur=21, gain=1.0):
    g = cv2.GaussianBlur(layer, (0, 0), blur)
    return clamp8(img.astype(np.float32) + (g.astype(np.float32) + layer.astype(np.float32)) * gain)


def pil_layer(h, w):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def comp_pil(img, layer):
    a = np.asarray(layer).astype(np.float32) / 255
    rgb = a[..., :3][..., ::-1] * 255
    return over(img, rgb, a[..., 3])


class Face:
    def __init__(self, pts, fmat):
        self.p = pts
        self.fmat = fmat

    def pt(self, i):
        return self.p[i]

    @property
    def l_eye(self):
        return self.p[468]

    @property
    def r_eye(self):
        return self.p[473]

    @property
    def mouth(self):
        return (self.p[13] + self.p[14]) / 2

    @property
    def nose(self):
        return self.p[1]

    @property
    def top(self):
        return self.p[10]

    @property
    def chin(self):
        return self.p[152]

    @property
    def width(self):
        return float(np.linalg.norm(self.p[234] - self.p[454]))

    @property
    def height(self):
        return float(np.linalg.norm(self.p[10] - self.p[152]))

    @property
    def center(self):
        return (self.p[10] + self.p[152]) / 2

    @property
    def roll(self):  # degrees, eye line angle
        d = self.r_eye - self.l_eye
        return math.degrees(math.atan2(d[1], d[0]))

    @property
    def up(self):  # unit vector from chin to forehead
        v = self.top - self.chin
        return v / (np.linalg.norm(v) + 1e-6)

    @property
    def yaw(self):  # -1..1 rough, from nose offset relative to face sides
        a, b = self.p[234], self.p[454]
        return float(((self.nose[0] - a[0]) / max(1, b[0] - a[0]) - 0.5) * 2)

    OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149,
            150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]

    def oval(self):
        return self.p[self.OVAL].astype(np.int32)


class Warp:
    """Accumulates smooth local displacement (bulges, stretches) and applies them with one remap."""

    def __init__(self, h, w):
        self.h, self.w = h, w
        self.gy, self.gx = np.mgrid[0:h, 0:w].astype(np.float32)
        self.mx, self.my = self.gx.copy(), self.gy.copy()

    def bulge(self, c, r, s, sx=1.0, sy=1.0):
        """s>0 magnifies the disc (c, r), s<0 pinches. sx/sy scale strength per axis."""
        x0, x1 = int(max(0, c[0] - r)), int(min(self.w, c[0] + r))
        y0, y1 = int(max(0, c[1] - r)), int(min(self.h, c[1] + r))
        if x1 <= x0 or y1 <= y0:
            return self
        gx, gy = self.gx[y0:y1, x0:x1], self.gy[y0:y1, x0:x1]
        dx, dy = gx - c[0], gy - c[1]
        d = np.sqrt(dx * dx + dy * dy) / r
        f = np.where(d < 1, (1 - d * d) ** 2, 0)
        self.mx[y0:y1, x0:x1] -= dx * s * sx * f
        self.my[y0:y1, x0:x1] -= dy * s * sy * f
        return self

    def shift(self, c, r, v):
        """Move content near c by vector v (smooth falloff)."""
        x0, x1 = int(max(0, c[0] - r)), int(min(self.w, c[0] + r))
        y0, y1 = int(max(0, c[1] - r)), int(min(self.h, c[1] + r))
        gx, gy = self.gx[y0:y1, x0:x1], self.gy[y0:y1, x0:x1]
        d = np.sqrt((gx - c[0]) ** 2 + (gy - c[1]) ** 2) / r
        f = np.where(d < 1, (1 - d * d) ** 2, 0)
        self.mx[y0:y1, x0:x1] -= v[0] * f
        self.my[y0:y1, x0:x1] -= v[1] * f
        return self

    def apply(self, img):
        return cv2.remap(img, self.mx, self.my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def affine(img, angle=0, scale=1.0, tx=0, ty=0, center=None):
    h, w = img.shape[:2]
    c = center if center is not None else (w / 2, h / 2)
    M = cv2.getRotationMatrix2D((float(c[0]), float(c[1])), angle, scale)
    M[0, 2] += tx
    M[1, 2] += ty
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)


FRAME_W, FRAME_H = 720, 1280   # set by the caller to the working frame size
SAFE_TOP = 40                   # raise this when something (a label, a title) covers the top of the frame


def safe(pt, margin=0):
    """Clamp a point so stickers stay inside the frame (and below SAFE_TOP)."""
    return np.array([min(max(pt[0], 40 + margin), FRAME_W - 40 - margin), max(pt[1], SAFE_TOP + margin)], np.float32)


def fbm(t, seed, octaves=3):
    v, a, f = 0.0, 1.0, 1.0
    for o in range(octaves):
        v += a * math.sin(t * f * 2.1 + seed * 7.3 + o * 1.7) * math.cos(t * f * 1.3 + seed * 3.1)
        a *= 0.5
        f *= 2.0
    return v


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def pop(t, start=0.0, dur=0.25):
    x = min(1, max(0, (t - start) / dur))
    return 1 + 0.25 * math.sin(math.pi * x) if x < 1 else 1.0 if x >= 1 else 0


def draw_text_outlined(d, xy, text, size, fill, stroke, sw, path=FONT_CJK, anchor="mm"):
    d.text(tuple(map(float, xy)), text, font=font(path, size), fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


def question_mark(d, xy, size, fill, rot=0, path=FONT_BOLD):
    im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.text((size, size), "?", font=font(path, size), fill=fill, stroke_width=max(2, size // 12), stroke_fill=(30, 20, 0, 255), anchor="mm")
    im = im.rotate(rot, resample=Image.BICUBIC)
    return im


def sticker_text(text, size, fill, stroke, sw, rot=0, path=FONT_CJK):
    f = font(path, size)
    bbox = f.getbbox(text, stroke_width=sw)
    w, h = bbox[2] - bbox[0] + 20, bbox[3] - bbox[1] + 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((w / 2, h / 2), text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor="mm")
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def put(layer, im, center):
    x, y = int(center[0] - im.width / 2), int(center[1] - im.height / 2)
    layer.paste(im, (x, y), im)


def tear(d, x, y, r, fill=(70, 160, 255, 255), outline=(20, 60, 140, 255)):
    d.polygon([(x, y - r * 1.8), (x - r, y), (x + r, y)], fill=fill)
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=2)
    d.ellipse([x - r * 0.45, y - r * 0.5, x - r * 0.1, y - r * 0.1], fill=(255, 255, 255, 200))


def star(d, cx, cy, r, fill, rot=0):
    pts = []
    for i in range(10):
        a = math.radians(rot + i * 36 - 90)
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=fill)


def lightning(rng, a, b, jag=18, depth=5):
    pts = [np.array(a, float), np.array(b, float)]
    for _ in range(depth):
        new = [pts[0]]
        for p, q in zip(pts[:-1], pts[1:]):
            m = (p + q) / 2
            n = np.array([-(q - p)[1], (q - p)[0]])
            n = n / (np.linalg.norm(n) + 1e-6)
            new += [m + n * rng.uniform(-jag, jag), q]
        pts = new
        jag *= 0.55
    return np.array(pts, np.int32)


def load_cube(path):
    size, rows = None, []
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if s.startswith("LUT_3D_SIZE"):
            size = int(s.split()[1])
        elif s and (s[0].isdigit() or s[0] in "-.") and len(s.split()) == 3:
            rows.append([float(v) for v in s.split()])
    lut = np.array(rows, np.float32).reshape(size, size, size, 3)  # [b][g][r] -> rgb
    return lut


def apply_lut(img, lut):
    n = lut.shape[0]
    rgb = img[..., ::-1].astype(np.float32) / 255 * (n - 1)
    i = np.clip(np.round(rgb).astype(np.int32), 0, n - 1)
    out = lut[i[..., 2], i[..., 1], i[..., 0]]
    return clamp8(out[..., ::-1] * 255)


def log_flatten(img):
    """Approximate how log footage looks: lifted blacks, low contrast, low saturation."""
    f = img.astype(np.float32) / 255
    f = 0.12 + 0.68 * np.power(f, 0.6)
    g = f.mean(axis=2, keepdims=True)
    f = g + (f - g) * 0.55
    return clamp8(f * 255)


def split_view(a, b, x, label_a, label_b):
    out = a.copy()
    out[:, x:] = b[:, x:]
    cv2.line(out, (x, 0), (x, out.shape[0]), (255, 255, 255), 3)
    for txt, px in ((label_a, x - 14), (label_b, x + 14)):
        size = cv2.getTextSize(txt, cv2.FONT_HERSHEY_DUPLEX, 0.8, 2)[0]
        xx = px - size[0] if px < x else px
        ty = int(out.shape[0] * 0.45)
        cv2.putText(out, txt, (xx, ty), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 0), 5, cv2.LINE_AA)
        cv2.putText(out, txt, (xx, ty), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    return out


ASCII = np.array(list("01アイウエオカキクケコｱｲｳ@#$%&*+=<>"))


# ---------------------------------------------------------------- effects
def fx_portrait_matte(img, c):
    h, w = img.shape[:2]
    bg = checker(h, w)
    a = cv2.GaussianBlur(c.person, (0, 0), 1.5)
    out = over(bg, img, a)
    edge = cv2.Canny((a * 255).astype(np.uint8), 60, 160)
    out[edge > 0] = (255, 255, 255)
    return out


def fx_smart_object(img, c):
    obj = (c.cat == 4).astype(np.float32)
    obj = cv2.GaussianBlur(obj, (0, 0), 2)
    dim = clamp8(cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) * 0.35)
    out = over(dim, img, obj)
    cnts, _ = cv2.findContours((obj > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, cnts, -1, (255, 200, 60), 3, cv2.LINE_AA)
    ys, xs = np.nonzero(obj > 0.5)
    if len(xs):
        cx, cy = int(xs.mean()), int(ys.mean())
        cv2.circle(out, (cx, cy), 14, (255, 200, 60), -1, cv2.LINE_AA)
        cv2.circle(out, (cx, cy), 22, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(out, "tracking: shirt", (cx + 30, cy + 8), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    return out


def fx_ape_face(img, c):
    f = c.face
    W = Warp(*img.shape[:2])
    W.bulge(f.l_eye, f.width * 0.22, 0.55).bulge(f.r_eye, f.width * 0.22, 0.55)
    muzzle = f.nose * 0.4 + f.mouth * 0.6
    W.bulge(muzzle, f.width * 0.62, 0.42, sx=1.35, sy=0.8)
    W.bulge(f.nose, f.width * 0.22, 0.5, sx=1.4, sy=0.6)
    out = W.apply(img)
    # darker, furrier tint inside the face
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.fillPoly(mask, [f.oval()], 255)
    mask = cv2.GaussianBlur(mask, (0, 0), 12).astype(np.float32) / 255 * 0.35
    tint = clamp8(out * np.array([0.55, 0.7, 0.85]))
    return over(out, tint, mask)


def fx_ascii_rain(img, c):
    h, w = img.shape[:2]
    cell = 20
    small = cv2.resize(lum(img), (w // cell, h // cell), interpolation=cv2.INTER_AREA)
    out = (img * 0.45).astype(np.uint8)
    layer = np.zeros_like(img)
    rng = np.random.default_rng(7)
    speeds = rng.uniform(6, 16, small.shape[1])
    offs = rng.uniform(0, small.shape[0], small.shape[1])
    for cy in range(small.shape[0]):
        for cx in range(small.shape[1]):
            b = small[cy, cx] / 255
            if b > 0.35 and (cx * 31 + cy * 17 + int(c.t * 8)) % 3 == 0:
                cv2.putText(layer, "01"[(cx + cy + int(c.t * 10)) % 2], (cx * cell + 2, cy * cell + cell - 3), cv2.FONT_HERSHEY_PLAIN, 1.35, (int(120 * b), int(60 * b), 0), 1, cv2.LINE_AA)
    for cx in range(small.shape[1]):
        head = (offs[cx] + c.t * speeds[cx] * 3) % (small.shape[0] + 12)
        for cy in range(small.shape[0]):
            trail = head - cy
            if trail < 0 or trail > 22:
                continue
            b = small[cy, cx] / 255
            if b < 0.15:
                continue
            ch = ASCII[(cx * 7 + cy * 13 + int(c.t * 12)) % len(ASCII)]
            ch = ch if ch.isascii() else "1"
            inten = (1 - trail / 22) * (0.5 + b)
            col = (255, int(160 + 95 * (trail < 1)), int(60 + 195 * (trail < 1)))
            cv2.putText(layer, ch, (cx * cell + 2, cy * cell + cell - 3), cv2.FONT_HERSHEY_PLAIN, 1.35,
                        tuple(int(v * min(1, inten)) for v in col), 1, cv2.LINE_AA)
    return add_glow(out, layer, 5, 1.4)


def fx_awkward(img, c):
    f = c.face
    W = Warp(*img.shape[:2])
    W.bulge(f.top * 0.7 + f.center * 0.3, f.width * 0.55, -0.35, sx=1.3, sy=0.3)   # narrow forehead
    W.bulge(f.chin * 0.6 + f.center * 0.4, f.width * 0.7, 0.35, sx=1.4, sy=0.4)      # wide jaw (pear)
    W.bulge(f.mouth, f.width * 0.35, 0.6, sx=1.6, sy=-0.3)                           # stretched mouth
    W.bulge(f.l_eye, f.width * 0.18, 0.4, sx=0.3, sy=1.4).bulge(f.r_eye, f.width * 0.18, 0.4, sx=0.3, sy=1.4)
    out = W.apply(img)
    layer, d = pil_layer(*img.shape[:2])
    side = f.p[454] + np.array([10, -f.height * 0.25])
    for i in range(3):
        y = (c.t * 60 + i * 25) % 70
        tear(d, side[0] + i * 14, side[1] + y, 7 + i)
    return comp_pil(out, layer)


def fx_big_head(img, c):
    f = c.face
    amt = 0.55 * ease(c.p * 3)
    return Warp(*img.shape[:2]).bulge(f.center, f.height * 1.25, amt).apply(img)


def fx_big_mouth(img, c):
    f = c.face
    W = Warp(*img.shape[:2])
    W.bulge(f.mouth, f.width * 0.55, 0.7, sx=1.2, sy=1.0)
    W.bulge(f.l_eye, f.width * 0.2, 0.6).bulge(f.r_eye, f.width * 0.2, 0.6)
    return W.apply(img)


def fx_brain_confusion(img, c):
    f = c.face
    layer, d = pil_layer(*img.shape[:2])
    rw, rh = f.width * 0.55, f.height * 0.33
    cx, cy = safe(f.p[454] + np.array([f.width * 0.45, -f.height * 0.55]), int(rw))
    for i in range(14):
        a = i / 14 * math.tau
        r = 0.16 * rw
        d.ellipse([cx + math.cos(a) * rw * 0.8 - r, cy + math.sin(a) * rh * 0.8 - r, cx + math.cos(a) * rw * 0.8 + r, cy + math.sin(a) * rh * 0.8 + r], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=4)
    d.ellipse([cx - rw * 0.85, cy - rh * 0.85, cx + rw * 0.85, cy + rh * 0.85], fill=(255, 255, 255, 255))
    for k, s in enumerate([0.12, 0.07]):
        bx, by = (f.top * (0.4 + k * 0.3) + np.array([cx, cy]) * (0.6 - k * 0.3))
        d.ellipse([bx - f.width * s / 2, by - f.width * s / 2, bx + f.width * s / 2, by + f.width * s / 2], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=3)
    rng = np.random.default_rng(int(c.t * 6))
    pts = [(cx + rng.uniform(-rw, rw) * 0.6, cy + rng.uniform(-rh, rh) * 0.55) for _ in range(16)]
    d.line(pts, fill=(30, 30, 30, 255), width=4, joint="curve")
    return comp_pil(img, layer)


def fx_canon_log(img, c):
    flat = log_flatten(img)
    graded = clamp8((img.astype(np.float32) - 128) * 1.08 + 128)
    x = int(img.shape[1] * (0.25 + 0.5 * ease(c.p * 1.4)))
    return split_view(flat, graded, x, "Canon Log 3", "709")


def fx_circle_mask(img, c):
    h, w = img.shape[:2]
    f = c.face
    r = f.height * (0.85 + 0.15 * math.sin(c.t * 3))
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt((x - f.center[0]) ** 2 + (y - f.center[1]) ** 2)
    a = np.clip((r - d) / 40 + 0.5, 0, 1)
    return over(checker(h, w), img, a)


def fx_color_wheels(img, c):
    f = img.astype(np.float32) / 255
    l = f.mean(axis=2, keepdims=True)
    shadows = (1 - l) ** 2
    highs = l ** 2
    lift = np.array([0.10, 0.04, -0.04])   # BGR: teal shadows
    gain = np.array([-0.06, 0.03, 0.10])   # warm highlights
    k = ease(c.p * 2)
    f = f + k * (shadows * lift + highs * gain)
    return clamp8(f * 255)


def fx_cool_red_eye(img, c):
    f = c.face
    e = f.r_eye
    layer = np.zeros_like(img)
    L = int(img.shape[1] * 1.2)
    ang = math.radians(f.roll)
    d = np.array([math.cos(ang), math.sin(ang)])
    p1, p2 = (e - d * L).astype(int), (e + d * L).astype(int)
    cv2.line(layer, tuple(p1), tuple(p2), (40, 40, 255), 6, cv2.LINE_AA)
    cv2.line(layer, tuple(p1), tuple(p2), (180, 180, 255), 2, cv2.LINE_AA)
    pulse = 0.8 + 0.2 * math.sin(c.t * 10)
    cv2.circle(layer, tuple(e.astype(int)), int(f.width * 0.07 * pulse), (220, 220, 255), -1, cv2.LINE_AA)
    cv2.circle(layer, tuple(e.astype(int)), int(f.width * 0.13 * pulse), (30, 30, 230), 3, cv2.LINE_AA)
    return add_glow(img, layer, 9, 0.9)


def fx_crt(img, c):
    h, w = img.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = x / w * 2 - 1, y / h * 2 - 1
    r2 = nx * nx + ny * ny
    k = 0.12
    mx = ((nx * (1 + k * r2)) + 1) / 2 * w
    my = ((ny * (1 + k * r2)) + 1) / 2 * h
    b, g, r = cv2.split(img)
    r = cv2.remap(r, mx + 3, my, cv2.INTER_LINEAR, borderValue=0)
    g = cv2.remap(g, mx, my, cv2.INTER_LINEAR, borderValue=0)
    b = cv2.remap(b, mx - 3, my, cv2.INTER_LINEAR, borderValue=0)
    out = cv2.merge([b, g, r]).astype(np.float32)
    out *= np.where((y.astype(int) // 2) % 2 == 0, 1.0, 0.7)[..., None]
    out += np.random.default_rng(c.k).normal(0, 9, out.shape[:2])[..., None]
    vig = np.clip(1.25 - r2 * 0.55, 0, 1)[..., None]
    out *= vig
    out[(np.abs(mx - w / 2) > w / 2) | (np.abs(my - h / 2) > h / 2)] = 0
    return clamp8(out)


def fx_custom_curves(img, c):
    x = np.arange(256) / 255.0
    s = 1 / (1 + np.exp(-(x - 0.5) * 8))
    s = (s - s.min()) / (s.max() - s.min())
    k = ease(c.p * 2)
    curve = (x * (1 - k) + s * k) * 255
    out = cv2.LUT(img, clamp8(curve))
    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
    hue = hsv[..., 0]
    orange = np.exp(-((hue - 12) ** 2) / 60)
    hsv[..., 1] = np.clip(hsv[..., 1] * (1 + 0.5 * k * orange), 0, 255)
    blue = np.exp(-((hue - 110) ** 2) / 120)
    hsv[..., 0] = hue + k * blue * 8
    return cv2.cvtColor(clamp8(hsv), cv2.COLOR_HSV2BGR)


def fx_dome(img, c):
    h, w = img.shape[:2]
    cx = w * (0.3 + 0.4 * (0.5 + 0.5 * math.sin(c.t * 1.7)))
    cy = h * (0.35 + 0.2 * math.sin(c.t * 1.1))
    return Warp(h, w).bulge((cx, cy), 210, 0.65).apply(img)


def fx_doubt(img, c):
    f = c.face
    layer = Image.new("RGBA", (img.shape[1], img.shape[0]), (0, 0, 0, 0))
    for side, off in ((-1, 0.0), (1, 0.15)):
        size = int(f.width * (0.55 if side < 0 else 0.42) * min(1, (c.t - off) * 5 + 0.2))
        if size < 8:
            continue
        q = sticker_text("?", size, (255, 255, 255, 255), (0, 0, 0, 255), max(3, size // 14), rot=-f.roll + side * 18 + math.sin(c.t * 3 + side) * 6, path=FONT_BOLD)
        q = q.transform(q.size, Image.AFFINE, (1, 0.25 * side, 0, 0, 1, 0), resample=Image.BICUBIC)
        pos = safe(f.top + f.up * f.height * 0.1 + np.array([side * f.width * 0.65, 0]), size // 2)
        put(layer, q, pos)
    return comp_pil(img, layer)


def fx_loading(img, c):
    f = c.face
    layer, d = pil_layer(*img.shape[:2])
    r = f.width * 0.22
    cx, cy = safe(f.top + f.up * f.height * 0.35, int(r))
    d.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], fill=(240, 240, 240, 220))
    for i in range(12):
        a = math.radians(i * 30 + c.t * 360)
        al = int(255 * ((i + 1) / 12))
        x1, y1 = cx + math.cos(a) * r * 0.45, cy + math.sin(a) * r * 0.45
        x2, y2 = cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9
        d.line([(x1, y1), (x2, y2)], fill=(110, 110, 110, al), width=max(3, int(r * 0.16)))
    return comp_pil(img, layer)


def eye_beams(img, c, col_core, col_glow, spread=0.0, length=2.0, thick=10):
    f = c.face
    layer = np.zeros_like(img)
    fwd = np.array([f.yaw * 0.8, 0.35])  # toward camera, slightly down in screen space
    fwd = fwd / np.linalg.norm(fwd)
    for e, s in ((f.l_eye, -1), (f.r_eye, 1)):
        d = fwd + np.array([s * spread, 0])
        d = d / np.linalg.norm(d)
        end = e + d * img.shape[0] * length
        cv2.line(layer, tuple(e.astype(int)), tuple(end.astype(int)), col_glow, thick * 2, cv2.LINE_AA)
        cv2.line(layer, tuple(e.astype(int)), tuple(end.astype(int)), col_core, max(2, thick // 2), cv2.LINE_AA)
        cv2.circle(layer, tuple(e.astype(int)), int(f.width * 0.07), col_core, -1, cv2.LINE_AA)
    return add_glow(img, layer, 14, 0.9)


def fx_face_laser(img, c):
    return eye_beams(img, c, (200, 200, 255), (30, 30, 255), spread=0.0, thick=8)


def fx_face_zoom(img, c):
    f = c.face
    s = 1 + 0.7 * ease(c.p * 1.6) - 0.7 * ease((c.p - 0.75) * 4)
    h, w = img.shape[:2]
    cx, cy = f.center
    return affine(img, 0, s, (w / 2 - cx) * (s - 1) / s * 0, 0, center=(cx, cy))


def fx_autothreshold(img, c):
    g = lum(img)
    _, t = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(t, cv2.COLOR_GRAY2BGR)


def fx_corners(img, c):
    h, w = img.shape[:2]
    j = 70 * math.sin(c.t * 2.2)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[60 + j, 90], [w - 40, 40 - j], [w - 80 + j, h - 60], [30, h - 120 - j]])
    M = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(img, M, (w, h), borderValue=(20, 20, 20))
    for p in dst:
        cv2.circle(out, tuple(p.astype(int)), 12, (60, 220, 255), -1, cv2.LINE_AA)
    return out


def fx_shake_ultimate(img, c):
    a = 6 * fbm(c.t * 3, 1)
    tx, ty = 30 * fbm(c.t * 4, 2), 30 * fbm(c.t * 4, 3)
    out = affine(img, a, 1.12 + 0.04 * fbm(c.t * 2, 4), tx, ty)
    k = int(abs(fbm(c.t * 5, 5)) * 18) * 2 + 1
    if k > 3:
        kernel = np.zeros((k, k), np.float32)
        kernel[k // 2, :] = 1 / k
        out = cv2.filter2D(out, -1, kernel)
    op = 0.85 + 0.15 * math.sin(c.t * 9)
    return clamp8(out * op)


def fx_cartoon(img, c):
    color = img
    for _ in range(2):
        color = cv2.bilateralFilter(color, 9, 60, 60)
    color = (color // 32) * 32 + 16
    edges = cv2.adaptiveThreshold(cv2.medianBlur(lum(img), 7), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 4)
    return cv2.bitwise_and(color, color, mask=edges)


def fx_color_distance(img, c):
    target = np.array([190, 130, 90], np.float32)  # shirt blue (BGR)
    d = np.linalg.norm(img.astype(np.float32) - target, axis=2)
    v = clamp8(255 - d * 1.4)
    return cv2.cvtColor(v, cv2.COLOR_GRAY2BGR)


def fx_halftone(img, c):
    h, w = img.shape[:2]
    out = np.full_like(img, 255)
    cell = 9
    small = cv2.resize(img, (w // cell, h // cell), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    cmy = 1 - small[..., ::-1]  # c m y from r g b
    inks = [(255, 255, 0), (255, 0, 255), (0, 255, 255)]  # BGR for cyan, magenta, yellow
    layers = []
    for ch, (ink, ang) in enumerate(zip(inks, (15, 75, 0))):
        L = np.full_like(img, 255)
        for y in range(small.shape[0]):
            for x in range(small.shape[1]):
                r = cmy[y, x, ch] * cell * 0.75
                if r > 0.6:
                    ox = (x + 0.5 + 0.25 * math.sin(math.radians(ang))) * cell
                    oy = (y + 0.5 + 0.25 * math.cos(math.radians(ang))) * cell
                    cv2.circle(L, (int(ox), int(oy)), int(r), ink, -1, cv2.LINE_AA)
        layers.append(L.astype(np.float32) / 255)
    m = layers[0] * layers[1] * layers[2]
    return clamp8(m * 255)


def fx_defish(img, c):
    h, w = img.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (x - w / 2) / (w / 2), (y - h / 2) / (h / 2)
    r = np.sqrt(nx * nx + ny * ny)
    k = 0.45 * ease(c.p * 2)
    f = 1 + k * r * r
    return cv2.remap(img, nx / f * (w / 2) + w / 2, ny / f * (h / 2) + h / 2, cv2.INTER_LINEAR, borderValue=0)


BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16


def fx_dither(img, c):
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 3, h // 3), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    t = np.tile(BAYER, (small.shape[0] // 4 + 1, small.shape[1] // 4 + 1))[:small.shape[0], :small.shape[1]][..., None]
    q = (small + (t - 0.5) * 0.5 > 0.5).astype(np.float32)
    return cv2.resize(clamp8(q * 255), (w, h), interpolation=cv2.INTER_NEAREST)


def fx_edgeglow(img, c):
    e = cv2.Canny(cv2.GaussianBlur(lum(img), (5, 5), 0), 40, 110)
    hue = int((c.t * 90) % 180)
    col = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0, 0]
    layer = np.zeros_like(img)
    layer[e > 0] = col
    return add_glow((img * 0.55).astype(np.uint8), layer, 3, 1.2)


def fx_elastic(img, c):
    h, w = img.shape[:2]
    x = np.linspace(-1, 1, w, dtype=np.float32)
    k = 0.6 * ease(c.p * 2)
    src = np.sign(x) * np.abs(x) ** (1 + k)
    mx = np.tile((src + 1) / 2 * (w - 1), (h, 1))
    my = np.tile(np.arange(h, dtype=np.float32)[:, None], (1, w))
    return cv2.remap(img, mx.astype(np.float32), my, cv2.INTER_LINEAR)


def fx_emboss(img, c):
    k = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], np.float32)
    e = cv2.filter2D(lum(img).astype(np.float32), -1, k) + 128
    return cv2.cvtColor(clamp8(e), cv2.COLOR_GRAY2BGR)


def fx_flippo(img, c):
    out = cv2.flip(img, 1)
    if c.p > 0.5:
        out = cv2.flip(out, 0)
    return out


def fx_glow(img, c):
    bright = np.clip(img.astype(np.float32) - 120, 0, 255) * 1.6
    g = cv2.GaussianBlur(bright, (0, 0), 25)
    return screen(img, clamp8(g))


def fx_heatmap(img, c):
    return cv2.applyColorMap(lum(img), cv2.COLORMAP_INFERNO)


def fx_lens_correction(img, c):
    h, w = img.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (x - w / 2) / (w / 2), (y - h / 2) / (h / 2)
    r2 = nx * nx + ny * ny
    k = 0.35 * math.sin(c.t * 2.5)
    f = 1 + k * r2
    out = cv2.remap(img, nx * f * (w / 2) + w / 2, ny * f * (h / 2) + h / 2, cv2.INTER_LINEAR, borderValue=0)
    for gx in range(0, w, 90):
        cv2.line(out, (gx, 0), (gx, h), (255, 255, 255), 1)
    for gy in range(0, h, 90):
        cv2.line(out, (0, gy), (w, gy), (255, 255, 255), 1)
    return out


def fx_letterbox(img, c):
    h, w = img.shape[:2]
    out = img.copy()
    bar = int(h * 0.2 * ease(c.p * 3))
    out[:bar] = 0
    out[h - bar:] = 0
    return out


def fx_ndvi(img, c):
    f = img.astype(np.float32)
    nir = f[..., 2] * 0.6 + f[..., 1] * 0.4
    vis = f[..., 0] + 1
    ndvi = (nir - vis) / (nir + vis + 1)
    v = clamp8((ndvi + 0.4) / 0.9 * 255)
    return cv2.applyColorMap(v, cv2.COLORMAP_TURBO)


def fx_nosync(img, c):
    h, w = img.shape[:2]
    roll = int((c.t * 420) % h)
    out = np.roll(img, roll, axis=0)
    rng = np.random.default_rng(c.k)
    for _ in range(6):
        y = rng.integers(0, h - 30)
        hh = rng.integers(5, 30)
        out[y:y + hh] = np.roll(out[y:y + hh], rng.integers(-60, 60), axis=1)
    out[(np.arange(h) + roll) % h < 12] = 0
    return out


def fx_perspective(img, c):
    h, w = img.shape[:2]
    k = 0.22 * math.sin(c.t * 1.8)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[w * max(0, k), h * 0.06], [w - w * max(0, -k), h * 0.06 * 0], [w - w * max(0, -k), h], [w * max(0, k), h - h * 0.06]])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (w, h), borderValue=(15, 15, 15))


def fx_pixelize(img, c):
    h, w = img.shape[:2]
    b = int(6 + 22 * (0.5 + 0.5 * math.sin(c.t * 2)))
    small = cv2.resize(img, (w // b, h // b), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def fx_posterize(img, c):
    lv = 4
    return clamp8((img // (256 // lv)) * (255 // (lv - 1)))


def fx_primaries(img, c):
    f = img.astype(np.float32)
    mx = f.max(axis=2, keepdims=True)
    return clamp8(np.where(f >= mx * 0.75, 255, 0) * (mx > 50))


def fx_rgbsplit(img, c):
    s = int(10 + 12 * math.sin(c.t * 4))
    b, g, r = cv2.split(img)
    return cv2.merge([np.roll(b, -s, axis=1), g, np.roll(r, s, axis=1)])


def fx_scanlines(img, c):
    out = img.copy()
    out[::3] = (out[::3] * 0.25).astype(np.uint8)
    out[1::3] = (out[1::3] * 0.75).astype(np.uint8)
    return out


def fx_sharpness(img, c):
    blur = cv2.GaussianBlur(img, (0, 0), 3)
    sharp = cv2.addWeighted(img, 2.4, blur, -1.4, 0)
    x = int(img.shape[1] * (0.3 + 0.4 * ease(c.p * 1.5)))
    return split_view(img, sharp, x, "before", "sharpened")


def fx_sigmoidal(img, c):
    g = lum(img).astype(np.float32) / 255
    s = 1 / (1 + np.exp(-(g - 0.5) * 14))
    return cv2.cvtColor(clamp8(s * 255), cv2.COLOR_GRAY2BGR)


def fx_sobel(img, c):
    g = lum(img).astype(np.float32)
    m = np.sqrt(cv2.Sobel(g, cv2.CV_32F, 1, 0) ** 2 + cv2.Sobel(g, cv2.CV_32F, 0, 1) ** 2)
    return cv2.cvtColor(clamp8(m * 0.8), cv2.COLOR_GRAY2BGR)


def fx_softglow(img, c):
    l = lum(img).astype(np.float32)
    mask = np.clip((l - 150) / 105, 0, 1)[..., None]
    g = cv2.GaussianBlur(img.astype(np.float32) * mask, (0, 0), 18)
    return screen(img, clamp8(g * 1.3))


def fx_squareblur(img, c):
    k = int(3 + 40 * (0.5 + 0.5 * math.sin(c.t * 2.2)))
    return cv2.blur(img, (k, k))


def fx_threelay(img, c):
    g = lum(img)
    t1, t2 = np.percentile(g, 33), np.percentile(g, 66)
    v = np.where(g < t1, 0, np.where(g < t2, 128, 255)).astype(np.uint8)
    return cv2.cvtColor(v, cv2.COLOR_GRAY2BGR)


def fx_threshold(img, c):
    g = lum(img)
    t = np.percentile(g, 50) + 25 * math.sin(c.t * 2)
    return cv2.cvtColor(np.where(g > t, 255, 0).astype(np.uint8), cv2.COLOR_GRAY2BGR)


def fx_twolay(img, c):
    g = lum(img)
    t = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 61, 0)
    return cv2.cvtColor(t, cv2.COLOR_GRAY2BGR)


def fx_gaunt(img, c):
    f = c.face
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.fillPoly(mask, [f.oval()], 255)
    m = cv2.GaussianBlur(mask, (0, 0), 10).astype(np.float32) / 255 * 0.45
    out = over(img, clamp8(img * np.array([1.15, 0.85, 0.75])), m)
    layer = Image.new("RGBA", (img.shape[1], img.shape[0]), (0, 0, 0, 0))
    s1 = sticker_text("憔悴", int(f.width * 0.32), (255, 255, 255, 255), (40, 90, 200, 255), 8, rot=-f.roll + 8)
    s2 = sticker_text("疲惫", int(f.width * 0.26), (255, 255, 255, 255), (40, 90, 200, 255), 7, rot=-f.roll - 12)
    put(layer, s1, f.top + f.up * f.height * 0.25)
    put(layer, s2, f.p[454] + np.array([f.width * 0.35, -f.height * 0.15]))
    d = ImageDraw.Draw(layer)
    for i in range(4):
        y = (c.t * 80 + i * 40) % 140
        tear(d, f.p[234][0] - 20 - i * 10, f.p[234][1] - 60 + y, 7, fill=(150, 170, 200, 230), outline=(80, 100, 140, 255))
    return comp_pil(out, layer)


def fx_gaussian(img, c):
    ang = c.t * 90
    k = 41
    kernel = np.zeros((k, k), np.float32)
    kernel[k // 2, :] = cv2.getGaussianKernel(k, 9).ravel()
    M = cv2.getRotationMatrix2D((k / 2 - 0.5, k / 2 - 0.5), ang, 1)
    kernel = cv2.warpAffine(kernel, M, (k, k))
    kernel /= kernel.sum()
    return cv2.filter2D(img, -1, kernel)


def fx_graffiti_ghost(img, c):
    f = c.face
    p = cv2.GaussianBlur(c.person, (0, 0), 1.2)
    out = over(clamp8(img * 0.8), np.full_like(img, 12), p)
    layer = np.zeros_like(img)
    cnts, _ = cv2.findContours((p > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(layer, cnts, -1, (60, 200, 40), 3, cv2.LINE_AA)
    m, ml, mr = f.mouth, f.p[61], f.p[291]
    w = (mr - ml)[0] * 1.6
    pts = []
    n = 9
    for i in range(n + 1):
        x = m[0] - w / 2 + w * i / n
        y = m[1] + (8 if i % 2 else -8) + 18 * math.sin(i / n * math.pi)
        pts.append((x, y))
    cv2.polylines(layer, [np.array(pts, np.int32)], False, (80, 255, 60), 5, cv2.LINE_AA)
    cv2.ellipse(layer, tuple(m.astype(int)), (int(w / 2), 26), 0, 0, 180, (80, 255, 60), 4, cv2.LINE_AA)
    out = add_glow(out, layer, 8, 1.0)
    L, d = pil_layer(*img.shape[:2])
    for e in (f.l_eye, f.r_eye):
        star(d, e[0], e[1], f.width * 0.08, (255, 240, 80, 255), rot=c.t * 90)
    for s in (-1, 1):
        base = f.top + np.array([s * f.width * 0.28, 0])
        tip = base + f.up * f.height * 0.45 + np.array([s * f.width * 0.15, 0])
        d.polygon([tuple(base - np.array([f.width * 0.08, 0])), tuple(base + np.array([f.width * 0.08, 0])), tuple(tip)], fill=(230, 40, 60, 255))
    return comp_pil(out, L)


def fx_hair(img, c):
    m = cv2.GaussianBlur((c.cat == 1).astype(np.float32), (0, 0), 2)
    hue = (c.t * 60) % 180
    col = cv2.cvtColor(np.uint8([[[hue, 220, 255]]]), cv2.COLOR_HSV2BGR)[0, 0].astype(np.float32)
    tinted = clamp8(lum(img)[..., None].astype(np.float32) / 255 * col * 1.4)
    return over(img, tinted, m * 0.85)


HAND_EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14),
              (14, 15), (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


def fx_hand_landmarks(img, c):
    out = img.copy()
    for hand, col in zip(c.hands, ((60, 255, 120), (255, 160, 60))):
        for a, b in HAND_EDGES:
            cv2.line(out, tuple(hand[a].astype(int)), tuple(hand[b].astype(int)), col, 4, cv2.LINE_AA)
        for p in hand:
            cv2.circle(out, tuple(p.astype(int)), 7, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(out, tuple(p.astype(int)), 7, col, 2, cv2.LINE_AA)
    if not c.hands:
        cv2.putText(out, "no hands in frame", (30, out.shape[0] - 50), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    return out


def fx_highlight(img, c):
    h, w = img.shape[:2]
    f = c.face
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = f.center
    ang = np.arctan2(y - cy, x - cx)
    rays = 0.5 + 0.5 * np.cos(ang * 14 + c.t * 2)
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / h
    bg = np.dstack([40 + 60 * rays * (1 - dist), 150 + 80 * rays * (1 - dist), 230 + 25 * rays]).clip(0, 255) * np.clip(1.2 - dist, 0.3, 1)[..., None]
    p = cv2.GaussianBlur(c.person, (0, 0), 1.5)
    out = over(clamp8(bg), img, p)
    mask = (p > 0.5).astype(np.uint8)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    rng = np.random.default_rng(int(c.t * 8))
    for cnt in cnts:
        if len(cnt) < 50:
            continue
        pts = cnt[::6, 0].astype(np.float32)
        n = np.zeros_like(pts)
        pts = pts + rng.normal(0, 2.5, pts.shape)
        cv2.polylines(out, [pts.astype(np.int32) + np.array([8, -6])], True, (255, 255, 255), 5, cv2.LINE_AA)
    return out


def fx_inspiration(img, c):
    f = c.face
    flash = math.exp(-((c.t - 0.6) ** 2) / 0.02)
    out = clamp8(img * (1 - 0.45 * min(1, c.t * 2) + 0.3 * flash))
    layer = np.zeros_like(img)
    rng = np.random.default_rng(int(c.t * 15))
    origin = f.top + f.up * f.height * 0.1 + np.array([f.width * 0.75, -f.height * 0.1])
    if c.t > 0.4:
        for i in range(7):
            a = rng.uniform(0, math.tau)
            end = origin + np.array([math.cos(a), math.sin(a)]) * rng.uniform(80, 200)
            cv2.polylines(layer, [lightning(rng, origin, end, 20, 4)], False, (200, 245, 255), 3, cv2.LINE_AA)
        cv2.circle(layer, tuple(origin.astype(int)), 22, (230, 250, 255), -1, cv2.LINE_AA)
    glint = f.p[454] + np.array([f.width * 0.15, -f.height * 0.35])
    L = int(40 + 30 * flash)
    cv2.line(layer, (int(glint[0] - L), int(glint[1])), (int(glint[0] + L), int(glint[1])), (255, 255, 255), 3, cv2.LINE_AA)
    cv2.line(layer, (int(glint[0]), int(glint[1] - L)), (int(glint[0]), int(glint[1] + L)), (255, 255, 255), 3, cv2.LINE_AA)
    return add_glow(out, layer, 10, 1.0)


def fx_laser_eyes(img, c):
    f = c.face
    out = eye_beams(img, c, (210, 245, 255), (40, 190, 255), spread=0.35, thick=14)
    layer = np.zeros_like(img)
    for e in (f.l_eye, f.r_eye):
        cv2.ellipse(layer, tuple(e.astype(int)), (int(f.width * 0.09), int(f.width * 0.05)), f.roll, 0, 360, (60, 210, 255), -1, cv2.LINE_AA)
    return add_glow(out, layer, 8, 0.8)


def fx_lightning_eyes(img, c):
    f = c.face
    layer = np.zeros_like(img)
    rng = np.random.default_rng(c.k)
    for e in (f.l_eye, f.r_eye):
        cv2.circle(layer, tuple(e.astype(int)), int(f.width * 0.06), (230, 250, 255), -1, cv2.LINE_AA)
        for _ in range(3):
            a = rng.uniform(0, math.tau)
            end = e + np.array([math.cos(a), math.sin(a)]) * rng.uniform(f.width * 0.15, f.width * 0.4)
            cv2.polylines(layer, [lightning(rng, e, end, 10, 3)], False, (170, 230, 255), 2, cv2.LINE_AA)
    return add_glow(img, layer, 12, 1.1)


def fx_linear_mask(img, c):
    h, w = img.shape[:2]
    stops = [(0.0, 0.0), (0.25 + 0.1 * math.sin(c.t * 2), 1.0), (0.7, 1.0), (1.0, 0.0)]
    y = np.linspace(0, 1, h)
    a = np.interp(y, [s[0] for s in stops], [s[1] for s in stops])
    a = np.tile(a[:, None], (1, w)).astype(np.float32)
    return over(checker(h, w), img, a)


def fx_local_mosaic(img, c):
    f = c.face
    x0, y0 = (f.center - np.array([f.width * 0.6, f.height * 0.7])).astype(int)
    x1, y1 = (f.center + np.array([f.width * 0.6, f.height * 0.6])).astype(int)
    x0, y0 = max(0, x0), max(0, y0)
    roi = img[y0:y1, x0:x1]
    b = 18
    small = cv2.resize(roi, (max(1, roi.shape[1] // b), max(1, roi.shape[0] // b)), interpolation=cv2.INTER_AREA)
    mos = cv2.resize(small, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
    m = np.zeros(img.shape[:2], np.float32)
    m[y0:y1, x0:x1] = 1
    m = cv2.GaussianBlur(m, (0, 0), 6)
    full = img.copy()
    full[y0:y1, x0:x1] = mos
    return over(img, full, m)


def fx_lost(img, c):
    f = c.face
    L, d = pil_layer(*img.shape[:2])
    rx, ry = f.width * 0.85, f.width * 0.25
    cx, cy = safe(f.top + f.up * f.height * 0.05, 0)
    cx = f.top[0]
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(10, 10, 10, 255), width=10)
    items = ["迷", "茫", "★", "迷", "茫", "★"]
    cols = [(0, 230, 255, 255), (255, 230, 0, 255), (255, 90, 160, 255), (255, 255, 255, 255), (0, 230, 255, 255), (120, 255, 120, 255)]
    for i, (txt, col) in enumerate(zip(items, cols)):
        a = c.t * 2.2 + i / len(items) * math.tau
        x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
        if math.sin(a) < 0 and txt != "★":
            col = col[:3] + (150,)
        s = sticker_text(txt, int(f.width * 0.18), col, (0, 0, 0, 255), 5, path=FONT_CJK)
        put(L, s, (x, y))
    return comp_pil(img, L)


def fx_black_overlay(img, c):
    h, w = img.shape[:2]
    over_l = np.zeros_like(img, np.float32)
    rng = np.random.default_rng(3)
    n = 140
    xs, ys0, sp, sz = rng.uniform(0, w, n), rng.uniform(0, h, n), rng.uniform(80, 260, n), rng.uniform(2, 7, n)
    for x, y0, s, z, i in zip(xs, ys0, sp, sz, range(n)):
        y = (y0 - c.t * s) % h
        xx = x + 20 * math.sin(c.t * 2 + i)
        cv2.circle(over_l, (int(xx), int(y)), int(z), (40, 140 + (i % 5) * 20, 255), -1, cv2.LINE_AA)
    leak = np.zeros_like(over_l)
    cv2.circle(leak, (int(w * 0.9), int(h * 0.15)), int(h * 0.35), (30, 90, 255), -1)
    over_l = over_l + cv2.GaussianBlur(leak, (0, 0), 90) * (0.6 + 0.4 * math.sin(c.t * 3))
    over_l = cv2.GaussianBlur(over_l, (0, 0), 1.2)
    return screen(img, clamp8(over_l))


_LUT = None


def fx_lut(img, c):
    global _LUT
    if _LUT is None:
        _LUT = load_cube(str(PLUGIN_ROOT / "styles" / "luts" / "blue-tint.cube"))
    graded = apply_lut(img, _LUT)
    x = int(img.shape[1] * (0.3 + 0.4 * ease(c.p * 1.5)))
    return split_view(img, graded, x, "original", "blue-tint.cube")


def fx_magnifier(img, c):
    h, w = img.shape[:2]
    cx = w * (0.25 + 0.5 * (0.5 + 0.5 * math.sin(c.t * 1.6)))
    cy = h * (0.55 + 0.15 * math.cos(c.t * 1.2))
    r = 150
    zoom = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    out = img.copy()
    y, x = np.mgrid[0:h, 0:w]
    m = ((x - cx) ** 2 + (y - cy) ** 2) < r * r
    sx = np.clip(((x - cx) + cx * 2).astype(int), 0, 2 * w - 1)
    sy = np.clip(((y - cy) + cy * 2).astype(int), 0, 2 * h - 1)
    out[m] = zoom[sy[m], sx[m]]
    cv2.circle(out, (int(cx), int(cy)), r, (255, 255, 255), 8, cv2.LINE_AA)
    cv2.circle(out, (int(cx), int(cy)), r + 4, (60, 60, 60), 2, cv2.LINE_AA)
    return out


def fx_mask(img, c):
    h, w = img.shape[:2]
    f = c.face
    pts = []
    for i in range(24):
        a = i / 24 * math.tau
        rr = 1 + 0.08 * math.sin(a * 3 + c.t * 2)
        pts.append(f.center + np.array([math.cos(a) * f.width * 1.25 * rr, math.sin(a) * f.height * 1.25 * rr]))
    pts = np.array(pts, np.int32)
    m = np.zeros((h, w), np.uint8)
    cv2.fillPoly(m, [pts], 255)
    m = cv2.GaussianBlur(m, (0, 0), 4).astype(np.float32) / 255
    out = over(checker(h, w), img, m)
    cv2.polylines(out, [pts], True, (60, 220, 255), 4, cv2.LINE_AA)
    for p in pts[::3]:
        cv2.circle(out, tuple(p), 7, (255, 255, 255), -1, cv2.LINE_AA)
    return out


def fx_person_focus(img, c):
    h, w = img.shape[:2]
    f = c.face
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((x - f.center[0]) ** 2 + ((y - f.center[1]) * 0.8) ** 2)
    r = f.height * 1.3
    a = np.clip(1 - (d - r) / 180, 0.18, 1)
    return clamp8(img * a[..., None])


def fx_person_regions(img, c):
    cols = {1: (255, 60, 200), 2: (60, 200, 255), 3: (80, 255, 120), 4: (255, 170, 40), 5: (255, 255, 255)}
    out = img.copy()
    for k, col in cols.items():
        m = cv2.GaussianBlur((c.cat == k).astype(np.float32), (0, 0), 1.5) * 0.55
        out = over(out, np.full_like(img, col), m)
    return out


POSE_EDGES = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
              (0, 2), (0, 5), (2, 7), (5, 8), (9, 10), (15, 17), (15, 19), (16, 18), (16, 20)]


def fx_body(img, c):
    out = (img * 0.7).astype(np.uint8)
    P = c.pose
    for a, b in POSE_EDGES:
        if P[a, 2] > 0.3 and P[b, 2] > 0.3:
            cv2.line(out, tuple(P[a, :2].astype(int)), tuple(P[b, :2].astype(int)), (255, 210, 60), 5, cv2.LINE_AA)
    for i, p in enumerate(P):
        if p[2] > 0.3:
            cv2.circle(out, tuple(p[:2].astype(int)), 8, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(out, tuple(p[:2].astype(int)), 8, (60, 120, 255), 3, cv2.LINE_AA)
    return out


def fx_question_marks(img, c):
    f = c.face
    L = Image.new("RGBA", (img.shape[1], img.shape[0]), (0, 0, 0, 0))
    base = f.center
    for i in range(5):
        a = math.radians(-165 + i * 37.5)
        pos = safe(base + np.array([math.cos(a) * f.width * 1.05, math.sin(a) * f.height * 0.85]), 30)
        appear = c.t - i * 0.12
        if appear <= 0:
            continue
        s = min(1.0, appear * 6) * (1 + 0.15 * math.sin(appear * 25) * math.exp(-appear * 4))
        size = int(f.width * 0.38 * s)
        if size < 6:
            continue
        q = sticker_text("?", size, (255, 225, 40, 255), (60, 40, 0, 255), max(3, size // 12), rot=math.sin(c.t * 5 + i) * 15 - f.roll, path=FONT_BOLD)
        put(L, q, pos)
    return comp_pil(img, L)


def fx_rect_mask(img, c):
    h, w = img.shape[:2]
    s = 0.55 + 0.25 * math.sin(c.t * 2)
    rw, rh = int(w * s), int(h * s * 0.7)
    m = np.zeros((h, w), np.uint8)
    x0, y0 = (w - rw) // 2, int(h * 0.12)
    r = 60
    cv2.rectangle(m, (x0 + r, y0), (x0 + rw - r, y0 + rh), 255, -1)
    cv2.rectangle(m, (x0, y0 + r), (x0 + rw, y0 + rh - r), 255, -1)
    for cx, cy in ((x0 + r, y0 + r), (x0 + rw - r, y0 + r), (x0 + r, y0 + rh - r), (x0 + rw - r, y0 + rh - r)):
        cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 6).astype(np.float32) / 255
    return over(checker(h, w), img, m)


def fx_red_hot(img, c):
    f = c.face
    out = Warp(*img.shape[:2]).bulge(f.center, f.height * 1.2, 0.45 + 0.08 * math.sin(c.t * 6)).apply(img)
    W2 = Warp(*img.shape[:2]).bulge(f.center, f.height * 1.2, 0.45 + 0.08 * math.sin(c.t * 6))
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.fillPoly(mask, [f.oval()], 255)
    mask = W2.apply(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR))[..., 0]
    m = cv2.GaussianBlur(mask, (0, 0), 10).astype(np.float32) / 255 * (0.42 + 0.12 * math.sin(c.t * 8))
    red = clamp8(out.astype(np.float32) * np.array([0.45, 0.55, 1.25]) + np.array([0, 0, 25]))
    return over(out, red, m)


def fx_sad(img, c):
    f = c.face
    h, w = img.shape[:2]
    bgL, bd = pil_layer(h, w)
    for row in range(5):
        y = 120 + row * 230
        off = (c.t * 160 * (1 if row % 2 else -1)) % 400
        for k in range(-1, 4):
            draw_text_outlined(bd, (k * 400 + off, y), "伤心", 120, (120, 170, 255, 170), (255, 255, 255, 220), 6)
    bg = comp_pil(img, bgL)
    p = cv2.GaussianBlur(c.person, (0, 0), 1.5)
    out = over(bg, img, p)
    L, d = pil_layer(h, w)
    for e in (f.l_eye, f.r_eye):
        top = e + np.array([0, f.width * 0.05])
        flow = (c.t * 300) % 420 + 120
        for s in range(0, int(min(flow, 520)), 6):
            wob = 6 * math.sin(s / 25 + c.t * 6)
            d.ellipse([top[0] - 13 + wob, top[1] + s - 10, top[0] + 13 + wob, top[1] + s + 10], fill=(70, 160, 255, 210))
    return comp_pil(out, L)


def fx_camera_shake(img, c):
    a = 2.2 * fbm(c.t * 6, 11)
    tx, ty = 16 * fbm(c.t * 7, 12), 16 * fbm(c.t * 7, 13)
    s = 1.08 + 0.02 * math.sin(c.t * 2.5)
    return affine(img, a, s, tx, ty)


def fx_gloomy(img, c):
    f = c.face
    out = clamp8(cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2HSV) * np.array([1, 0.55, 0.85]), cv2.COLOR_HSV2BGR) if False else img)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] *= 0.55
    hsv[..., 2] *= 0.85
    out = cv2.cvtColor(clamp8(hsv), cv2.COLOR_HSV2BGR)
    L, d = pil_layer(*img.shape[:2])
    base = safe(f.top + f.up * f.height * 0.45, 40)
    for k, ox in enumerate((-0.45, 0.0, 0.45)):
        cx, cy = base + np.array([ox * f.width + 10 * math.sin(c.t * 2 + k), -abs(ox) * 30])
        for j in range(6):
            r = 26 + j * 9
            d.ellipse([cx - r * 1.4 + j * 10 - 25, cy - r * 0.6, cx + r * 1.4 + j * 10 - 25, cy + r * 0.6], fill=(110, 70, 165, 210))
        pts = []
        for i in range(60):
            a = i * 0.35 + c.t * 4 + k
            rr = i * 0.85
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.5))
        d.line(pts, fill=(230, 210, 255, 255), width=4)
    return comp_pil(out, L)


def fx_slog3(img, c):
    flat = log_flatten(img)
    graded = clamp8((img.astype(np.float32) - 128) * 1.05 + 128)
    x = int(img.shape[1] * (0.25 + 0.5 * ease(c.p * 1.4)))
    return split_view(flat, graded, x, "S-Log3", "s709")


def fx_stone(img, c):
    f = c.face
    g = lum(img).astype(np.float32)
    noise = cv2.GaussianBlur(np.random.default_rng(1).normal(0, 1, g.shape).astype(np.float32), (0, 0), 2.2) * 26
    stone = np.clip(g * 0.8 + 30 + noise, 0, 255)
    stone = np.dstack([stone * 0.98, stone, stone * 1.02])
    prog = ease(c.p * 2.2)
    h = img.shape[0]
    y = np.arange(h)[:, None]
    reveal = (y < h * prog * 1.1).astype(np.float32)
    p = cv2.GaussianBlur(c.person, (0, 0), 1.5) * reveal
    out = over(img, clamp8(stone), p)
    if prog > 0.6:
        rng = np.random.default_rng(5)
        a = f.top + np.array([-f.width * 0.1, -f.height * 0.1])
        b = f.chin + np.array([f.width * 0.25, f.height * 0.6])
        crack = lightning(rng, a, b, 40, 5)
        cv2.polylines(out, [crack], False, (25, 25, 25), 6, cv2.LINE_AA)
        cv2.polylines(out, [crack + np.array([3, 2])], False, (200, 200, 200), 2, cv2.LINE_AA)
    return out


def fx_surprise(img, c):
    f = c.face
    L = Image.new("RGBA", (img.shape[1], img.shape[0]), (0, 0, 0, 0))
    for s, tdelay in ((-1, 0), (1, 0.1)):
        k = min(1, max(0, (c.t - tdelay) * 6))
        if k <= 0:
            continue
        size = int(f.width * 0.42 * k * (1 + 0.15 * math.sin(c.t * 20) * math.exp(-c.t * 3)))
        e = sticker_text("!", max(8, size), (255, 200, 30, 255), (90, 50, 0, 255), max(3, size // 10), rot=-f.roll - s * 20, path=FONT_BOLD)
        pos = (f.p[234] if s < 0 else f.p[454]) + np.array([s * f.width * 0.25, -f.height * 0.35])
        put(L, e, pos)
    return comp_pil(img, L)


def fx_really_thanks(img, c):
    f = c.face
    W = Warp(*img.shape[:2])
    W.bulge(f.mouth + np.array([0, f.height * 0.05]), f.width * 0.5, 0.55, sx=1.6, sy=-0.2)
    W.bulge(f.p[205], f.width * 0.3, 0.35).bulge(f.p[425], f.width * 0.3, 0.35)  # cheeks
    W.bulge(f.chin, f.width * 0.4, 0.3)
    W.shift(f.p[105], f.width * 0.25, np.array([0, -10])).shift(f.p[334], f.width * 0.25, np.array([0, -10]))
    out = W.apply(img)
    L, d = pil_layer(*img.shape[:2])
    x, y = f.p[454] + np.array([5, -f.height * 0.3])
    tear(d, x, y + 15 * math.sin(c.t * 3), 22)
    return comp_pil(out, L)


def fx_tilt_shift(img, c):
    h, w = img.shape[:2]
    blur = cv2.GaussianBlur(img, (0, 0), 9)
    center = h * (0.32 + 0.05 * math.sin(c.t * 1.5))
    y = np.arange(h, dtype=np.float32)
    a = np.clip((np.abs(y - center) - h * 0.08) / (h * 0.18), 0, 1)[:, None]
    out = over(img, blur, np.tile(a, (1, w)))
    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] *= 1.45
    out = cv2.cvtColor(clamp8(hsv), cv2.COLOR_HSV2BGR)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vig = 1 - 0.5 * (((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2)
    return clamp8(out * vig[..., None])


def fx_something_wrong(img, c):
    f = c.face
    W = Warp(*img.shape[:2])
    W.shift(f.p[105], f.width * 0.18, np.array([0, -8])).shift(f.p[46], f.width * 0.15, np.array([0, 10]))   # left brow slope
    W.shift(f.p[334], f.width * 0.18, np.array([0, -8])).shift(f.p[276], f.width * 0.15, np.array([0, 10]))  # right brow slope
    W.bulge(f.mouth, f.width * 0.3, -0.3, sx=1.4, sy=0.2)  # small forced smile
    W.bulge(f.p[205], f.width * 0.28, 0.3).bulge(f.p[425], f.width * 0.28, 0.3).bulge(f.chin, f.width * 0.35, 0.25)
    out = W.apply(img)
    L, d = pil_layer(*img.shape[:2])
    x, y = f.p[234] + np.array([-10, -f.height * 0.25])
    tear(d, x, y + 10 * math.sin(c.t * 3), 14)
    return comp_pil(out, L)


def fx_zoom(img, c):
    s = 1 + 0.45 * math.sin(c.p * math.pi)
    return affine(img, 0, s)


# name -> function (names must match styles/pixel-effects.json)
EFFECTS = {
    "AI Portrait Matte": fx_portrait_matte, "AI Smart Object Matte": fx_smart_object, "Ape Face": fx_ape_face,
    "ASCII Rain": fx_ascii_rain, "Awkward": fx_awkward, "Big Head": fx_big_head, "Big Mouth Monkey": fx_big_mouth,
    "Brain Confusion": fx_brain_confusion, "Canon Log3 to Canon 709": fx_canon_log, "Circle Mask": fx_circle_mask,
    "Color Wheels": fx_color_wheels, "Cool Red Eye": fx_cool_red_eye, "CRT Retro": fx_crt, "Custom Curves": fx_custom_curves,
    "Dome Magnifier": fx_dome, "Doubt": fx_doubt, "Loading…": fx_loading, "Face Laser Eyes": fx_face_laser,
    "Face Tracking Zoom": fx_face_zoom, "autothreshold": fx_autothreshold, "c0rners": fx_corners,
    "Camera Shake Ultimate": fx_shake_ultimate, "Cartoon": fx_cartoon, "Color Distance": fx_color_distance,
    "colorhalftone": fx_halftone, "Defish0r": fx_defish, "dither": fx_dither, "Edgeglow": fx_edgeglow,
    "Elastic scale filter": fx_elastic, "emboss": fx_emboss, "Flippo": fx_flippo, "Glow": fx_glow, "heatmap0r": fx_heatmap,
    "Lens Correction": fx_lens_correction, "LetterB0xed": fx_letterbox, "NDVI filter": fx_ndvi, "nosync0r": fx_nosync,
    "Perspective": fx_perspective, "pixeliz0r": fx_pixelize, "posterize": fx_posterize, "primaries": fx_primaries,
    "rgbsplit0r": fx_rgbsplit, "scanline0r": fx_scanlines, "Sharpness": fx_sharpness, "sigmoidaltransfer": fx_sigmoidal,
    "Sobel": fx_sobel, "softglow": fx_softglow, "Squareblur": fx_squareblur, "threelay0r": fx_threelay,
    "Threshold0r": fx_threshold, "Twolay0r": fx_twolay, "Gaunt": fx_gaunt, "Gaussian Blur": fx_gaussian,
    "Graffiti Ghost": fx_graffiti_ghost, "Hair Regions": fx_hair, "Hand Landmarks": fx_hand_landmarks,
    "Highlight": fx_highlight, "Inspiration": fx_inspiration, "Laser Eyes": fx_laser_eyes, "Lightning Eyes": fx_lightning_eyes,
    "Linear Mask": fx_linear_mask, "Local Mosaic": fx_local_mosaic, "Lost": fx_lost, "Black Overlay (Screen)": fx_black_overlay,
    "LUT": fx_lut, "Magnifying Glass": fx_magnifier, "Mask": fx_mask, "Person Focus": fx_person_focus,
    "Person Regions": fx_person_regions, "Body Landmarks": fx_body, "Question Marks": fx_question_marks,
    "Rectangle Mask": fx_rect_mask, "Red Hot Face": fx_red_hot, "Sad": fx_sad, "Camera Shake": fx_camera_shake,
    "Gloomy": fx_gloomy, "Sony S-Log3 s709": fx_slog3, "Stone": fx_stone, "Surprise": fx_surprise,
    "Really Thanks": fx_really_thanks, "Tilt-Shift": fx_tilt_shift, "Is Something Wrong": fx_something_wrong, "Zoom": fx_zoom,
}
