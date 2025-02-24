import logging

from fastapi import FastAPI
from fastapi import Request, HTTPException
import uvicorn

from resume import router

logging.basicConfig(
    filename=f'logs/app.log', 
    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI()
app.include_router(router)

@app.get("/health")
async def health_check(request: Request):
    logging.info("Health check request received")
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