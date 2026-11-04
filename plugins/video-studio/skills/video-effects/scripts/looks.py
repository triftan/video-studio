"""Color grades (styles/color-presets.json), LUT files and zoom presets (styles/zoom-presets.json)."""
import json
import math
from pathlib import Path

import cv2
import numpy as np

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
STYLES = PLUGIN_ROOT / "styles"

# HSL bands: centre hue in OpenCV units (0-180)
_BANDS = {"Red": 0, "Orange": 15, "Yellow": 30, "Green": 60, "Aqua": 90, "Blue": 115, "Purple": 135, "Magenta": 160}


def color_presets():
    return json.load(open(STYLES / "color-presets.json"))["presets"]


def zoom_presets():
    return {z["id"]: z for z in json.load(open(STYLES / "zoom-presets.json"))["presets"]}


def _curve_lut(points):
    """Monotone curve through [{'x','y'}...] (0-1) as a 256-entry LUT."""
    xs = np.array([p["x"] for p in points], np.float32)
    ys = np.array([p["y"] for p in points], np.float32)
    return np.clip(np.interp(np.linspace(0, 1, 256), xs, ys) * 255, 0, 255).astype(np.uint8)


def _identity(points):
    return len(points) == 2 and abs(points[0]["y"] - points[0]["x"]) < 1e-3 and abs(points[1]["y"] - points[1]["x"]) < 1e-3


def grade(img, p, frame_index=0, strength=1.0):
    """Apply a color preset dict (as stored in color-presets.json) to a BGR frame."""
    src = img
    f = img.astype(np.float32) / 255.0
    if p.get("basicEnabled", True):
        f = f * (2 ** p.get("exposure", 0))
        c = p.get("contrast", 1)
        f = (f - 0.5) * c + 0.5
        t = (p.get("temperature", 6500) - 6500) / 6500   # >0 warmer, <0 cooler
        f = f * np.array([1 - 0.25 * t, 1, 1 + 0.25 * t], np.float32)
        f[..., 1] *= 1 - 0.1 * p.get("tint", 0) / 100
        fade = p.get("fade", 0)
        if fade:
            f = f * (1 - 0.25 * fade) + 0.25 * fade
    f = np.clip(f, 0, 1)
    if p.get("wheelsEnabled"):
        lift = np.array([p.get("lift_b", 0), p.get("lift_g", 0), p.get("lift_r", 0)], np.float32)
        gamma = np.array([p.get("gamma_b", 1), p.get("gamma_g", 1), p.get("gamma_r", 1)], np.float32)
        gain = np.array([p.get("gain_b", 1), p.get("gain_g", 1), p.get("gain_r", 1)], np.float32)
        f = np.clip((f * gain + lift * (1 - f)), 0, 1) ** (1 / np.maximum(gamma, 0.05))
    out = np.clip(f * 255, 0, 255).astype(np.uint8)
    if p.get("curvesEnabled"):
        if not _identity(p.get("rgbCurve", [])):
            out = cv2.LUT(out, _curve_lut(p["rgbCurve"]))
        chans = list(cv2.split(out))
        for i, key in ((2, "redCurve"), (1, "greenCurve"), (0, "blueCurve")):
            if key in p and not _identity(p[key]):
                chans[i] = cv2.LUT(chans[i], _curve_lut(p[key]))
        out = cv2.merge(chans)
    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    sat = p.get("saturation", 1)
    rich = p.get("richness", 0)
    s *= sat
    s += rich * (1 - s / 255) * s * 0.6      # vibrance: lifts muted colors more than vivid ones
    if p.get("hslEnabled"):
        for name, centre in _BANDS.items():
            dh = p.get(f"hslHue{name}", 0)
            ds = p.get(f"hslSaturation{name}", 0)
            dl = p.get(f"hslLuminance{name}", 0)
            if not (dh or ds or dl):
                continue
            d = np.minimum(np.abs(h - centre), 180 - np.abs(h - centre))
            w = np.clip(1 - d / 15, 0, 1)
            h += w * dh * 0.25
            s *= 1 + w * ds / 100
            v *= 1 + w * dl / 200
    hsv[..., 0] = np.mod(h, 180)
    hsv[..., 1] = np.clip(s, 0, 255)
    hsv[..., 2] = np.clip(v, 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    if p.get("splitEnabled") and p.get("splitAmount", 0):
        hue = p.get("splitHue", 35) / 2
        tone = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0, 0].astype(np.float32)
        lum = out.mean(axis=2, keepdims=True) / 255
        hi = np.clip((lum - p.get("splitPivot", 0.5)) * 2, 0, 1)
        out = out + (tone - 128) * hi * p["splitAmount"] * 0.3 - (tone - 128) * (1 - hi) * p["splitAmount"] * 0.15
    H, W = out.shape[:2]
    if p.get("vignetteEnabled") and p.get("vignetteAmount", 0):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.414
        size = p.get("vignetteSize", 0.5)
        out *= (1 - p["vignetteAmount"] * np.clip((r - size * 0.6) / (1 - size * 0.6), 0, 1) ** 2)[..., None]
    if p.get("grainEnabled") and p.get("grainAmount", 0):
        rng = np.random.default_rng(frame_index)
        gs = max(1, int(p.get("grainSize", 6) / 4))
        n = rng.normal(0, 1, (H // gs + 1, W // gs + 1)).astype(np.float32)
        n = cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC)[:H, :W]
        n = cv2.GaussianBlur(n, (0, 0), 0.6 + p.get("grainSoftness", 0.4))
        out += n[..., None] * p["grainAmount"] * 14
    out = np.clip(out, 0, 255)
    if strength < 1:
        out = src.astype(np.float32) * (1 - strength) + out * strength
    return out.astype(np.uint8)


def load_cube(path):
    size, rows = None, []
    for line in open(path):
        s = line.strip()
        if s.startswith("LUT_3D_SIZE"):
            size = int(s.split()[1])
        elif s and (s[0].isdigit() or s[0] in "-.") and len(s.split()) == 3:
            rows.append([float(v) for v in s.split()])
    return np.array(rows, np.float32).reshape(size, size, size, 3)


def apply_lut(img, lut, strength=1.0):
    n = lut.shape[0]
    rgb = img[..., ::-1].astype(np.float32) / 255 * (n - 1)
    i = np.clip(np.round(rgb).astype(np.int32), 0, n - 1)
    out = lut[i[..., 2], i[..., 1], i[..., 0]][..., ::-1] * 255
    if strength < 1:
        out = img * (1 - strength) + out * strength
    return np.clip(out, 0, 255).astype(np.uint8)


def _spring(x):
    """0 -> 1 with a soft overshoot, like a spring settling."""
    x = min(1.0, max(0.0, x))
    return 1 - math.exp(-6 * x) * math.cos(7 * x)


def zoom_scale(preset, t, dur):
    """Magnification at time t (s) within an effect of length dur (s)."""
    o = preset["propertyOverrides"]
    m = o.get("magnification", 1.4)
    shape, direction = o.get("shape"), o.get("direction", "in")
    if shape == "instant":
        return m
    if shape == "slow-push":
        return 1 + (m - 1) * (t / max(dur, 1e-6))
    if shape == "slow-pull":
        return m - (m - 1) * (t / max(dur, 1e-6))
    ein, eout = o.get("easeInDurationInSeconds", 0) or 0.0001, o.get("easeOutDurationInSeconds", 0) or 0.0001
    if direction == "in":
        return 1 + (m - 1) * _spring(t / ein)
    if direction == "out":
        return m - (m - 1) * _spring(t / eout)
    k = _spring(t / ein) if t < dur - eout else 1 - _spring((t - (dur - eout)) / eout)
    return 1 + (m - 1) * k


def apply_zoom(img, scale, focal_x=0.5, focal_y=0.37):
    H, W = img.shape[:2]
    M = cv2.getRotationMatrix2D((W * focal_x, H * focal_y), 0, scale)
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
