from PIL import Image, ImageFilter, ImageOps, ImageEnhance
from .base import Processor

TARGET_LONG_SIDE = {"standard": 1920, "pro": 2560, "4k": 3840}
MAX_SCALE = 4
# (denoise blend, contrast, color, clarity %, fine sharpen %)
STRENGTH = {
    "standard": (0.30, 1.06, 1.08, 45, 90),
    "pro": (0.35, 1.09, 1.12, 65, 130),
    "4k": (0.40, 1.12, 1.16, 90, 190),
}

class ClassicalProcessor(Processor):
    name = "classical"
    is_ai = False  # resizing + filters, NOT super-resolution

    def process(self, img, mode):
        dn, ct, co, clar, fine = STRENGTH.get(mode, STRENGTH["standard"])
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = Image.blend(img, img.filter(ImageFilter.MedianFilter(3)), dn)
        img = Image.blend(img, ImageOps.autocontrast(img, cutoff=0.5), 0.6)
        img = ImageEnhance.Contrast(img).enhance(ct)
        img = ImageEnhance.Color(img).enhance(co)
        scale = min(MAX_SCALE, TARGET_LONG_SIDE[mode] / max(img.size))
        if scale > 1:
            if scale > 2:
                img = img.resize((round(img.width * 2), round(img.height * 2)), Image.LANCZOS)
                scale = scale / 2
            img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=25, percent=clar, threshold=2))
        img = img.filter(ImageFilter.UnsharpMask(radius=1.4, percent=fine, threshold=3))
        return img
