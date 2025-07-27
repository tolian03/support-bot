import os
import datetime
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Файл базы рядом с models.py
DB_PATH = os.path.join(os.path.dirname(__file__), 'tickets.db')
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, nullable=False)
    username    = Column(String, nullable=False)
    problem_type = Column(String)
    quest_type   = Column(String)
    issue_type   = Column(String)
    details      = Column(String)
    email        = Column(String)
    wallet       = Column(String)
    status       = Column(String, default='open')
    created_at   = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    """Создаёт файл tickets.db и все таблицы, если их нет."""
    Base.metadata.create_all(bind=engine)
