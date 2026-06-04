"""SpellBitmaps — loads spell/item icons from BAM resources."""

from PySide6.QtGui import QPixmap, QImage

from ..formats.inf_bam import InfBam


class SpellBitmaps:
    """Manages spell icon loading from BAM resources."""

    def __init__(self, resource_manager):
        self._resource_manager = resource_manager
        self._cache: dict[str, QPixmap] = {}

    def get_icon(self, res_name: str, frame: int = 0) -> QPixmap | None:
        cache_key = f"{res_name}:{frame}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        from ..formats.constants import RESTYPE_BAM
        data = self._resource_manager.get_resource(RESTYPE_BAM, res_name)
        if data is None:
            return None

        bam = InfBam()
        if not bam.read(data):
            return None

        pixels = bam.get_frame_pixels(frame)
        if pixels is None:
            return None

        w, h = bam.get_frame_dimensions(frame)
        if w == 0 or h == 0:
            return None

        image = QImage(w, h, QImage.Format.Format_ARGB32)
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                if idx < len(pixels):
                    r, g, b, a = pixels[idx]
                    image.setPixelColor(x, y, image.pixelColor(x, y).fromRgb(r, g, b, a))

        pixmap = QPixmap.fromImage(image)
        self._cache[cache_key] = pixmap
        return pixmap

    def clear_cache(self):
        self._cache.clear()
