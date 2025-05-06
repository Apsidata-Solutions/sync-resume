import os
from dotenv import load_dotenv
import logging

from fastapi import FastAPI
from fastapi import Request
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.routes import resume_router

# Configure root logger with different settings for production and development
load_dotenv()

if os.getenv("MODE", "DEVELOPMENT") == "PRODUCTION":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
        ]
    )
else:  # development mode
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

# Get logger for this module
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(resume_router, prefix="/v1")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check(request: Request):
    logger.info("Health check request received")
    return {
        "status": "UP",
        "metadata": {
            "request_ip": request.client.host,
            "request_method": request.method,
            "request_path": request.url.path
        },
    }

if "__name__"=="__main__":
    uvicorn.run(app, host= "0.0.0.0", port=8000 )