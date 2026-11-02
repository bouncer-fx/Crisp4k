from PIL import Image, ImageFilter, ImageOps, ImageEnhance
from .base import Processor

TARGET_LONG_SIDE = {"standard": 1920, "pro": 2560, "4k": 3840}
MAX_SCALE = 4

# dn: denoise blend | gamma: <1 brightens mids | lift: shadow lift
# contrast: S-curve | color: vividness | warm: warmth | clarity/sharp: %
PARAMS = {
    "standard": dict(dn=0.25, gamma=0.93, lift=0.10, contrast=0.30, color=1.12, warm=1.012, clarity=35, sharp=70),
    "pro":      dict(dn=0.30, gamma=0.92, lift=0.12, contrast=0.35, color=1.15, warm=1.014, clarity=50, sharp=100),
    "4k":       dict(dn=0.35, gamma=0.91, lift=0.14, contrast=0.38, color=1.18, warm=1.016, clarity=65, sharp=130),
}

def _lut(gamma, lift, contrast):
    out = []
    for i in range(256):
        x = i / 255.0
        y = x ** gamma
        y = y + lift * 4 * y * (1 - y) ** 2          # lift shadows, keep black and white points
        s = y * y * (3 - 2 * y)
        y = (1 - contrast) * y + contrast * s        # gentle S-curve
        out.append(max(0, min(255, round(y * 255))))
    return out

class ClassicalProcessor(Processor):
    name = "classical"
    is_ai = False  # tone mapping + filters, NOT super-resolution

    def process(self, img, mode):
        p = PARAMS.get(mode, PARAMS["standard"])
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = Image.blend(img, img.filter(ImageFilter.MedianFilter(3)), p["dn"])
        img = Image.blend(img, ImageOps.autocontrast(img, cutoff=0.3), 0.5)
        img = img.point(_lut(p["gamma"], p["lift"], p["contrast"]) * 3)
        img = ImageEnhance.Color(img).enhance(p["color"])
        w = p["warm"]
        r, g, b = img.split()
        r = r.point(lambda v: min(255, int(v * w)))
        b = b.point(lambda v: int(v * (2 - w)))
        img = Image.merge("RGB", (r, g, b))
        scale = min(MAX_SCALE, TARGET_LONG_SIDE.get(mode, 1920) / max(img.size))
        if scale > 1:
            if scale > 2:
                img = img.resize((round(img.width * 2), round(img.height * 2)), Image.LANCZOS)
                scale = scale / 2
            img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=30, percent=p["clarity"], threshold=0))
        y, cb, cr = img.convert("YCbCr").split()
        sharp = y.filter(ImageFilter.UnsharpMask(radius=1.1, percent=p["sharp"] * 2, threshold=0))
        mask = y.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.5)).point(lambda v: min(255, v * 6))
        y = Image.composite(sharp, y, mask)
        return Image.merge("YCbCr", (y, cb, cr)).convert("RGB")
