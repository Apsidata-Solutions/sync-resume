

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/postgres', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

# if __name__ == "__main__":
#     # Create an SQLite engine (for production, switch to a more robust DB)
#     engine = create_engine('sqlite:///dry_cleaning.db', echo=True)
    
#     # Create all tables in the engine
#     Base.metadata.create_all(engine)