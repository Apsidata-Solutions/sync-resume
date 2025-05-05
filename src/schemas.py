from src.outputs import TeachingCandidate
from typing import Literal, Optional
from pydantic import BaseModel

class ResumeUploadResponse(BaseModel):
    status: Literal["success", "failure", "cancelled", "pending", "processing"]
    id: Optional[str]
    error: Optional[str] 
    resume_url: Optional[str] 
    candidate: Optional[TeachingCandidate] = None


class ResumeSearchResponse(BaseModel):
    id : str
    confidence : float

DEMO_RESPONSE = {
  "id": "ed48649d-cd8c-4cba-b276-f03c0cef19b4",
  "status": "success",
  "candidate": {
    "prefix": None,
    "first_name": "Padmini",
    "last_name": "Negi",
    "date_of_birth": "28-05-1985",
    "gender": None,
    "email": "negimini@gmail.com",
    "mobile": "+91-8010056152",
    "alternate_email": None,
    "alternate_mobile": "+91-9650126607",
    "address": "Flat No. 60 C, 2nd Floor, Dhawaligiri Apartment, B-12 A, Sector 34",
    "pin_code": None,
    "city": "Noida",
    "state": "Uttar Pradesh",
    "career_start_date": "01-2012",
    "education": [
      {
        "specialization": "English & SSt.",
        "school": "HNB Garhwal University",
        "university": "HNB Garhwal University",
        "degree": "B.A.",
        "country": "India",
        "start_date": "01-2007",
        "end_date": "01-2008",
        "status": "completed"
      },
      {
        "specialization": "English",
        "school": "HNB Garhwal University",
        "university": "HNB Garhwal University",
        "degree": "M.A.",
        "country": "India",
        "start_date": "01-2010",
        "end_date": "01-2011",
        "status": "completed"
      },
      {
        "specialization": "History",
        "school": "Indira Gandhi National Open University",
        "university": "Indira Gandhi National Open University",
        "degree": "M.A.",
        "country": "India",
        "start_date": "01-2019",
        "end_date": None,
        "status": "in progress"
      }
    ],
    "experiences": [
      {
        "organisation": "ASSISI Convent School",
        "designation": "PRT All Subject",
        "start_date": "04-2021",
        "end_date": None,
        "contributions": [],
        "current_job_or_not": True
      },
      {
        "organisation": "Nehru International School",
        "designation": "PRT SSt",
        "start_date": "04-2015",
        "end_date": "05-2019",
        "contributions": [
          {
            "situation": "Worked as a PRT SSt in a reputable school.",
            "task": "Educate students in social studies.",
            "action": "Implemented innovative teaching methods to engage students.",
            "result": "Improved student performance in examinations and overall interest in the subject.",
            "skills_applied": "Social Science"
          }
        ],
        "current_job_or_not": False
      },
      {
        "organisation": "Blooming Dale Public School",
        "designation": "PRT SSt",
        "start_date": "05-2013",
        "end_date": "12-2014",
        "contributions": [],
        "current_job_or_not": False
      },
      {
        "organisation": "Vanasthali Public School",
        "designation": "PRT SSt",
        "start_date": "01-2012",
        "end_date": "11-2012",
        "contributions": [],
        "current_job_or_not": False
      },
      {
        "organisation": "Holly Faith Public School",
        "designation": "PRT SSt. & English",
        "start_date": "07-2007",
        "end_date": "05-2009",
        "contributions": [],
        "current_job_or_not": False
      }
    ],
    "industry": "Education",
    "primary_skill": "Social Science",
    "secondary_skill": "English",
    "tertiary_skill": None,
    "role": "Teacher",
    "level": "PRT"
  },
  "resume_url": "/static/resume/cand-48649d-cd8c-4cba-b276-f03c0cef19b4"
}
