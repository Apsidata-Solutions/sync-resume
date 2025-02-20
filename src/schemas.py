import pandas as pd
from typing import Optional,Enum
from pydantic import BaseModel, Field, EmailStr

from db import engine

def read_master(engine)->tuple:

    skills = pd.read_sql_query("SELECT name FROM skills", engine)
    roles = pd.read_sql_query("SELECT name from roles", engine)
    levels = pd.read_sql_query("SELECT name from levels", engine)

    # Create enums from the SQL query results
    roleEnum = Enum("Role", {name: name for name in roles["name"].to_list()})
    skillEnum = Enum("Skill", {name: name for name in skills["name"].to_list()})
    levelEnum = Enum("Level", {name: name for name in levels["name"].to_list()})

    return roleEnum, skillEnum, levelEnum

roleEnum, skillEnum, levelEnum = read_master(engine)


class Candidate(BaseModel):
    prefix: str = Field(description="Prefix used by the candidate, as it appears in their resume")
    first_name: str = Field(description="The first name of the candidate, exactly as it is written in their resume")
    last_name: Optional[str] = Field(default="", description="The last name of the candidate, exactly as it is written in their resume. If not provided, it defaults to an empty string.")
    email: EmailStr = Field(description="The email address of the candidate, exactly as it is written in their resume. If multiple email addresses are provided, any one of them can be chosen.")
    mobile: str = Field(description="The contact phone number of the candidate, excluding the country code, exactly as it is written in their resume")
    primary_skill: skillEnum = Field(description="The primary skill that the candidate highlights most frequently or for the longest duration")
    secondary_skill: Optional[skillEnum] = None
    tertiary_skill: Optional[skillEnum] = None
    date_of_birth: Optional[str] = Field(None, description="The date of birth of the candidate, if provided")
    role: roleEnum = Field(description="The role that the candidate is applying for")
    level: levelEnum = Field(description="The level of the role that the candidate is applying for")
    address: str = Field(description="The address of the candidate, as it appears in their resume")
    pin_code: Optional[str] = Field(None, description="The postal index number of the candidate's address, if provided")
    city: str = Field(description="The name of the city where the candidate resides, as it appears in their resume")
    state: str = Field(description="The state where the candidate resides, as it appears in their resume")
    career_start_date: str = Field(description="The MM-YYYY date when the candidate started their career, as it appears in their resume")
