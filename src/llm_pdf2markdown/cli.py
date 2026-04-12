#!/usr/bin/env python3
import click
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from llm_pdf2markdown.ollama_client import OllamaClient
from llm_pdf2markdown.pdf_converter import PDFConverter


@click.group()
def cli():
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--model", help="Override Ollama model")
@click.option("--url", help="Override Ollama URL")
def pdf(path: str, model: str | None, url: str | None):
    load_dotenv()

    url = url or os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = model or os.getenv("OLLAMA_MODEL", "gemma3:4b")
    output_dir = os.getenv("OUTPUT_DIR", "")

    client = OllamaClient(url, model)
    
    if not client.check_connection():
        click.echo(f"Error: Cannot connect to Ollama at {url}", err=True)
        sys.exit(1)

    converter = PDFConverter(client)
    result = converter.convert(Path(path), output_dir if output_dir else None)

    if result.success:
        click.echo(f"Created: {result.output_path}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--model", help="Override Ollama model")
@click.option("--url", help="Override Ollama URL")
def batch(directory: str, model: str | None, url: str | None):
    load_dotenv()

    url = url or os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = model or os.getenv("OLLAMA_MODEL", "gemma3:4b")
    output_dir = os.getenv("OUTPUT_DIR", "")

    client = OllamaClient(url, model)

    if not client.check_connection():
        click.echo(f"Error: Cannot connect to Ollama at {url}", err=True)
        sys.exit(1)

    converter = PDFConverter(client)
    pdf_files = list(Path(directory).rglob("*.pdf"))

    if not pdf_files:
        click.echo("No PDF files found.")
        return

    click.echo(f"Found {len(pdf_files)} PDF(s)")

    success = 0
    failed = 0

    for pdf_path in pdf_files:
        result = converter.convert(pdf_path, output_dir if output_dir else None)
        if result.success:
            click.echo(f"  ✓ {pdf_path.name} -> {result.output_path}")
            success += 1
        else:
            click.echo(f"  ✗ {pdf_path.name}: {result.error}")
            failed += 1

    click.echo(f"\nDone: {success} succeeded, {failed} failed")


def main():
    cli()
