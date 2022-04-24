from PIL import Image
from io import BytesIO
import logging

_logger = logging.getLogger(f"INGEST.{__name__}")


class StaticImage:
    data: Image.Image = None
    title: str = None

    def __init__(self, data: Image.Image, title: str = None):
        self.data = data
        self.title = title

    def save_io(self):
        b = BytesIO()
        _logger.debug("Save Image to BytesIO")
        self.data.save(b, format=self.data.format)
        b.seek(0)
        return b
