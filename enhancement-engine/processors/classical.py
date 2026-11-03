from PIL import Image, ImageFilter, ImageOps, ImageChops, ImageStat
from .base import Processor

TARGET_LONG_SIDE = {"standard": 1920, "pro": 2560, "4k": 3840}
MAX_SCALE = 4

# Starting points. Every photo is measured and these are tuned per photo.
PRESETS = {
    "standard": dict(exposure=14, brightness=10, contrast=30, highlights=-20, shadows=25,
                     whites=10, blacks=-10, saturation=18, vibrance=40, temperature=5, tint=2,
                     clarity=30, texture=25, sharpness=50, noise=15, dehaze=5, vignette=0,
                     edge=0, floor=45),
    "pro": dict(exposure=10, brightness=8, contrast=50, highlights=-25, shadows=30,
                whites=14, blacks=-18, saturation=30, vibrance=60, temperature=7, tint=3,
                clarity=45, texture=35, sharpness=70, noise=15, dehaze=10, vignette=-10,
                edge=0, floor=60),
    "4k": dict(exposure=6, brightness=4, contrast=38, highlights=-18, shadows=22,
               whites=6, blacks=-8, saturation=20, vibrance=45, temperature=3, tint=0,
               clarity=40, texture=50, sharpness=65, noise=20, dehaze=5, vignette=0,
               edge=40, floor=80),
}

LIMITS = dict(exposure=(-40, 40), brightness=(-30, 30), contrast=(0, 60), highlights=(-40, 10),
              shadows=(0, 45), saturation=(0, 40), vibrance=(0, 70), temperature=(-5, 12),
              clarity=(0, 60), texture=(0, 60), sharpness=(0, 90), noise=(0, 45), dehaze=(0, 20))

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

def analyze(img):
    """Measure the photo with plain image statistics."""
    w, h = img.size
    small = img.copy()
    small.thumbnail((400, 400))
    lum = small.convert("L")
    hist = lum.histogram()
    total = float(sum(hist))

    def pct(q):
        acc = 0
        for i, c in enumerate(hist):
            acc += c
            if acc >= q * total:
                return i
        return 255

    mean = ImageStat.Stat(lum).mean[0] / 255.0
    sat = ImageStat.Stat(small.convert("HSV").split()[1]).mean[0] / 255.0
    rgb = ImageStat.Stat(small).mean
    _, cb, cr = small.convert("YCbCr").split()
    cbm = cb.point(lambda v: 255 if 77 <= v <= 127 else 0)
    crm = cr.point(lambda v: 255 if 133 <= v <= 173 else 0)
    skin = ImageStat.Stat(ImageChops.multiply(cbm, crm)).mean[0] / 255.0
    cw, ch = min(w, 500), min(h, 500)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    crop = img.crop((x0, y0, x0 + cw, y0 + ch)).convert("L")
    return dict(
        mean=mean, lo=pct(0.01), hi=pct(0.99),
        dark=sum(hist[:40]) / total, clip=sum(hist[246:]) / total,
        sat=sat, cast=(rgb[0] - rgb[2]) / (rgb[0] + rgb[2] + 1.0), skin=skin,
        edge=ImageStat.Stat(crop.filter(ImageFilter.FIND_EDGES)).mean[0],
        noise=ImageStat.Stat(ImageChops.difference(crop, crop.filter(ImageFilter.MedianFilter(3)))).mean[0],
        long=max(w, h))

def adapt(a, base):
    p = dict(base)
    notes = []
    d = (0.47 - a["mean"]) * 100
    p["exposure"] += _clamp(d * 0.5, -14, 14)
    p["brightness"] += _clamp(d * 0.3, -10, 10)
    if d > 8:
        notes.append("Brightened a dark photo")
    elif d < -8:
        notes.append("Toned down strong exposure")
    if a["clip"] > 0.03:
        p["highlights"] -= min(20, a["clip"] * 400)
        notes.append("Recovered bright highlights")
    elif a["clip"] < 0.003:
        p["highlights"] *= 0.5
    if a["dark"] > 0.25:
        p["shadows"] += min(20, (a["dark"] - 0.25) * 80)
        notes.append("Opened up deep shadows")
    elif a["dark"] < 0.05:
        p["shadows"] *= 0.5
    rng = a["hi"] - a["lo"]
    if rng < 180:
        p["contrast"] += min(25, (180 - rng) / 3.0)
        p["dehaze"] += min(10, (180 - rng) / 8.0)
        notes.append("Added depth to flat contrast")
    elif rng > 235:
        p["contrast"] *= 0.5
        notes.append("Eased contrast, the tones are already punchy")
    if a["sat"] < 0.25:
        p["vibrance"] += 15
        p["saturation"] += 8
        notes.append("Boosted muted colours")
    elif a["sat"] > 0.5:
        p["vibrance"] *= 0.5
        p["saturation"] *= 0.3
        notes.append("Held colour back, it is already vivid")
    if a["cast"] < -0.04:
        p["temperature"] += min(8, (-0.04 - a["cast"]) * 100)
        notes.append("Warmed a cool colour cast")
    elif a["cast"] > 0.2:
        p["temperature"] -= min(8, (a["cast"] - 0.2) * 100)
        notes.append("Cooled a strong warm cast")
    f = _clamp(1.3 - a["edge"] / 12.0, 0.6, 1.4)
    p["sharpness"] *= f
    p["clarity"] *= f
    if f > 1.1:
        notes.append("Sharpened soft detail")
    elif f < 0.8:
        notes.append("Kept sharpening light, it is already crisp")
    if a["noise"] > 2.5:
        p["noise"] += min(25, (a["noise"] - 2.5) * 10)
        notes.append("Cleaned up noise")
    elif a["noise"] < 1.2:
        p["noise"] *= 0.6
    if a["long"] < 800:
        p["clarity"] *= 0.8
        p["texture"] *= 0.8
        notes.append("Went gentle on detail, the source is small")
    if a["skin"] > 0.08:
        p["saturation"] *= 0.7
        p["vibrance"] *= 0.8
        p["temperature"] = min(p["temperature"], 4)
        p["texture"] *= 0.9
        notes.append("Kept skin tones natural")
    for k, (lo, hi) in LIMITS.items():
        p[k] = _clamp(p[k], lo, hi)
    if not notes:
        notes.append("Already well exposed, applying a light polish")
    return p, notes[:4]

def plan(img, mode):
    return adapt(analyze(img), PRESETS.get(mode, PRESETS["standard"]))

def _tone_lut(p):
    gain = 2 ** (p["exposure"] / 100.0)
    expo = 1.0 - p["brightness"] / 100.0 * 0.6
    c = p["contrast"] / 100.0 * 1.6
    out = []
    for i in range(256):
        y = min(1.0, (i / 255.0) * gain) ** expo
        y += p["shadows"] / 100.0 * 0.8 * 4 * y * (1 - y) ** 2
        y += p["highlights"] / 100.0 * 0.8 * 4 * y * y * (1 - y)
        y += p["whites"] / 100.0 * 1.5 * 4 * (y ** 6) * (1 - y)
        y += p["blacks"] / 100.0 * 1.5 * 4 * y * (1 - y) ** 6
        y = min(1.0, max(0.0, y))
        y = y + c * (y * y * (3 - 2 * y) - y)
        out.append(max(0, min(255, round(y * 255))))
    return out

def _chroma_lut(p):
    sat = 1 + p["saturation"] / 100.0
    vib = p["vibrance"] / 100.0
    out = []
    for i in range(256):
        c = i - 128
        k = sat * (1 + vib * (1 - abs(c) / 128.0))
        out.append(max(0, min(255, round(128 + c * k))))
    return out

def _sharp(ch, radius, pct, thr=0):
    if pct <= 0:
        return ch
    return ch.filter(ImageFilter.UnsharpMask(radius=radius, percent=int(pct), threshold=thr))

class ClassicalProcessor(Processor):
    name = "classical"
    is_ai = False  # measured tone, colour and sharpening. No AI, no face changes.

    def process(self, img, mode, target=None, params=None):
        img = ImageOps.exif_transpose(img).convert("RGB")
        p = dict(params) if params else plan(img, mode)[0]

        n = p["noise"] / 100.0
        y, cb, cr = img.convert("YCbCr").split()
        cb = cb.filter(ImageFilter.GaussianBlur(0.8 + 2.5 * n))
        cr = cr.filter(ImageFilter.GaussianBlur(0.8 + 2.5 * n))
        y = Image.blend(y, y.filter(ImageFilter.MedianFilter(3)), n * 0.5)
        img = Image.merge("YCbCr", (y, cb, cr)).convert("RGB")

        scale = min(MAX_SCALE, (target or TARGET_LONG_SIDE.get(mode, 1920)) / max(img.size))
        if scale > 1:
            if scale > 2:
                img = img.resize((round(img.width * 2), round(img.height * 2)), Image.LANCZOS)
                scale = scale / 2
            img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        long_side = max(img.size)

        y, cb, cr = img.convert("YCbCr").split()
        y = y.point(_tone_lut(p))
        if p["dehaze"]:
            y = Image.blend(y, ImageOps.autocontrast(y, cutoff=0.5), p["dehaze"] * 0.03)
        lut = _chroma_lut(p)
        cb, cr = cb.point(lut), cr.point(lut)

        y = _sharp(y, max(10.0, long_side / 100.0), p["clarity"] * 2.0)
        y = _sharp(y, 2.5 + long_side / 1500.0, p["texture"] * 1.5)
        sh = _sharp(y, 1.0 + long_side / 3000.0, p["sharpness"] * 2.2)
        if p["edge"]:
            sh = _sharp(sh, 0.6, p["edge"] * 1.4, 3)
        fl = p["floor"]
        mask = y.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.5)).point(
            lambda v: min(255, fl + v * 5))
        y = Image.composite(sh, y, mask)

        if p["vignette"]:
            k = 1 + p["vignette"] / 100.0 * 1.5
            rg = Image.radial_gradient("L").resize(y.size, Image.BILINEAR)
            m = rg.point(lambda v: max(0, min(255, (v - 100) * 255 // 155)))
            y = Image.composite(y.point(lambda v: int(v * k)), y, m)

        out = Image.merge("YCbCr", (y, cb, cr)).convert("RGB")
        r, g, b = out.split()
        tk = p["temperature"] / 100.0 * 0.25
        tn = p["tint"] / 100.0 * 0.2
        r = r.point(lambda v: min(255, int(v * (1 + tk))))
        b = b.point(lambda v: min(255, int(v * (1 - tk))))
        g = g.point(lambda v: int(v * (1 - tn)))
        return Image.merge("RGB", (r, g, b))
