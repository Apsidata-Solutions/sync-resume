import mimetypes
import os
from datetime import datetime
from typing import Literal

import hashlib
from pathlib import Path

import imaplib
import email
from email.header import decode_header

from agents.classify import EmailType

DEFAULT_CREDENTIALS = {
    "host":os.environ["EDUCARE_EMAIL_HOST"],
    "username":os.environ["EDUCARE_EMAIL_USERNAME"],
    "password":os.environ["EDUCARE_EMAIL_PASSWORD"],
}



class Email :

    _metadata = None
    _body = None
    _attachments = []
    type: EmailType = None
    
    def __init__(self, id, hash, msg: email.message.Message, dir):
        self.id=id
        self.__hash=hash
        self.msg: email.message.Message = msg

        self._metadata = self.extract_metadata()
        self._body = self.extract_text_content()
        self._attachments = self.list_attachments(dir)

    def __repr__(self):
        return (
            f"Email("
            f"id={self.id},"
            f"Emailtype=({self.type}), "
            f"metadata={self._metadata},"
            f"attachments=[{', '.join([str({k: v for k, v in attachment.items() if k != 'content'}) for attachment in self._attachments])}]"
            # f"body={self._body}),"
            f")"
        )
    
    @property
    def hash(self):
        return self.__hash

    @staticmethod
    def format_email_string(header: str) -> tuple[str,str]:
        """Extract name, email from a From/To header"""
        if "<" in header and ">" in header:
            name = header.split("<")[0].strip().strip('"')
            email = header.split("<")[1].split(">")[0].strip()
        else:
            name = ""
            email = header.strip()
        return name, email
    
    def extract_metadata(self):
        """Extract basic metadata from email message for classification"""
        # Extract subject with encoding handling
        subject, encoding = decode_header(self.msg.get("Subject", ""))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")
        
        # Extract from/sender info
        from_name, from_email = self.format_email_string(self.msg.get("From", ""))
        
        self._metadata = {
            "subject": subject,
            # "from_name": from_name,
            # "from_email": from_email,
            "from": self.msg.get("From", ""),
            "date": self.msg.get("Date", ""),
            "to": self.msg.get("To", ""),
            "cc": self.msg.get("Cc", ""),
            "message_id": self.msg.get("Message-ID", ""),
        }
        return self._metadata
    
    def extract_text_content(self) -> str:
        """Extract only the text content from email for initial classification"""
        text_content = ""
        
        if self.msg.is_multipart():
            for part in self.msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Get text/plain and text/html content, but skip attachments
                if content_type in ("text/plain", "text/html") and "attachment" not in content_disposition:
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        text_content += payload.decode(charset, errors='replace')
                        if content_type == "text/plain":  # Prioritize plain text
                            break
                    except Exception as e:
                        continue
        else:
            # If not multipart, just get the payload
            try:
                payload = self.msg.get_payload(decode=True)
                charset = self.msg.get_content_charset() or 'utf-8'
                text_content = payload.decode(charset, errors='replace')
            except Exception as e:
                pass
                
        return text_content


    def list_attachments(self, temp_dir="."):
        """Record metadata about attachments without processing them yet"""
        attachments = []
        
        for part in self.msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
                
            filename = part.get_filename()
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            
            # Skip if it's not an attachment and not inline content
            if not filename and "attachment" not in content_disposition and "inline" not in content_disposition:
                continue
                
            # Create a standardized filename if none exists
            if not filename:
                ext = mimetypes.guess_extension(content_type) or ".bin"
                filename = f"unnamed_attachment_{len(attachments)}{ext}"
                
            # Create a reference path for where this would be stored
            safe_filename = Path(filename).name  # Remove any path manipulation
            attachment_path = temp_dir / f"{self.__hash}_{safe_filename}"
          
            attachments.append({
                "filename": safe_filename,
                "content_type": content_type,
                "disposition": content_disposition,
                "content": part.get_payload(decode=True),
                "size": len(part.get_payload(decode=True)),
                "path": str(attachment_path),
                "processed": False
            })
            
        return attachments
    
    def process_attachments(self):
        for attachment in self._attachments:
            with open(attachment["path"], 'wb') as f:
                f.write(attachment["content"])
            attachment.update({"processed": True})
        print(f"Saved {len(self._attachments)} to {self._attachments[0]['path']}")
        

def fetch_emails(
        start_date: str, 
        credentials: dict[str, str] =DEFAULT_CREDENTIALS,
        end_date:str | None = None, 
        folder: Literal["INBOX"]="INBOX", #TODO: Have to expand  this to all allowed folder names
        max_emails: int=50,
        temp_dir=None, 
    ) -> list[Email]:
    
    if not all(key in credentials for key in ("host", "username", "password")):
        raise ValueError("Credentials must contain 'host', 'username', and 'password' keys.")

    mail = imaplib.IMAP4_SSL(credentials["host"], 993) 
    mail.login(credentials["username"], credentials["password"])
    mail.select(folder)
    # The date format is 'DD-Mon-YYYY' (e.g., "25-Feb-2025")
    if end_date:
        status, data = mail.search(None, f'(SINCE "{start_date}")', f'(BEFORE "{end_date}")')
    else:
        status, data = mail.search(None, f'(ON "{start_date}")')        

    email_ids = data[0].split()

    if max_emails and len(email_ids) > max_emails:
        email_ids = email_ids[-max_emails:]  

    emails = []
    if not temp_dir:
        temp_dir = Path(os.getcwd()) / f"data/tmp/{start_date}"
    temp_dir.mkdir(exist_ok=True, parents=True)

    for id in email_ids:
        email_id = id.decode()
        # Create a unique ID for this email
        email_hash = hashlib.md5(f"{email_id}_{start_date}".encode()).hexdigest()
        
        status, messages = mail.fetch(id, "(RFC822)")
        for message in messages:
            if isinstance(message, tuple):
                msg = email.message_from_bytes(message[1])
                
                emails.append(Email(id=email_id, hash=email_hash, msg=msg, dir=temp_dir))

    mail.logout()
        
    return emails



def classify_emails(emails: list[Email], classification_threshold=0.7) -> list[Email]:
    """
    Classify emails based on their metadata and text content
    (Placeholder for your LLM-based classification logic)
    """
    classified_emails = []
    
    for email in emails:
        # Example classification logic (replace with your LLM implementation)
        # This is where you'd call your LLM to classify based on subject/content
        recruitment_indicators = [
            "resume", "cv", "application", "job", "position", 
            "candidate", "apply", "hiring", "recruitment"
        ]
        
        score = 0.0
        subject_lower = email["subject"].lower()
        content_lower = email["text_content"].lower()
        
        for indicator in recruitment_indicators:
            if indicator in subject_lower:
                score += 0.3
            if indicator in content_lower:
                score += 0.1
                
        # Add classification results
        email["is_candidate_related"] = score > classification_threshold
        email["confidence_score"] = score
        classified_emails.append(email)
        
    return classified_emails


def process_candidate_email(
        email_data, 
        temp_dir, 
        credentials: dict[str, str] = DEFAULT_CREDENTIALS):
    """
    Process a classified candidate email to extract attachments and detailed information
    (Only called for emails classified as candidate-related)
    """

    mail = imaplib.IMAP4_SSL(credentials["host"], 993)
    mail.login(credentials["username"], credentials["password"])
    # Reconnect to get the full message if needed

    mail.select("INBOX")
    
    status, messages = mail.fetch(email_data["id"].encode(), "(RFC822)")
    msg = email.message_from_bytes(messages[0][1]) #Getting only the response part(#1) from the last message(#0) 
    
    # Now process all attachments that we identified earlier
    for i, attachment in enumerate(email_data["attachments"]):
        email_data["attachments"][i] = process_attachment(msg, attachment)
    
    # Example of extracting candidate information (placeholder for your LLM extraction)
    candidate_info = {
        "source": "email",
        "email_id": email_data["id"],
        "contact_email": email_data["from_email"],
        "contact_name": email_data["from_name"],
        "received_date": email_data["date"],
        "resume_files": [
            attachment["temp_path"] 
            for attachment in email_data["attachments"] 
            if attachment["processed"] and attachment["content_type"] in [
                "application/pdf", "application/msword", 
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ]
        ],
        # Additional fields to be populated by LLM extraction
        "extracted_info": {}
    }
    
    mail.logout()
    return candidate_info



# Example usage workflow
def process_daily_emails():
    date_str = datetime.utcnow().strftime("%d-%b-%Y")
    
    # Step 1: Fetch emails with lightweight extraction
    emails = fetch_emails(date_str, max_emails=100)
    
    # Step 2: Classify emails using the lightweight content
    classified_emails = classify_emails(emails)
    
    # Step 3: Process only candidate-related emails more deeply
    candidates = []
    for email in classified_emails:
        if email["type"]=="candidate":
            email.process_attachments()

    
    # Step 4: Return structured candidate information
    return {
        "total_emails": len(emails),
        "candidate_emails": len(candidates),
        "candidates": candidates
    }

