import cv2, numpy as np
from PIL import Image

def preprocess(img: Image.Image, enhance=False) -> np.ndarray:
    a = np.array(img.convert("RGB"))
    h, w = a.shape[:2]
    if h < 400 and w <= 1600:   # small crops: 2x upscale gives clearer words and spacing
        a = cv2.resize(a, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    if enhance:
        g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
        g = cv2.createCLAHE(2.0, (8, 8)).apply(g)
        a = cv2.cvtColor(g, cv2.COLOR_GRAY2RGB)
    return a
