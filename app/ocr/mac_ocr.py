"""macOS built-in OCR (Apple Vision framework). No downloads, no admin rights."""
import io


def _join(items):
    """items: (center_y, left_x, height, text). Vision's y axis points up, so top = largest y."""
    items = sorted(items, key=lambda t: -t[0])
    lines = []
    for cy, x, h, text in items:                  # merge boxes that sit on the same visual line
        if lines and abs(cy - lines[-1]["cy"]) < 0.5 * max(h, lines[-1]["h"]):
            lines[-1]["parts"].append((x, text))
        else:
            lines.append({"cy": cy, "h": h, "parts": [(x, text)]})
    return "\n".join(" ".join(t for _, t in sorted(l["parts"])) for l in lines)


def read(img) -> str:
    import Vision
    from Foundation import NSData

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    raw = buf.getvalue()
    data = NSData.dataWithBytes_length_(raw, len(raw))
    handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(data, {})
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    req.setUsesLanguageCorrection_(True)
    ok, err = handler.performRequests_error_([req], None)
    if not ok:
        raise RuntimeError(f"Vision OCR failed: {err}")
    items = []
    for obs in (req.results() or []):
        cands = obs.topCandidates_(1)
        if cands:
            b = obs.boundingBox()
            items.append((b.origin.y + b.size.height / 2, b.origin.x, b.size.height, str(cands[0].string())))
    return _join(items)
