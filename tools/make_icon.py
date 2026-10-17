"""Turns your picture into assets/icon.ico (exe icon) and assets/icon.png (tray icon).
Put your image in assets/ named icon.png (or icon.jpg / icon.jpeg / icon.webp / icon.bmp), then build.
With no image, a default blue 'AI' icon is generated."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

A = Path(__file__).resolve().parent.parent / "assets"
A.mkdir(exist_ok=True)
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def default_icon() -> Image.Image:
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, 248, 248), radius=56, fill=(0, 120, 215, 255))
    try:
        f = ImageFont.load_default(size=120)
    except TypeError:
        f = ImageFont.load_default()
    d.text((128, 128), "S", font=f, fill="white", anchor="mm")
    return im


src = next((p for e in ("png", "jpg", "jpeg", "webp", "bmp") for p in [A / f"icon.{e}"] if p.exists()), None)
if src:
    img = Image.open(src).convert("RGBA")
    side = max(img.size)                                  # pad to a square, keep transparency
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    img = sq.resize((256, 256), Image.LANCZOS)
    print("Using", src.name)
else:
    img = default_icon()
    print("No assets/icon.* image found - using the default icon")

img.save(A / "icon.ico", format="ICO", sizes=SIZES)
try:
    img.save(A / "icon.icns")                             # macOS app icon
except Exception:
    pass
if not (src and src.suffix.lower() == ".png"):
    img.save(A / "icon.png")                              # tray icon
print("Created assets/icon.ico")
