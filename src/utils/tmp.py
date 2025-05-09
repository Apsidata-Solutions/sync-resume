from agents.classify import agent, model
from src.utils.emailer import fetch_emails, DEFAULT_CREDENTIALS
from src.routes.resume import load_resume
import httpx

start_date = "27-Feb-2025"
from fastapi import UploadFile
def cron_job(start_date, credentials=None):
    
    all_emails = fetch_emails(start_date, max_emails=1)
    print("Fetched all emails")
    inputs= [{"email":str(email)} for email in all_emails]
    outputs= model.batch(inputs)
    print("Received Outputs")

    for idx, output in enumerate(outputs):
        all_emails[idx].type = output

    candidates=[]

    for my_email in all_emails:
        if my_email.type.type != 'candidate':
            pass
        attachment = my_email._attachments[0]
        upload_file = UploadFile(
            filename=attachment["filename"],
            file=attachment["content"],
            content_type=attachment["content_type"]
        )
        candidates.append(load_resume(upload_file))
    
    return candidates

print(cron_job('27-Feb-2025'))    