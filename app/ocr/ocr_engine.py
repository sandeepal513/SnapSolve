import re
from PIL import Image
from app.ocr.image_processor import preprocess
from app.utils.logger import get_logger

log = get_logger()

try:
    import wordninja
except Exception:
    wordninja = None


def fix_spaces(line: str) -> str:
    """Fallback OCR sometimes drops spaces ('Hierarchiesindimensionalmodels'). Re-insert them,
    but only on lines that clearly have giant glued tokens, so normal text is never touched."""
    if not wordninja or max((len(t) for t in re.findall(r"[A-Za-z]+", line)), default=0) < 18:
        return line
    line = re.sub(r"(?<=[a-z])(?=[A-Z]{2,})", " ", line)          # ...inOLAP -> ...in OLAP
    line = re.sub(r"\b([A-Z]{2,})([a-z]{3,})\b", r"\1 \2", line)   # OLAPqueries -> OLAP queries

    def seg(m):
        parts = wordninja.split(m.group(0))
        if len(parts) > 1 and len(parts[-1]) == 1 and parts[-1].lower() not in ("a", "i"):
            parts = parts[:-1]                                      # stray icon read as a letter
        ok = all(len(p) >= 2 or p.lower() in ("a", "i") for p in parts)
        return " ".join(parts) if ok else m.group(0)
    return re.sub(r"[A-Za-z]{10,}", seg, line)


class OCRError(Exception):
    pass


class OCREngine:
    def __init__(self):
        self._eng = None
        self._win_ok = True

    def read(self, img, enhance=False) -> str:
        if self._win_ok:                          # 1) Windows built-in OCR (most accurate)
            try:
                from app.ocr import windows_ocr
                big = img
                if img.height < 400 and img.width <= 1600:   # small crops read better enlarged
                    big = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
                text = windows_ocr.read(big)
                if text.strip():
                    return text
            except (ImportError, RuntimeError) as e:
                log.info("Windows OCR unavailable (%s); using fallback", e)
                self._win_ok = False
            except Exception as e:
                log.info("Windows OCR failed once (%s: %s)", type(e).__name__, e)
        return self._read_rapid(img, enhance)     # 2) RapidOCR fallback

    def _read_rapid(self, img, enhance) -> str:
        try:
            if self._eng is None:
                from rapidocr_onnxruntime import RapidOCR
                self._eng = RapidOCR()
            result, _ = self._eng(preprocess(img, enhance))
        except Exception as e:
            raise OCRError("Could not read text. Please select a clearer area.") from e
        if not result:
            return ""
        items = []                                # (center_y, left_x, height, text)
        for box, text, _score in result:
            ys, xs = [p[1] for p in box], [p[0] for p in box]
            items.append(((min(ys) + max(ys)) / 2, min(xs), max(ys) - min(ys), text))
        items.sort()
        lines = []                                # group boxes that sit on the same visual line
        for cy, x, h, t in items:
            if lines and abs(cy - lines[-1]["cy"]) < 0.5 * max(h, lines[-1]["h"]):
                lines[-1]["parts"].append((x, t))
            else:
                lines.append({"cy": cy, "h": h, "parts": [(x, t)]})
        return "\n".join(fix_spaces(" ".join(t for _, t in sorted(l["parts"]))) for l in lines)
