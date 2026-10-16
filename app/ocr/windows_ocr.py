"""Windows built-in OCR (Windows.Media.Ocr) - the same engine PowerToys Text Extractor (Win+Shift+T) uses.
No admin rights, no model files; needs an OCR language pack (English is installed by default)."""
import asyncio, io


async def _run(png: bytes) -> str:
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(png)
    await writer.store_async()
    writer.detach_stream()
    stream.seek(0)
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        from winrt.windows.globalization import Language
        engine = OcrEngine.try_create_from_language(Language("en-US"))
    if engine is None:
        raise RuntimeError("No Windows OCR language installed")
    result = await engine.recognize_async(bitmap)
    return "\n".join(line.text for line in result.lines)


def read(img) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    return asyncio.run(_run(buf.getvalue()))
