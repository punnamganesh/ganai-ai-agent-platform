import os
import logging
from typing import Dict, Any, Optional
from tavily import TavilyClient

logger = logging.getLogger(__name__)

class WebSearchTool:
    """Tool to search the web using Tavily API"""
    
    def __init__(self):
        self.name = "web_search"
        self.description = "Searches the internet for up‑to‑date information"
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.client = None
        if self.api_key:
            self.client = TavilyClient(api_key=self.api_key)
    
    def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Execute a web search.
        
        Args:
            query (str): The search query.
            max_results (int): Number of results to return (max 10).
        
        Returns:
            Dict with success flag and search results or error.
        """
        if not self.client:
            return {
                "success": False,
                "error": "TAVILY_API_KEY not set or invalid",
                "message": "Please add your Tavily API key to .env"
            }
        
        try:
            response = self.client.search(
                query=query,
                max_results=min(max_results, 10),
                search_depth="basic"  # "basic" or "advanced" (advanced uses more credits)
            )
            
            results = response.get("results", [])
            if not results:
                return {
                    "success": True,
                    "data": [],
                    "formatted": "No results found for that query."
                }
            
            # Format results into readable text
            formatted_results = []
            for idx, item in enumerate(results[:max_results], 1):
                title = item.get("title", "Untitled")
                url = item.get("url", "#")
                content = item.get("content", "")
                formatted_results.append(f"{idx}. **{title}**\n   {content[:200]}...\n   Source: {url}")
            
            formatted_text = "\n\n".join(formatted_results)
            
            return {
                "success": True,
                "data": results,
                "formatted": f"Found {len(results)} results:\n\n{formatted_text}"
            }
            
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to perform web search."
            }
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "requires_api_key": True
        }