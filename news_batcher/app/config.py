import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@db:3306/news_db")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    RSS_FEED_URL = os.getenv("RSS_FEED_URL", "https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRDgwZ0hzQlJCelZnV25Oc2JXd3FCSG9A?hl=ko&gl=KR&ceid=KR%3Ako") # Default to Google News Economy KR
    BATCH_SCHEDULE_HOUR = int(os.getenv("BATCH_SCHEDULE_HOUR", "9")) # Default 9 AM
    BATCH_SCHEDULE_MINUTE = int(os.getenv("BATCH_SCHEDULE_MINUTE", "0"))

settings = Settings()
