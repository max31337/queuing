from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the database URL
#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:ccPBVCZUKuhjTrvUFILiMUKhPRczaRcY@postgres.railway.internal:5432/railway"
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:@localhost:5432/queueingdb"


# Create an engine that connects to the database
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"options": "-csearch_path=public"})

# Create a SessionLocal class using the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define a base class for your models
Base = declarative_base()
