"""Acumen Web Scraper Tool - Extract content from any webpage."""

from crewai.tools import BaseTool
from acumen.security.audit import audit
from acumen.core.logger import get_logger

logger = get_logger("acumen.tools.scraper")

class WebScraperTool(BaseTool):
    name: str = "Web Scraper"
    description: str = "Scrape and extract content from a URL. Input: URL string."

    def _run(self, url: str) -> str:
        try:
            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            headers = {"User-Agent": "Mozilla/5.0 (compatible; AcumenBot/1.0)"}
            response = requests.get(url.strip(), headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            title = soup.title.string if soup.title else "No title"
            paragraphs = soup.find_all(["p", "h1", "h2", "h3", "li", "td"])
            content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            content = content[:5000]
            audit.log_action("tool", "web_scrape", "scraper", url,
                f"{len(content)} chars extracted", "success")
            logger.info(f"Scraped {len(content)} chars from {url[:50]}")
            return f"Title: {title}\n\nContent:\n{content}"
        except Exception as e:
            audit.log_action("tool", "web_scrape", "scraper", url, str(e), "error")
            return f"Scrape failed: {str(e)}"