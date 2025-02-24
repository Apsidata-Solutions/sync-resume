import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv()
#This is the engine for retrieval database. Only a placeholder for now. Ideally this should become same as vector DB
engine = create_engine(f'postgresql+psycopg://postgres:postgres@{os.getenv('DATABASE_HOST')}:5432/postgres', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=3072)
connection = create_async_engine(f"postgresql+psycopg://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:6024/{os.getenv('DATABASE_NAME')}")  # Uses psycopg3!
collection_name = "education"

# vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
vectorstore = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
)

