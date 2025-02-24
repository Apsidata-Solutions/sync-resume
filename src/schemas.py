import re
from datetime import datetime, date
import pandas as pd
from typing import Optional, List, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from db import engine

def read_master(engine)->tuple:

    skills = pd.read_sql_query("SELECT Id, name FROM skills", engine).set_index("id")
    roles = pd.read_sql_query("SELECT Id, name from roles", engine).set_index("id")
    levels = pd.read_sql_query("SELECT Id, name from levels", engine).set_index("id")

    # Create enums from the SQL query results
    skillEnum = Enum("Skill", {name:name for name in skills["name"].to_list()}) #roles["name"].to_dict()
    roleEnum = Enum("Role", {name:name for name in roles["name"].to_list()})
    levelEnum = Enum("Level", {name:name for name in levels["name"].to_list()})

    return roleEnum, skillEnum, levelEnum

roleEnum, skillEnum, levelEnum = read_master(engine)

class PersonalInfo(BaseModel):
    prefix: Optional[str] = Field(description="Prefix used by the candidate, as it appears in their resume")
    first_name: str = Field(description="The first name of the candidate, exactly as it is written in their resume")
    last_name: Optional[str] = Field(description="The last name of the candidate, exactly as it is written in their resume. If not provided, it defaults to an empty string.")
    date_of_birth: Optional[str] = Field(description="The date of birth of the candidate, if provided in the DD-MM-YYYY format")
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v: Optional[str]) -> Optional[str]:
        """
        Validates the date of birth to ensure it is in the correct format (dd-mm-yyyy).
        """
        if v is not None:
            try:
                datetime.strptime(v, '%d-%m-%Y')
            except ValueError:
                raise ValueError("Incorrect date format, should be dd-mm-yyyy")
        return v


class PersonalDisclosure(BaseModel):
    gender: Optional[Literal["Male", "Female", "Non- Binary"]]
    # race: Optional[Literal["Asian", "White", "Black", "Native American", "Mixed", "Not Disclosed"]]
    # ethnicity: Optional[Literal["Hispanic", "Non- Hispanic", "Not Disclosed"]]
    # nationality: Optional[str]


class Location(BaseModel):
    """
    The geographical details of the candidate's residence.
    """
    address: Optional[str] = Field(None, description="The complete street address of the candidate, exactly as provided in the resume, no city, state or zipcode")
    pin_code: Optional[str] = Field(None, description="The postal or zip code corresponding to the candidate's address.")
    #TODO: Make these two also an Enum with values recieved from the database
    city: str = Field(..., description="The city where the candidate resides.")
    state: str = Field(..., description="The state or region where the candidate resides.")
    # country: Optional[str] = Field("India", description="The country where the candidate resides (default set to India).")


class ContactInfo(BaseModel):
    """
    Contact information for the candidate with robust validation.
    """
    email: str = Field(
        description="The candidate's primary email address, as provided in the resume.",
        # examples=["john.doe@example.com"]
    )
    mobile: str = Field(
        description="The candidate's primary mobile phone number in international format with country code (e.g. +91-9876543210). If number only 10",
        # examples=["+91-9876543210", "+1-2345678900"]
    )
    alternate_email: Optional[str] = Field(
        None,
        description="An alternative email address for the candidate, if available.",
    )
    alternate_mobile: Optional[str] = Field(
        None,
        description="An alternative mobile number for the candidate in international format.",
    )
    
    @field_validator('mobile', 'alternate_mobile')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """
        Validates phone numbers to ensure they:
        - Start with a + followed by 1-3 digits for country code
        - Have a hyphen after country code
        - Contain exactly 10 digits after the hyphen
        """
        if v is None:
            return v
            
        pattern = r'^\+\d{1,3}-\d{10}$'
        if not re.match(pattern, v):
            raise ValueError(
                'Invalid phone number format. Must be in international format: '
                '+[country code]-[10 digits] (e.g. +91-9876543210)'
            )
            
        # Optional: Add specific country code validation if needed
        country_code = v.split('-')[0][1:]  # Extract country code without +
        if country_code == "91" and not v[4:].startswith(('6', '7', '8', '9')):
            raise ValueError(
                'Invalid Indian mobile number. Must start with 6, 7, 8, or 9'
            )
            
        return v
    
    @field_validator('email', 'alternate_email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """
        Validates email addresses to ensure they:
        - Follow standard email format
        - Don't contain common typos
        - Have valid TLD length
        """
        if v is None:
            return v
            
        # More comprehensive email pattern
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError(
                'Invalid email format. Must be a valid email address '
                '(e.g. name@domain.com)'
            )
            
        # Additional validations
        if '..' in v:
            raise ValueError('Email cannot contain consecutive dots')
            
        # Check TLD length (2-63 characters as per standards)
        tld = v.split('.')[-1]
        if len(tld) < 2 or len(tld) > 63:
            raise ValueError('Invalid top-level domain length')
            
        # Common typo check
        common_typos = ['gmial', 'yahho', 'outlok', 'hotnail']
        domain = v.split('@')[1].split('.')[0].lower()
        for typo in common_typos:
            if typo in domain:
                raise ValueError(f'Possible typo in email domain: {domain}')
                
        return v
    
    def clean_phone_number(self, phone: str) -> str:
        """
        Helper method to clean and standardize phone numbers.
        """
        # Remove all non-numeric characters except + and -
        cleaned = ''.join(c for c in phone if c.isdigit() or c in '+-')
        
        # Add + if missing
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
            
        # Add - after country code if missing
        if '-' not in cleaned:
            country_code_end = 2 if cleaned.startswith('+91') else 2
            cleaned = f"{cleaned[:country_code_end]}-{cleaned[country_code_end:]}"
            
        return cleaned
    
    def model_post_init(self, __context) -> None:
        """
        Post-initialization processing to clean phone numbers.
        """
        if self.mobile:
            self.mobile = self.clean_phone_number(self.mobile)
        if self.alternate_mobile:
            self.alternate_mobile = self.clean_phone_number(self.alternate_mobile)


class Education(BaseModel):
    """
    A record of the candidate's educational background.
    """
    institute: str = Field(..., description="The name of the educational institution.")
    degree: str = Field(..., description="The degree earned by the candidate (e.g., Bachelor's, Master's, etc.).")
    status: str = Field(..., description="The status of the candidate's education (e.g., completed, in progress, etc.).")
    major: str = Field(..., description="The major or field of study of the candidate's degree.")
    country: str = Field(..., description="The country where the educational institution is located.")
    grant_date: Optional[str] = Field(None, description="The date when the degree was granted, if applicable.")

class ExperienceItem(BaseModel):
    """
    A detailed description of a specific contribution or achievement during an experience,
    structured using the STAR (Situation, Task, Action, Result) method.
    """
    situation: str = Field(..., description="Describe the context or situation in which the contribution was made.")
    task: str = Field(..., description="Detail the specific task or challenge that needed to be addressed.")
    action: str = Field(..., description="Explain the actions you took to address the task.")
    result: str = Field(..., description="Describe the outcome or result of your actions, including measurable impacts if any.")

class Experience(BaseModel):
    """
    A record of professional experience, detailing roles, responsibilities, and contributions.
    """
    organisation: str = Field(..., description="The name of the organisation or institution where the experience was gained.")
    role: str = Field(..., description="The job title or position held during this experience.")
    start_date: str = Field(..., description="The start date of this experience (format: MM-YYYY).")
    end_date: Optional[str] = Field(None, description="The end date of this experience (format: MM-YYYY). Use 'Present' if still ongoing.")
    contributions: List[ExperienceItem] = Field(..., description="A list of contributions or achievements during this experience, structured using the STAR method.")
    skills_applied: List[str] = Field(..., description="A list of skills that were applied or enhanced during this experience.")

class VisaStatus(BaseModel):
    visa_status: str
    visa_expiration: str


class BaseCandidate(Location, ContactInfo, PersonalDisclosure, PersonalInfo, BaseModel):
    """
    Core information about the candidate, including personal details and contact information.
    """
    # personal_info: PersonalInfo
    # personal_disclosure: PersonalDisclosure
    # contact_info: ContactInfo
    # location: Location

    career_start_date: str = Field(description=f"The date when the candidate started their career, inferred from the data in MM-YYYY format (e.g., 03-2024). The start data of their first experience.If no month is given. choose 01-YYYY. If no year is given, chose {date.today().year}")
    education: Optional[List[Education]] = Field(default_factory=list, description="A comprehensive list of the candidate's format education AFTER high school.")
    experiences:Optional[List[Experience]] = Field(default_factory=list, description="A comprehensive list of the candidate's professional experiences in teaching or related fields.")
    
    #TODO: Need to make this validator also, such that it checks that this date is after DOB
    @field_validator('career_start_date')
    def validate_date(cls, v):
        try:
            # Check format
            if not re.match(r'^(0[1-9]|1[0-2])-\d{4}$', v):
                raise ValueError
            # Verify it's a valid date
            datetime.strptime(v, '%m-%Y')
            return v
        except ValueError:
            raise ValueError('Date must be in MM-YYYY format (e.g., 03-2024)')
    

class TeachingCandidate(BaseCandidate):
    """
    Detailed information specific to candidates applying within the teaching industry.
    """
    industry: Literal["Education"] = Field(description="The industry for which the candidate is applying; fixed as 'Education'.")

    primary_skill: skillEnum = Field(description="The primary skill that the candidate highlights most frequently or for the longest duration")
    secondary_skill: Optional[skillEnum] = Field(description="The secondary skill of the candidate, if provided")
    tertiary_skill: Optional[skillEnum] = Field(description="The tertiary skill of the candidate, if provided")

    role: roleEnum = Field(description="The role that the candidate is applying for")
    level: Optional[levelEnum] = Field(description="The level of the role that the candidate is applying for")
    
    # certifications: Optional[List[str]] = Field(None, description="A list of any teaching certifications or professional qualifications the candidate holds.")


DEMO_CANDIDATE_TEMPLATE ={
  "prefix": "Mrs.",
  "first_name": "Mahalakshmi",
  "last_name": "Jaiswal",
  "date_of_birth": None,
  "gender": None,

  "email": "jaiswalmahi9@gmail.com",
  "mobile": "+91-9621212981",

  "address": None,
  "pin_code": None,
  "city": "Noida",
  "state": "Uttar Pradesh",

  "career_start_date": "04-2019",
  "education": [
    {
      "institute": "Ewing Christian College, Prayagraj",
      "degree": "B.Ed.",
      "status": "completed",
      "major": "Education",
      "country": "India",
      "grant_date": "2019"
    },
    {
      "institute": "Subharti University, Meerut",
      "degree": "M.Com",
      "status": "completed",
      "major": "Commerce",
      "country": "India",
      "grant_date": "2019"
    },
    {
      "institute": "University of Allahabad",
      "degree": "B.Com",
      "status": "completed",
      "major": "Commerce",
      "country": "India",
      "grant_date": "2017"
    },
    {
      "institute": "Girls' High School & College, Prayagraj",
      "degree": "XIIth",
      "status": "completed",
      "major": "I.S.C.",
      "country": "India",
      "grant_date": "2014"
    },
    {
      "institute": "Girls' High School & College, Prayagraj",
      "degree": "Xth",
      "status": "completed",
      "major": "I.C.S.E.",
      "country": "India",
      "grant_date": "2012"
    }
  ],
  "experiences": [
    {
      "organisation": "NOIDA PUBLIC SR SEC SCHOOL, NOIDA",
      "role": "Teacher",
      "start_date": "Present",
      "end_date": None,
      "contributions": [],
      "skills_applied": [
        "English"
      ]
    },
    {
      "organisation": "Boys' High School & College, Prayagraj",
      "role": "Primary Teacher",
      "start_date": "04-2019",
      "end_date": "03-2021",
      "contributions": [
        {
          "situation": "Class teacher of Prep Standard",
          "task": "Taught various subjects",
          "action": "Conducted daily sessions and participated in activities",
          "result": "Managed class strength of 50 students"
        }
      ],
      "skills_applied": [
        "English",
        "Hindi",
        "Mathematics",
        "E.V.S",
        "Conversation",
        "Handwriting",
        "Reading/Recitation",
        "Health Hygiene",
        "Computer Play"
      ]
    }
  ],
  "industry": "Education",

  "primary_skill": "English",
  "secondary_skill": "Commerce",
  "tertiary_skill": None,
  "role": "Teacher",
  "level": "TGT",
  "certifications": [
    "Teachers Eligibility Test (TET) 2019",
    "Course on Computer Concepts (CCC)",
    "English & Hindi handwriting certificate",
    "Paryavaran Ratna Certificate",
    "Silver level in HDFC Bank Meritus Scholarship",
    "3rd International Mathematics Olympiad Certificate",
    "Computer Prize (G.H.S.)",
    "Scout & Guide Program participation",
    "Various prizes in competitions and workshops"
  ]
}
