from fastapi import FastAPI, Depends, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging

from .database import engine, Base, get_db
from .services.news_service import fetch_and_process_news
from .config import settings



logger = logging.getLogger(__name__)

# Scheduler setup
scheduler = BackgroundScheduler()

def scheduled_job():
    logger.info("Running scheduled news batch job...")
    # Create a new session for the job
    from .database import SessionLocal
    db = SessionLocal()
    try:
        count = fetch_and_process_news(db, limit=10)
        logger.info(f"Scheduled job finished. Articles added: {count}")
    except Exception as e:
        logger.error(f"Job failed: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Scheduler
    # Initialize DB tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        # Depending on requirement, we might want to fail startup or continue
        # raising here will stop startup
        raise e
    trigger = CronTrigger(hour=settings.BATCH_SCHEDULE_HOUR, minute=settings.BATCH_SCHEDULE_MINUTE)
    scheduler.add_job(scheduled_job, trigger, id='daily_news_batch')
    scheduler.start()
    logger.info(f"Scheduler started. Job set for {settings.BATCH_SCHEDULE_HOUR}:{settings.BATCH_SCHEDULE_MINUTE:02d}")
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(title="Synology News Batcher", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"status": "running", "service": "News Batcher"}

@app.api_route("/trigger-batch", methods=["GET", "POST"])
def trigger_batch(db: Session = Depends(get_db)):
    """
    Manually trigger the news fetch process.
    """
    try:
        count = fetch_and_process_news(db, limit=10)
        return {"message": "Batch executed successfully", "new_articles_count": count}
    except Exception as e:
        logger.error(f"Manual trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news")
def get_news(limit: int = 10, db: Session = Depends(get_db)):
    from .models import NewsArticle
    articles = db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit).all()
    return articles
