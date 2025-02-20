from dotenv import load_dotenv

from fastapi import FastAPI
import uvicorn

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from loader import transformer_base64
from schemas import Candidate
from prompts import PARSE_PROMPT
app = FastAPI()


# Candidate.model_dump()
load_dotenv()


llm = ChatOpenAI(model="gpt-4o", temperature=0)
model =  PARSE_PROMPT | llm.with_structured_output(Candidate)

from fastapi.responses import StreamingResponse
import io
import csv
import pandas as pd
from typing import List
from fastapi import File, UploadFile

@app.post("/batch-load")
async def batch_load(zip_file: UploadFile = File(...)):
    # Extract resumes from zip file
    resumes = await extract_resumes_from_zip(zip_file)
    
    # Load each resume into a candidate object
    candidates = []
    for resume in resumes:
        candidate = await load_resume(resume)
        candidates.append(candidate)
    
    # Convert list of candidates to a dataframe
    df = pd.DataFrame(candidates)
    
    # Convert dataframe to a CSV file
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(io.TextIOWrapper(output, newline=""), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=resumes.csv"})

async def extract_resumes_from_zip(zip_file: UploadFile):
    # TO DO: implement extracting resumes from zip file
    pass


   

@app.post("/resume-loader", response_model=Candidate)
async def load_resume(pdf_file):
    # pdf_file ="data/CV for TGT/1 - Mahalakshmi jaiswal  - Primary teacher - 2 Yrs 7 Months.pdf"

    b64_images = transformer_base64(pdf_file, save=False)
    response = extract_candidate(b64_images)
    return response    


def extract_candidate(images: list[str]) -> Candidate:
    # Create a single message with all pages
    content = [
        {
            "type": "text",
            "text": "Extract all relevant information from these pages of the PDF. Provide a comprehensive analysis combining information from all pages.",
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

    # logger.info("Processing all PDF pages")

    output = model.invoke({"messages": [HumanMessage(content=content)],"schema":Candidate.model_json_schema()})
    # logger.info("Successfully processed PDF")
    return output

@app.get("/health")
def health_check():
    return {"status":"Healh Ok"}



if "__name__"=="__main__":
    uvicorn.run(app, host= "0.0.0.0", port=8000 )