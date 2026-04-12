import pypdfium2 as pdfium
from pathlib import Path
from dataclasses import dataclass

from llm_pdf2markdown.ollama_client import OllamaClient, OllamaResponse


PROMPT = """Convert this image to Markdown. Preserve the structure:
- Use # for headings
- Use ``` for code blocks
- Use | for tables
- Extract all readable text
- Keep formatting as close to original as possible
"""


@dataclass
class ConvertResult:
    success: bool
    output_path: Path | None = None
    error: str | None = None


class PDFConverter:
    def __init__(self, client: OllamaClient):
        self.client = client

    def convert(self, pdf_path: Path, output_dir: Path | None = None) -> ConvertResult:
        try:
            images = self._pdf_to_images(pdf_path)
        except Exception as e:
            return ConvertResult(success=False, error=f"PDF conversion failed: {e}")

        if not images:
            return ConvertResult(success=False, error="No pages extracted")

        markdown_parts = []

        for i, img_path in enumerate(images, 1):
            response = self.client.send_image(img_path, PROMPT)
            if not response.success:
                return ConvertResult(success=False, error=f"Page {i}: {response.error}")
            markdown_parts.append(response.markdown or "")

        markdown = "\n\n---\n\n".join(markdown_parts)
        output_path = self._get_output_path(pdf_path, output_dir)
        output_path.write_text(markdown, encoding="utf-8")

        for img_path in images:
            img_path.unlink()

        return ConvertResult(success=True, output_path=output_path)

    def _pdf_to_images(self, pdf_path: Path) -> list[Path]:
        pdf = pdfium.PdfDocument(str(pdf_path))
        renderer = pdf.render(
            pdfium.PdfBitmap.to_pil,
            scale=2.0,
        )

        temp_dir = pdf_path.parent / ".temp_images"
        temp_dir.mkdir(exist_ok=True)

        image_paths = []
        for i, image in enumerate(renderer):
            img_path = temp_dir / f"{pdf_path.stem}_page_{i+1:03d}.png"
            image.save(img_path, "PNG")
            image_paths.append(img_path)

        return image_paths

    def _get_output_path(self, pdf_path: Path, output_dir: Path | None) -> Path:
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir / f"{pdf_path.stem}.md"
        return pdf_path.with_suffix(".md")
