import requests
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
    
    model = None
    try:
        logger.info("Discovering available Gemini models...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        logger.info(f"Available models: {available_models}")
        
        # Prioritize 1.5-flash, then pro, then any gemini
        target_model_name = None
        
        # Priority list
        priorities = ['models/gemini-1.5-flash', 'models/gemini-pro', 'models/gemini-1.0-pro']
        
        # Check against available models (which usually start with 'models/')
        for p in priorities:
            if p in available_models:
                target_model_name = p
                break
        
        # If no priority model found, pick the first 'gemini' model
        if not target_model_name:
            for m in available_models:
                if 'gemini' in m:
                    target_model_name = m
                    break
        
        if target_model_name:
            # SDK often wants no 'models/' prefix for GenerativeModel constructor, 
            # OR it handles it. Safe to strip 'models/' if present just in case implementation varies,
            # but google-generativeai usually accepts both or just the short name.
            # Let's try passing exactly what list_models returned first.
            logger.info(f"Selected Model: {target_model_name}")
            model = genai.GenerativeModel(target_model_name)
        else:
            logger.error("No suitable Gemini model found in the list.")
            
    except Exception as e:
        logger.error(f"Error during model discovery: {e}")
        # Fallback blindly
        model = genai.GenerativeModel('gemini-pro')

else:
    logger.warning("GEMINI_API_KEY not set. Summarization will be skipped or mocked.")
    model = None

def fetch_and_process_news(db: Session, limit: int = 10):
    logger.info("Starting news fetch cycle using RSS Feed...")

    # 1. Fetch from RSS using requests for better header control
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://news.google.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        response = requests.get(settings.RSS_FEED_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch RSS. Status: {response.status_code}, Body: {response.text[:200]}")
            return 0
            
        feed = feedparser.parse(response.content)
        
    except Exception as e:
        logger.error(f"Network error fetching RSS: {e}")
        return 0
    
    if hasattr(feed, 'status'):
        logger.info(f"RSS Feed Status: {feed.status}")
    
    if not feed.entries:
        logger.warning(f"No entries found in RSS feed. Feed Details: {feed.feed}")
        if hasattr(feed, 'bozo') and feed.bozo:
             logger.warning(f"Feed parse error (bozo): {feed.bozo_exception}")
        return 0

    logger.info(f"Found {len(feed.entries)} entries in RSS feed. Processing top {limit}...")

    processed_count = 0
    
    # Iterate through entries
    for entry in feed.entries[:limit]:
        title = entry.title
        link = entry.link
        
        # Parse publication date
        try:
            published_at = date_parser.parse(entry.published)
        except:
            published_at = datetime.utcnow()
            
        # Check duplicates
        existing = db.query(NewsArticle).filter(NewsArticle.original_url == link).first()
        if existing:
            # logger.info(f"Skipping duplicate: {title}")
            continue

        # 2. Prepare content for Gemini
        content_snippet = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
        
        summary_text = "요약 정보를 가져오지 못했습니다."
        
        # 3. Call Gemini
        if model:
            try:
                prompt = f"""
                다음 뉴스 기사를 한국어로 10줄 요약해줘.
                
                제목: {title}
                내용: {content_snippet}
                
                요약:
                """
                response = model.generate_content(prompt)
                if response.text:
                    summary_text = response.text
            except Exception as e:
                logger.error(f"Gemini summarization error for {title}: {e}")
                summary_text = f"요약 실패: {e}"

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
