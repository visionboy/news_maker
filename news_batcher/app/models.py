from sqlalchemy import Column, Integer, String, Text, DateTime, TIMESTAMP
from sqlalchemy.sql import func
from .database import Base

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    original_url = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
