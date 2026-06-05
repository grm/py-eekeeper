"""SpellBitmaps — loads spell/item icons from BAM resources."""

import struct

from PySide6.QtGui import QPixmap, QImage

from ..formats.inf_bam import InfBam


class SpellBitmaps:
    """Manages spell and item icon loading from BAM resources."""

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

        pixmap = self._bam_to_pixmap(data, frame)
        if pixmap:
            self._cache[cache_key] = pixmap
        return pixmap

    def get_item_icon(self, item_res_name: str) -> QPixmap | None:
        cache_key = f"itm:{item_res_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        from ..formats.constants import RESTYPE_ITM, RESTYPE_BAM
        itm_data = self._resource_manager.get_resource(RESTYPE_ITM, item_res_name)
        if not itm_data or len(itm_data) < 0x42:
            return None

        bam_name = itm_data[0x3A:0x42].decode("latin-1").rstrip("\x00")
        if not bam_name:
            return None

        bam_data = self._resource_manager.get_resource(RESTYPE_BAM, bam_name)
        if not bam_data:
            return None

        pixmap = self._bam_to_pixmap(bam_data, 0)
        if pixmap:
            self._cache[cache_key] = pixmap
        return pixmap

    def _bam_to_pixmap(self, data: bytes, frame: int) -> QPixmap | None:
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

        return QPixmap.fromImage(image)

    def clear_cache(self):
        self._cache.clear()
