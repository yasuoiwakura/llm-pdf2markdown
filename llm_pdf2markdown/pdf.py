"""Convert PDF pages to images."""
import pypdfium2 as pdfium
from pathlib import Path
from tempfile import TemporaryDirectory


class PDFConverter:
    def __init__(self, scale: float = 2.0):
        self.scale = scale

    def to_images(self, pdf_path: Path) -> list[Path]:
        """Convert PDF to list of PNG image paths."""
        pdf = pdfium.PdfDocument(str(pdf_path))
        images = []

        with TemporaryDirectory() as tmpdir:
            for i, page in enumerate(pdf):
                image = page.render(pdfium.PdfBitmap.to_pil, scale=self.scale)
                path = Path(tmpdir) / f"page_{i+1:03d}.png"
                image.save(path, "PNG")
                images.append(path)

        return images
