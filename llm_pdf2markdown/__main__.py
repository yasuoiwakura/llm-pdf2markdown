"""CLI entry point."""
import os
import shutil
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from llm_pdf2markdown.client import OllamaClient
from llm_pdf2markdown.pdf import PDFConverter


@click.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--url", default=None, help="Ollama URL")
@click.option("--model", default=None, help="Ollama model")
def main(input: str, url: str | None, model: str | None):
    """Convert PDF to Markdown using Ollama."""
    load_dotenv()

    url = url or os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = model or os.getenv("OLLAMA_MODEL", "gemma3:4b")

    client = OllamaClient(url, model)

    if not client.ping():
        click.echo("Error: Cannot connect to Ollama", err=True)
        sys.exit(1)

    input_path = Path(input)
    output_path = input_path.with_suffix(".md")

    pdf_conv = PDFConverter()
    images = pdf_conv.to_images(input_path)

    click.echo(f"Converting {len(images)} page(s)...")

    parts = []
    for i, img in enumerate(images, 1):
        prompt = "Convert this image to Markdown."
        click.echo(f"  Page {i}/{len(images)}...")
        md = client.generate_with_image(img, prompt)
        parts.append(md)
        shutil.rmtree(img.parent)

    output_path.write_text("\n\n---\n\n".join(parts), encoding="utf-8")
    click.echo(f"Created: {output_path}")


if __name__ == "__main__":
    main()
