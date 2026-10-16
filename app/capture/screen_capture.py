from PIL import Image

def pixmap_to_pil(pm) -> Image.Image:
    """QPixmap -> PIL. Qt grabs at native resolution, so it is DPI/multi-monitor safe."""
    from PySide6.QtGui import QImage
    img = pm.toImage().convertToFormat(QImage.Format_RGBA8888)
    return Image.frombytes("RGBA", (img.width(), img.height()), img.bits().tobytes()).convert("RGB")
