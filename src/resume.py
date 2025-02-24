import logging
import io
import asyncio
import time
import json
import uuid
from dotenv import load_dotenv

import pandas as pd
import zipfile
import fitz
from typing import List, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document

from fastapi import APIRouter
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi import File, UploadFile

from src.loader import pdf_to_img64
from src.schemas import TeachingCandidate 
from src.prompts import PARSE_PROMPT
from src.db import vectorstore

router = APIRouter(prefix="/resume", tags=["Resumes"])

logging.basicConfig(
    filename=f'logs/app.log', 
    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()


llm = ChatOpenAI(model="gpt-4o", temperature=0)
model =  PARSE_PROMPT | llm.with_structured_output(TeachingCandidate)


def create_message(images:List[str], content:str | None = None) -> HumanMessage:
    """
    Create a single message with from a list of images with all pages' content
    Args:
        images (`List[str]`): list of base64 encoded images
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

@router.get("/", )
async def search_resume(query:str, filters:dict | None = None, confidence: int = 0.5) -> List[TeachingCandidate]:
    if filters:
        results = await vectorstore.asimilarity_search_with_relevance_scores(query, filter=filters)
    else :
        results = await vectorstore.asimilarity_search_with_relevance_scores(query)
        
    return [json.loads(doc.page_content) for doc, score in results if score > confidence]


@router.post("/", response_model=TeachingCandidate)
async def load_resume(pdf_file: UploadFile = File(...)) -> TeachingCandidate:
    if not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File is not a PDF.")

    logging.info("Starting to process resume")
    pdf_bytes = await pdf_file.read()

    b64_images = pdf_to_img64(fitz.open(stream=pdf_bytes, filename=pdf_file.filename), save=False)
    logging.info("PDF converted to images successfully")

    message = create_message(b64_images)
    candidate = model.invoke({"messages": [message], "schema": TeachingCandidate.model_json_schema()})
    logging.info("Successfully extracted candidate information")

    try:
        await vectorstore.aadd_documents([(
            Document(
                page_content=candidate.model_dump_json(), 
                metadata=json.loads(candidate.model_dump_json())
            )
        )])
        logging.info("Successfully inserted candidate record")
    except Exception as e:
        logging.error(f"Failed to add document to vectorstore: {e}")
        raise HTTPException(status_code=500, detail="Failed to add document to vectorstore", extra={"candidate": candidate})
    
    return candidate    

@router.get("/{resume_id}", )
async def find_resume(resume_id:int) -> TeachingCandidate:
    pass

@router.patch("/{resume_id}", )
async def update_resume(resume_id:int) -> TeachingCandidate:
    pass

@router.delete("/{resume_id}", )
async def delete_resume(resume_id:int) -> None:
    pass

@router.post("/batch")
async def batch_load(zip_file: UploadFile) -> StreamingResponse:
    """
    Batch Process Resumes from ZIP File

    This endpoint accepts a ZIP file containing one or more PDF resumes, 
    extracts relevant candidate information, and returns a CSV file containing 
    the extracted data.

    Args:
        zip_file (UploadFile): A ZIP file containing one or more PDF resumes.

    Returns:
        StreamingResponse: A CSV file containing the extracted candidate information.

    Raises:
        HTTPException: If the uploaded file is not a valid ZIP file, or unable to read it or parse the files.
    """
    
    if not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=422, detail="File is not a ZIP.")
    
    logging.info("Starting batch resume processing")
    try:
        zip_bytes = await zip_file.read()
    except Exception as e:
        logging.error(f"Failed to read ZIP file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read ZIP file.")

    zip_stream = io.BytesIO(zip_bytes)
    pdf_files: List[Tuple[str, bytes]] = []
    try:
        with zipfile.ZipFile(zip_stream) as z:
            for info in z.infolist():
                # NOTE: Only process PDFs (ignoring Word docs for now)
                if info.filename.lower().endswith(".pdf"):
                    pdf_files.append((info.filename, z.read(info.filename)))
    except zipfile.BadZipFile as e:
        logging.error(f"Invalid ZIP file: {e}")
        raise HTTPException(status_code=400, detail="Invalid ZIP file.")
    except Exception as e:
        logging.error(f"Failed to process ZIP file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process ZIP file.")

    logging.info(f"Found {len(pdf_files)} PDF(s) in the zip file.")
    inputs = []
    for filename, pdf_bytes in pdf_files:
        try:
            b64_images = pdf_to_img64(fitz.open(stream=pdf_bytes, filename=filename),zoom=2, save=False)
            logging.info(f"{filename} PDF converted to Images successfully")
        except Exception as e:
            logging.error(f"Failed to convert {filename} to images: {e}")
            continue
        inputs.append({"messages": [create_message(b64_images)], "schema": TeachingCandidate.model_json_schema()})

    logging.info("Converted all PDFs into images. ATS Parsing all PDF files in a batch")
    try:
        outputs: list[TeachingCandidate] = await model.abatch(inputs)
    except Exception as e:
        logging.error(f"Failed to batch process PDFs to Form: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch parse PDFs.")
    
    logging.info("Batch processing complete, upserting to vectorstor.")
    tasks = [] 
    for candidate in outputs:
        tasks.append(vectorstore.aadd_documents([Document(
            page_content=candidate.model_dump_json(),
            metadata=json.loads(candidate.model_dump_json())
        )]))

    await asyncio.gather(*tasks)

    logging.info("Added batch to vectorstore, converting to CSV file.")
    candidate_dicts = [json.loads(candidate.model_dump_json()) for candidate in outputs if hasattr(candidate, "model_dump_json")]
    df = pd.DataFrame(candidate_dicts)
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    logging.info("Added to vectorstore. Returning CSV file.")
    
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=Candidates.csv"}
    )
