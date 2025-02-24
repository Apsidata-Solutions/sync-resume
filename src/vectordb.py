import asyncio
import time
from db import vectorstore
import pandas as pd

from langchain_core.documents import Document

df =pd.read_csv("~/Downloads/Candidates (1).csv")

async def add_docs():
    start_time = time.time()
    tasks = []  # Create a list to hold the tasks
    for idx, cand in pd.concat([df,df,df,df]).iterrows():
        tasks.append(vectorstore.aadd_documents([Document(page_content=str(cand))]))

    await asyncio.gather(*tasks)  # Await all tasks at once
    print(time.time()-start_time)

if __name__ == "__main__":
    asyncio.run(add_docs())
