import os
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

load_dotenv()

class FirecrawlService:
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment variables")
        self.app = FirecrawlApp(api_key=api_key)
    
    def search_companies(self, query: str, num_results: int = 5):
        try:
            result = self.app.search(
                query=f"{query} company pricing",
                limit=num_results,
                formats=["markdown"]
            )
            return result
        except Exception as e:
            print(f"Error during Firecrawl search: {e}")
            return []
    def scrape_company_pages(self, url: str):  
        try:
            result = self.app.scrape_url(
                url=url,
                formats=["markdown"]
            )
            return result
        except Exception as e:
            print(f"Error during Firecrawl scraping: {e}")
            return None