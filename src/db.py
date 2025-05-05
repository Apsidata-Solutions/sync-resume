import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL

load_dotenv(".env")

# Create the SQLAlchemy engine NOTE: Can't create a Vector DB since target is in SSMS
engine = create_engine(
    URL.create(
        drivername=os.getenv('DATABASE_DRIVER'),
        username=os.getenv('DATABASE_USERNAME'),
        password= os.getenv('DATABASE_PASSWORD'),
        host=os.getenv('DATABASE_HOST'),
        database=os.getenv('DATABASE_NAME'),
    ), 
    echo=True
)

Session = sessionmaker(bind=engine)
session = Session()

# Optional test to verify connection
def test_connection():
    try:
        with engine.connect() as connection:
            query = input("Enter a query: ")
            result = connection.execute(text(query))
            for row in result:
                print(f"\nResult: {row[0]}")
            return True
    except Exception as e:
        print(f"\nError connecting to the database: {e}")
        return False
    
# Run test connection only if this file is executed directly
if __name__ == "__main__":
    test_connection()

