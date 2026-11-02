import sys, time, os
from PIL import Image
from processors.classical import ClassicalProcessor

src, mode = sys.argv[1], sys.argv[2]
os.makedirs("out", exist_ok=True)
t = time.time()
p = ClassicalProcessor()
img = Image.open(src)
before = img.size
res = p.process(img, mode)
dst = "out/%s_%s.jpg" % (os.path.splitext(os.path.basename(src))[0], mode)
res.save(dst, quality=95)
print("processor:", p.name, "| AI:", p.is_ai)
print("size:", before, "->", res.size, "| %.1fs" % (time.time() - t))
print("saved:", dst)
