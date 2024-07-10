from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

url = 'sqlite:///./database.db'
args = {'check_same_thread': False}
engine = create_engine(url, connect_args=args)
SessionLocal = sessionmaker(engine, autoflush=False, autocommit=False)
Base = declarative_base()