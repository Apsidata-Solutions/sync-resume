import base64
from pathlib import Path
from PIL import Image
import fitz
import io
from langchain_core.messages import HumanMessage

def pdfpath_to_img64(pdf_path: str, save: bool = False, zoom: int = 8) -> list[str]:
    """
    Convert each page of the PDF to a base64-encoded PNG string.
    
    If save=True, the PNG images are also saved to a unique directory.
    
    Args:
        pdf_path (str): Path to the PDF file.
        save (bool): Whether to save the PNG files to disk. Defaults to False.
        zoom (int): Zoom factor for higher resolution. Defaults to 8.
    
    Returns:
        list: List of base64 strings (one per PDF page).
    """
    output_dir = None

    # Create a unique directory if saving files.
    if save:
        base_dir = Path("./data") / Path(pdf_path).stem
        output_dir = base_dir
        counter = 1
        while output_dir.exists():
            output_dir = Path(f"{base_dir}({counter})")
            counter += 1
        output_dir.mkdir(parents=True)

    with fitz.open(pdf_path) as pdf:
        base64_images=pdf_to_img64(pdf, zoom, save, output_dir)
        
    return base64_images

def pdf_to_img64(pdf:fitz.Document, zoom:int =  8, save:bool=False, output_dir: Path | None = None):
    base64_images = []
    for i, page in enumerate(pdf):
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        if save:
            img_path = output_dir / f"Page_{i}.png"
            pix.save(str(img_path))
            # Read the saved file into memory.
            with open(img_path, "rb") as f:
                img_data = f.read()
        else:
            # Convert directly in memory.
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_data = buffer.getvalue()

        base64_images.append(base64.b64encode(img_data).decode("utf-8"))

    return base64_images

def create_message(images:list[str], content:str | None = None) -> HumanMessage:
    """
    Create a single message with from a list of images with all pages' content
    Args:
        images (`list[str]`): list of base64 encoded images
        content (`str | None`): Any additional content the user wants to add with the images. Defaults to `None`
    Returns:
        message: `HumanMessage` : Langchain `HumanMessage` interface with the images padded with the content or some sample content
    """

    content = [
        {
            "type": "text",
            "text": content if content else "Extract all relevant information from these pages of the PDF. Provide a comprehensive analysis combining information from all pages.",
        }
    ]

    # Add each page as an image
    for page_num, page_image in enumerate(images):
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{page_image}"},
            }
        )
    return HumanMessage(content=content)
