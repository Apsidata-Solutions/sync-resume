import logging
import io
import os
import base64
import asyncio
import json
import uuid
from dotenv import load_dotenv

import pandas as pd
import zipfile
import fitz
from typing import List, Tuple, Optional, Union

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from fastapi import File, UploadFile

from src.utils.loader import pdf_to_img64, create_message
from src.outputs import TeachingCandidate 
from src.schemas import ResumeUploadResponse
from src.agents import CandidateAgent

router = APIRouter(prefix="/resume", tags=["Resumes"])

logger = logging.getLogger(__name__)
load_dotenv()


#FIXME: Clean the database wrong state name data
@router.post("/search")
async def search_resume(query:str, filters:dict = None, confidence: float = 0.3)-> List[ResumeUploadResponse]:
    pass

@router.post("/zip")
async def get_resumes(ids: list[str]):
    """
    Return a Zip file of the resumes whose ids are provided in the query parameter.
    """
    # Create a unique filename for the zip
    zip_filename = f"resumes_{uuid.uuid4()}.zip"
    zip_buffer = io.BytesIO()
    
    # Create the zip file in memory
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for id in ids:
            try:
                file_path = f"./static/resume/{id}.pdf"
                if os.path.exists(file_path):
                    zip_file.write(file_path, f"{id}.pdf")
                else:
                    logger.warning(f"Resume file not found for ID: {id}")
            except Exception as e:
                logger.error(f"Error adding file to zip for ID {id}: {e}")
    
    # Reset buffer position to the beginning
    zip_buffer.seek(0)
    
    # Return the zip file as a streaming response
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )

@router.post("/batch")
async def batch_load(ids: Optional[List[str]] = None, zip_file: UploadFile = File(...)) -> List[ResumeUploadResponse]:
    """
    Batch Process Resumes from ZIP File

    This endpoint accepts a ZIP file containing one or more PDF resumes, 
    extracts relevant candidate information, and returns a list of ResumeUploadResponse objects.

    Args:
        id (Optional[List[str]]): A list of IDs for the resumes.
        zip_file (UploadFile): A ZIP file containing one or more PDF resumes.

    Returns:
        List[ResumeUploadResponse]: A list of ResumeUploadResponse objects containing the extracted candidate information.
    Raises:
        HTTPException: If the uploaded file is not a valid ZIP file, or unable to read it or parse the files.
    """

    if not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=422, detail="Not a ZIP file.")    
    
    logger.info("Starting batch resume processing")
    try:
        zip_bytes = await zip_file.read()
    except Exception as e:
        logger.error(f"Failed to read ZIP file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read ZIP file.")

    response = []
    resumes = {}
    
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for i, info in enumerate(z.infolist()):
                id = "cand-"+str(uuid.uuid4())
                r = {
                    "id": id,
                    "resume_url": f"/static/resume/{id}.pdf",
                }
                with open("."+r["resume_url"], "wb") as f:
                    f.write(z.read(info.filename))

                resumes[id] = z.read(info.filename)

                if info.filename.lower().endswith(".pdf"):
                    r["status"] = "pending"

                else:
                    # Mark non-PDF files as cancelled
                    r["status"] = "cancelled"
                    r["error"] = "File is not a PDF"
                
                response.append(r)
    except zipfile.BadZipFile as e:
        logger.error(f"Invalid ZIP file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid ZIP file.")
    except Exception as e:
        logger.error(f"Failed to process ZIP file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process ZIP file.")
    
    logger.info(f"Found {len(response)} PDF(s) in the zip file.")
    inputs = []
    for r in response:
        if r["status"] != "pending":
            continue
        try:
            inputs.append({
                "messages": [create_message(
                    pdf_to_img64(
                        fitz.open(
                            stream=resumes[r["id"]], 
                            filename=r["resume_url"]
                        ),zoom=2, save=False
                    )
                )], 
                "schema": TeachingCandidate.model_json_schema(),
                "id": r["id"]
            })            
            logger.info(f"{r['resume_url']} PDF converted to Images successfully")
        except Exception as e:
            r["status"] = "failed"
            r["error"] = f"Failed to convert {r['resume_url']} to images: {e}"
            logger.error(f"Failed to convert {r['resume_url']} to images: {e}")
            continue

    logger.info("Converted PDFs into images. ATS Parsing all PDF files in a batch")
    try:
        outputs: list = await CandidateAgent.abatch(inputs)
    except Exception as e:
        logger.error(f"Failed to batch process PDFs to Form: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch parse PDFs.")
    
    logger.info("Batch processing complete, upserting to vectorstor.")
    # try:
    #     docs = await vectorstore.aadd_documents([
    #         Document(
    #             page_content=json.dumps(output["candidate"][-1]), 
    #             metadata=output["candidate"][-1]
    #         )
    #         for output in outputs
    #     ])
    # except Exception as e:
    #     logger.error(f"Failed to add document to vectorstore: {e}")
    # logger.info("Added batch to vectorstore, returning the list of candidates.")
    
    output_map = {output["id"]: output for output in outputs}
    
    for r in response:
        r.pop("resume") if "resume" in r else None
        if r["id"] in output_map:
            output = output_map[r["id"]]
            if output.get("candidate"):
                r["status"] = "success"
                r["candidate"] = output["candidate"][-1]
            else:
                r["status"] = "failed"
                r["error"] = f"Failed to extract information for candidate {output['id']} after {output['iteration']} iterations"

    logger.debug(f"File response: {len(response)}")
    try:
        logger.debug([ResumeUploadResponse(**r) for r in response])
    except Exception as e:
        logger.error(f"Failed to create ResumeUploadResponse: {e}")
    return response

@router.delete("/batch")
async def delete_resumes(ids: list[str]):
    """
    Delete multiple resumes by their IDs
    
    Args:
        ids (list[str]): List of resume IDs to delete
        
    Returns:
        dict: Contains status for each resume ID and summary statistics
    """
    response = []
    
    for id in ids:
        try:
            if os.path.exists(f"./static/resume/{id}.pdf"):
                os.remove(f"./static/resume/{id}.pdf")
                response.append({
                    "id": id, 
                    "status": "success",
                    "message": "Resume deleted successfully"
                })
            else:
                logger.warning(f"Resume file not found: {id}")
                response.append({
                    "id": id, 
                    "status": "failure",
                    "message": "File not found"
                })
        except Exception as e:
            logger.error(f"Failed to delete resume {id}: {str(e)}")
            response.append({
                "id": id, 
                "status": "failure",
                "message": f"Error deleting file: {str(e)}"
            })
    
    return response

@router.get("/{resume_id}", )
async def find_resume(resume_id:int) :
    return f"GET endpoint development in progress ID: {resume_id}"

@router.patch("/{resume_id}", )
async def update_resume(resume_id:int) :
    return f"POST endpoint development in progress ID: {resume_id}"

@router.delete("/{resume_id}", )
async def delete_resume(resume_id:str):
    try:
        if os.path.exists(f"./static/resume/{resume_id}.pdf"):
            os.remove(f"./static/resume/{resume_id}.pdf")
        else:
            logger.warning(f"Resume file not found: {resume_id}")
            return {"id": resume_id, "status": "failure", "message": "Resume file not found"}
    except Exception as e:
        logger.error(f"Failed to delete resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete resume.")
    return {"id": resume_id, "status": "success", "message": "Resume deleted successfully"}

@router.post("/", response_model=ResumeUploadResponse)
async def load_resume(id: Optional[str] = None, pdf_file: UploadFile = File(...)) -> ResumeUploadResponse:
    if not id:
        id = "cand-" + str(uuid.uuid4())
        
    if not pdf_file.filename.lower().endswith(".pdf"):
        return ResumeUploadResponse(
            status="failure",
            id=id,
            error="Unsupported file type. Only PDFs are accepted."
        )
    logger.info(f"Starting to process resume {id}")
    try:
        pdf_bytes = await pdf_file.read()
        with open(f"./static/resume/{id}.pdf", "wb") as f:
            f.write(pdf_bytes)
    except Exception as e:
        logger.error(f"Failed to read PDF file: {e}")
        return ResumeUploadResponse(
            status="failure",
            id=id,
            error="Failed to read PDF file."
        )
    
    try:
        b64_images = pdf_to_img64(fitz.open(stream=pdf_bytes, filename=pdf_file.filename), save=False)
        logger.info("PDF converted to images successfully")
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        return ResumeUploadResponse(
            status="failure",
            id=id,
            error="Failed to convert PDF to images."
        )

    try:
        output = CandidateAgent.batch([{
            "messages": [create_message(b64_images)], 
            "schema": TeachingCandidate.model_json_schema(),
            "id": id
        }])[0]
        if output.get("candidate"):
            logger.info("Successfully extracted candidate information")
        else:
            logger.error(f"Failed to extract candidate information: {output.get('error')}")
            return ResumeUploadResponse(
                status="failure",
                id=id,
                error=f"Failed to extract information for candidate {output['id']} after {output['iteration']} iterations"
            )
    except Exception as e:
        logger.error(f"Failed to extract candidate information: {e}")
        return ResumeUploadResponse(
            status="failure",
            id=id,
            error="Failed to extract candidate information."
        )
    
    # try:
    #     await vectorstore.aadd_documents([(
    #         Document(
    #             page_content=json.dumps(output["candidate"][-1]), 
    #             metadata=output["candidate"][-1]
    #         )
    #     )])
    #     logger.info("Successfully inserted candidate record")

    # except Exception as e:
    #     logger.warning(f"Failed to add document to vectorstore: {e}")
    
    return ResumeUploadResponse(
        status="success",
        id=output["id"], 
        candidate=output["candidate"][-1], 
        resume_url=f"/static/resume/{id}",
    ) 

@router.post("/cron/email")
async def cron_job() -> List[TeachingCandidate]:
    """
    """
    pass
