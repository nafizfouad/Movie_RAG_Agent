"""
YouTube search tool for finding videos and trailers.
"""
import re
import requests

from urllib.parse import quote_plus
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, Field
from langchain.tools.base import BaseTool

class YouTubeSearchInput(BaseModel):

    """Input for YouTube search."""

    query: str = Field(..., description="The search query to use.")
    num_results: int = Field(1, description="Number of search results to return.")

class YouTubeSearchTool(BaseTool):

    """Tool for searching videos on YouTube."""

    name: str = "youtube_search"
    description: str = "Search for videos on YouTube based on a query."
    args_schema: Type[BaseModel] = YouTubeSearchInput
    
    def _run(self, query: str, num_results: int = 1) -> List[Dict[str, Any]]:

        """Run the YouTube search tool."""

        import re
        import requests
        from urllib.parse import quote_plus
        
        try:
            # Direct search using YouTube's site
            search_query = quote_plus(query)
            url = f"https://www.youtube.com/results?search_query={search_query}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Extract video data from the page
            # YouTube stores this in a JavaScript variable
            video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
            
            # Remove duplicates while preserving order
            unique_video_ids = []
            for video_id in video_ids:
                if video_id not in unique_video_ids:
                    unique_video_ids.append(video_id)
            
            # Limit to requested number
            unique_video_ids = unique_video_ids[:num_results]
            
            # Get video details
            formatted_results = []
            for i, video_id in enumerate(unique_video_ids, 1):
                # Create video information dictionary
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                
                # Extract title from the page (simplified)
                title_match = re.search(f'"{video_id}".*?"title".*?"([^"]+)"', response.text)
                title = title_match.group(1) if title_match else f"Video {i}"
                
                formatted_results.append({
                    "index": i,
                    "title": title,
                    "url": video_url,
                    "thumbnail": thumbnail_url,
                    "video_id": video_id
                })
            
            return formatted_results
        except Exception as e:
            return [{"error": f"Error during YouTube search: {str(e)}"}]

    async def _arun(self, query: str, num_results: int = 1) -> List[Dict[str, Any]]:

        """Run the YouTube search tool asynchronously."""
        
        return self._run(query, num_results)

class MovieTrailerSearchTool(BaseTool):

    """Tool for finding movie trailers on YouTube."""

    name: str = "movie_trailer_search"
    description: str = "Search for trailers of specific movies or TV shows on YouTube."
    args_schema: Type[BaseModel] = YouTubeSearchInput
    
    def _run(self, query: str, num_results: int = 1) -> List[Dict[str, Any]]:

        """Run the movie trailer search tool."""
        
        try:
            # Enhance the query to get better trailer results
            enhanced_query = quote_plus(f"{query} official trailer")
            
            # Direct search using YouTube's site
            url = f"https://www.youtube.com/results?search_query={enhanced_query}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Extract video IDs from the page
            video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
            
            # Remove duplicates while preserving order
            unique_video_ids = []
            for video_id in video_ids:
                if video_id not in unique_video_ids:
                    unique_video_ids.append(video_id)
            
            # Limit to requested number
            unique_video_ids = unique_video_ids[:num_results]
            
            # Get trailer details
            trailer_results = []
            for i, video_id in enumerate(unique_video_ids, 1):
                # Create video information dictionary
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                
                # Extract title from the page (simplified)
                title_match = re.search(f'"{video_id}".*?"title".*?"([^"]+)"', response.text)
                title = title_match.group(1) if title_match else f"Trailer {i}"
                
                # Check if this is likely to be a trailer
                is_likely_trailer = any(keyword.lower() in title.lower() for keyword in ["trailer", "teaser", "official"])
                
                trailer_results.append({
                    "index": i,
                    "title": title,
                    "url": video_url,
                    "thumbnail": thumbnail_url,
                    "video_id": video_id,
                    "is_likely_trailer": is_likely_trailer
                })
            
            return trailer_results
        except Exception as e:
            return [{"error": f"Error during movie trailer search: {str(e)}"}]

    async def _arun(self, query: str, num_results: int = 1) -> List[Dict[str, Any]]:

        """Run the movie trailer search tool asynchronously."""

        return self._run(query, num_results)