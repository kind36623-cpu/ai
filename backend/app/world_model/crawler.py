"""
Layer 6: Internet Learning — World Model Updater
Runs on a schedule (every 6 hours) to crawl RSS feeds, extract knowledge,
summarize it with Gemini, and store the result as long-term memory nodes.
The AI never browses the open web directly; it reads structured feeds only
(safe, deterministic, auditable).
"""
import feedparser
import requests
import logging
import time
from bs4 import BeautifulSoup
from app.memory.pinecone_db import memory_graph
from app.core.config import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

# ── Trusted knowledge feeds ───────────────────────────────────────────────
# Add or remove any RSS feeds here to control what your AI reads.
KNOWLEDGE_FEEDS = [
    # Science & Technology
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://www.wired.com/feed/rss",
    "https://rss.arxiv.org/rss/cs.AI",

    # World news (for context awareness)
    "https://feeds.bbci.co.uk/news/world/rss.xml",

    # Health
    "https://feeds.bbci.co.uk/news/health/rss.xml",
]

MAX_ARTICLES_PER_FEED = 5      # Don't overload memory on each crawl
MAX_TEXT_CHARS        = 2000   # Truncate long articles before summarising

class WebCrawler:
    def __init__(self):
        self.summariser = None
        if settings.gemini_api_key:
            self.summariser = genai.GenerativeModel(
                model_name=settings.primary_model,
                system_instruction=(
                    "You are a precise knowledge extractor. "
                    "Given a news article, extract the 3 most important facts as "
                    "concise bullet points. No opinions, no filler words."
                )
            )

    def _fetch_article_text(self, url: str) -> str:
        """Download a page and extract its readable text."""
        try:
            resp = requests.get(url, timeout=8,
                                headers={"User-Agent": "SeedAGI-Crawler/1.0"})
            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove script / style noise
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return text[:MAX_TEXT_CHARS]
        except Exception as e:
            logger.warning(f"Could not fetch {url}: {e}")
            return ""

    def _summarise(self, title: str, body: str) -> str:
        """Use Gemini to compress an article into key facts."""
        if not self.summariser or not body:
            return title  # Fallback: store just the headline
        try:
            prompt = f"Article title: {title}\n\nContent: {body}"
            response = self.summariser.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Summarisation failed: {e}")
            return title

    def crawl_and_learn(self):
        """
        Main entry point — called by the scheduler every N hours.
        Crawl every feed, summarise new articles, store as memory nodes.
        """
        if not memory_graph.is_enabled:
            logger.warning("Memory Graph offline — skipping internet learning cycle.")
            return

        total_stored = 0
        logger.info("═══ Internet Learning Cycle Started ═══")

        for feed_url in KNOWLEDGE_FEEDS:
            try:
                feed    = feedparser.parse(feed_url)
                entries = feed.entries[:MAX_ARTICLES_PER_FEED]
                logger.info(f"Feed: {feed_url} → {len(entries)} articles")

                for entry in entries:
                    title = entry.get("title", "Untitled")
                    link  = entry.get("link", "")

                    # Avoid re-storing articles already in memory
                    existing = memory_graph.retrieve_memories(title, top_k=1)
                    if existing and title[:30] in existing:
                        continue

                    body    = self._fetch_article_text(link)
                    summary = self._summarise(title, body)

                    memory_graph.store_memory(
                        text        = f"[WORLD KNOWLEDGE] {title}: {summary}",
                        source      = "internet_crawler",
                        trust_score = 60  # Internet info is lower trust than direct user input
                    )
                    total_stored += 1
                    time.sleep(0.5)  # Be polite to servers

            except Exception as e:
                logger.error(f"Failed to process feed {feed_url}: {e}")

        logger.info(f"═══ Internet Learning Cycle Complete — {total_stored} nodes stored ═══")


# Global instance
crawler = WebCrawler()
