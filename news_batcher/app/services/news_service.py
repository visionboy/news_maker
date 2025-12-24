import google.generativeai as genai
import feedparser
from sqlalchemy.orm import Session
from datetime import datetime
from ..config import settings
from ..models import NewsArticle
import logging
from dateutil import parser as date_parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    logger.warning("GEMINI_API_KEY not set. Summarization will be skipped or mocked.")
    model = None

def fetch_and_process_news(db: Session, limit: int = 20):
    """
    Fetches news from RSS, summarizes using Gemini, and saves to DB.
    """
    logger.info("Starting news fetch cycle...")
    
    # 1. Fetch from RSS
    feed = feedparser.parse(settings.RSS_FEED_URL)
    if not feed.entries:
        logger.warning("No entries found in RSS feed.")
        return 0

    processed_count = 0
    
    # Iterate through entries (limit to specified count)
    for entry in feed.entries[:limit]:
        title = entry.title
        link = entry.link
        # RSS 'published' is a string, parse it
        try:
            published_at = date_parser.parse(entry.published)
        except:
            published_at = datetime.utcnow()
            
        # Check duplicates
        existing = db.query(NewsArticle).filter(NewsArticle.original_url == link).first()
        if existing:
            logger.info(f"Skipping duplicate: {title}")
            continue

        # 2. Prepare content for Gemini
        # Use description/summary from RSS if available
        content_snippet = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
        
        summary_text = "No summary available."
        
        # 3. Call Gemini
        if model:
            try:
                prompt = f"""
                다음 경제 뉴스 기사를 한국어로 3줄 요약해줘.
                제목: {title}
                내용: {content_snippet}
                링크: {link}
                
                요약:
                """
                response = model.generate_content(prompt)
                if response.text:
                    summary_text = response.text
            except Exception as e:
                logger.error(f"Gemini error for {title}: {e}")
                summary_text = f"Error generating summary: {e}"

        # 4. Save to DB
        news_item = NewsArticle(
            title=title,
            original_url=link,
            summary=summary_text,
            published_at=published_at
        )
        db.add(news_item)
        processed_count += 1
    
    db.commit()
    logger.info(f"Completed batch. Processed {processed_count} new articles.")
    return processed_count
