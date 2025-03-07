"""
Search tool for retrieving information from the web.
"""
import re
import requests

from bs4 import BeautifulSoup
from typing import List, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain.tools.base import BaseTool
from duckduckgo_search import DDGS

class WebSearchInput(BaseModel):

    """Input for web search."""

    query: str = Field(..., description="The search query to use.")
    num_results: int = Field(5, description="Number of search results to return.")

class WebSearchTool(BaseTool):

    """Tool for searching the web using DuckDuckGo."""

    name: str = "web_search"
    description: str = "Search for information on the web using DuckDuckGo."
    args_schema: Type[BaseModel] = WebSearchInput
    
    def _run(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:

        """Run the web search tool."""

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
            
            # Format the results for better readability
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append({
                    "index": i,
                    "title": result.get("title", "No Title"),
                    "body": result.get("body", "No Content"),
                    "href": result.get("href", "No URL"),
                })
            
            return formatted_results
        except Exception as e:
            return [{"error": f"Error during web search: {str(e)}"}]

    async def _arun(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:

        """Run the web search tool asynchronously."""
        
        return self._run(query, num_results)

class MovieInfoSearchTool(BaseTool):

    """Tool for searching specific movie or TV show information."""

    name: str = "movie_info_search"
    description: str = "Search for specific information about a movie or TV show (title, year, rating, etc.)."
    args_schema: Type[BaseModel] = WebSearchInput
    
    def _run(self, query: str, num_results: int = 3) -> Dict[str, Any]:

        """Run the movie info search tool."""
        
        try:
            # First, search for the movie on DuckDuckGo to get IMDb link
            enhanced_query = f"{query} site:imdb.com"
            
            movie_info = {
                "title": None,
                "release_year": None,
                "imdb_rating": None,
                "genre": None,
                "director": None,
                "synopsis": None,
                "sources": []
            }
            
            # Search for IMDb results
            with DDGS() as ddgs:
                search_results = list(ddgs.text(enhanced_query, max_results=3))
            
            # Extract IMDb URL
            imdb_url = None
            for result in search_results:
                url = result.get("href", "")
                if "imdb.com/title/" in url and "/releaseinfo" not in url:
                    imdb_url = url
                    movie_info["sources"].append({
                        "title": result.get("title", "IMDb"),
                        "url": url
                    })
                    break
            
            # If an IMDb URL is found, scrape it for information
            if imdb_url:
                try:
                    # Get the IMDb page
                    response = requests.get(imdb_url, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    })
                    response.raise_for_status()
                    
                    # Parse the HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract title and year
                    title_elem = soup.select_one('h1')
                    if title_elem:
                        full_title = title_elem.text.strip()
                        movie_info["title"] = full_title
                        
                        # Extract year if it's in the title
                        year_match = re.search(r'\((\d{4})\)', full_title)
                        if year_match:
                            movie_info["release_year"] = year_match.group(1)
                    
                    # Try to find release year in release info if not in title
                    if not movie_info["release_year"]:
                        # Look for year in any span that might contain it
                        year_spans = soup.select('a[href*="releaseinfo"]')
                        for span in year_spans:
                            year_match = re.search(r'(\d{4})', span.text)
                            if year_match:
                                movie_info["release_year"] = year_match.group(1)
                                break
                                
                        # Also try to find year in the URL
                        if not movie_info["release_year"] and "tt" in imdb_url:
                            # Get the page content for the release info
                            release_url = imdb_url.split("?")[0].rstrip('/') + "/releaseinfo"
                            try:
                                release_response = requests.get(release_url, headers={
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                                })
                                release_soup = BeautifulSoup(release_response.text, 'html.parser')
                                
                                # Look for release dates
                                date_elements = release_soup.select('td.release-date-item__date')
                                for date in date_elements:
                                    year_match = re.search(r'(\d{4})', date.text)
                                    if year_match:
                                        movie_info["release_year"] = year_match.group(1)
                                        break
                            except:
                                pass
                    
                    # Extract rating
                    rating_elem = soup.select_one('[data-testid="hero-rating-bar__aggregate-rating__score"] span')
                    if rating_elem:
                        rating_text = rating_elem.text.strip()
                        try:
                            movie_info["imdb_rating"] = float(rating_text)
                        except ValueError:
                            pass
                    
                    # Extract director
                    director_section = soup.find('span', string=re.compile('Director|Directors', re.I))
                    if director_section:
                        director_elem = director_section.find_next('a')
                        if director_elem:
                            movie_info["director"] = director_elem.text.strip()
                    
                    # Extract genre
                    genre_elems = soup.select('a[href*="genres="]')
                    if genre_elems:
                        movie_info["genre"] = ", ".join([g.text.strip() for g in genre_elems[:3]])
                    
                    # Extract synopsis
                    synopsis_elem = soup.select_one('[data-testid="plot"]')
                    if synopsis_elem:
                        movie_info["synopsis"] = synopsis_elem.text.strip()
                
                except Exception as e:
                    # If scraping fails, add error to movie info
                    movie_info["scrape_error"] = str(e)
            
            # If scraping failed use DuckDuckGo search
            if not movie_info["title"] or not movie_info["release_year"]:
                enhanced_query = f"{query} movie information IMDb rating release date"
                
                with DDGS() as ddgs:
                    results = list(ddgs.text(enhanced_query, max_results=num_results))
                
                # Process and extract information from the search results
                for result in results:
                    if not result.get("href") in [s["url"] for s in movie_info["sources"]]:
                        movie_info["sources"].append({
                            "title": result.get("title", ""),
                            "url": result.get("href", "")
                        })
                    
                    content = result.get("body", "").lower()
                    
                    # Extract title from result title if not already found
                    if not movie_info["title"] and result.get("title"):
                        title = result.get("title", "")
                        # Remove common suffixes like "- IMDb" or "| Official Site"
                        title = title.split(" - ")[0].split(" | ")[0].strip()
                        movie_info["title"] = title
                    
                    # Extract year if not already found
                    if not movie_info["release_year"]:
                        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', content)
                        if year_match:
                            movie_info["release_year"] = year_match.group(1)
                    
                    # Extract rating if not already found
                    if not movie_info["imdb_rating"]:
                        rating_patterns = [
                            r'imdb rating[:\s]+(\d+\.?\d*)',
                            r'rated[:\s]+(\d+\.?\d*)/10',
                            r'rating[:\s]+(\d+\.?\d*)',
                            r'(\d+\.?\d*)/10'
                        ]
                        
                        for pattern in rating_patterns:
                            rating_match = re.search(pattern, content, re.IGNORECASE)
                            if rating_match:
                                try:
                                    rating = float(rating_match.group(1))
                                    if 0 <= rating <= 10:
                                        movie_info["imdb_rating"] = rating
                                        break
                                except ValueError:
                                    pass
                    
                    # Extract synopsis if not already found
                    if not movie_info["synopsis"] and len(content) > 100:
                        movie_info["synopsis"] = content[:300] + "..."
            
            return movie_info
        except Exception as e:
            return {"error": f"Error during movie info search: {str(e)}"}

    async def _arun(self, query: str, num_results: int = 3) -> Dict[str, Any]:

        """Run the movie info search tool asynchronously."""

        return self._run(query, num_results)