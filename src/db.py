from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.ext.asyncio import create_async_engine

#This is the engine for retrieval database
engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/postgres', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=3072)
connection = create_async_engine("postgresql+psycopg://adit:Warmachinerox-123@localhost:6024/candidates")  # Uses psycopg3!
collection_name = "education"

# vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
vectorstore = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
)

