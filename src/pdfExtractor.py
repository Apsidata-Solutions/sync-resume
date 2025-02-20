import base64
import io
import os
from pathlib import Path
import fitz
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from typing import List


def save_page_as_png(page, dir_path: str, page_number: int, zoom: int) -> str:
    """Save a single PDF page as PNG file."""
    image_path = os.path.join(dir_path, f"Page_{page_number}.png")
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(image_path)
    print(f"Saving page @ {image_path}")
    return image_path


def convert_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    buffer = io.BytesIO()
    with Image.open(image_path) as img:
        img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def process_pdf_pages(pdf_document, dir_path: str, zoom: int) -> list:
    """Process all pages in PDF and return list of base64 strings."""
    output_images = []

    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        image_path = save_page_as_png(page, dir_path, page_number, zoom)
        base64_string = convert_image_to_base64(image_path)
        output_images.append(base64_string)

    return output_images


def transformer_base64(pdf_path: str, zoom: int = 8) -> list:
    """
    Convert PDF pages to PNG images and return their base64 representations.

    Args:
        pdf_path (str): Path to the PDF file
        zoom (int): Zoom factor for resolution (default=8)

    Returns:
        list: List of base64 strings, one for each page
    """
    """Create a unique directory based on PDF filename."""
    base_path = Path("./data") / Path(pdf_path).stem
    dir_path = base_path
    counter = 1

    while os.path.exists(dir_path):
        dir_path = f"{base_path}({counter})"
        counter += 1

    os.makedirs(dir_path)

    try:
        pdf_document = fitz.open(pdf_path)
        return process_pdf_pages(pdf_document, dir_path, zoom)
    finally:
        pdf_document.close()


def pdf_to_base64(page: fitz.Page, zoom: int = 8) -> str:
    """Convert a single PDF page directly to base64 string without saving to disk."""
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    # Convert pixmap to PIL Image directly in memory
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Convert to base64 string directly in memory
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def process_pdf(pdf_path: str, zoom: int = 8) -> List[str]:
    """Process PDF pages in parallel and return list of base64 strings."""
    with fitz.open(pdf_path) as pdf_document:
        with ThreadPoolExecutor() as executor:
            # Process pages in parallel
            futures = [
                executor.submit(pdf_to_base64, page, zoom) for page in pdf_document
            ]
            return [future.result() for future in futures]
