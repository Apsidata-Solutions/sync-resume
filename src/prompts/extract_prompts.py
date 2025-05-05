from langchain_core.prompts import ChatPromptTemplate

PARSE_TEMPLATE="""You are being given images of the resume of a candidate who is looking for a 
role in an educational institute. You job is to extract any and all information you might need from 
this image yield the following information. Atleast write the following information {schema}"""
PARSE_PROMPT=ChatPromptTemplate([
    ("system", PARSE_TEMPLATE), 
    ("placeholder","{messages}")
])

SCHEMA_TEMPLATE="""You job is to read the given chain of messages and outptut a structured response 
that correctly and most accurately extracts the required candidates information, based off 
the image as well as your obdervation understanding of it."""
SCHEMA_PROMPT=ChatPromptTemplate([
    ("system", SCHEMA_TEMPLATE), 
    ("placeholder","{messages}")
])