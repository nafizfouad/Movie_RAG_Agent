"""
Utility functions for the RAG agent.
"""

import os
import json
from typing import Dict, Any, List, Optional

def parse_tool_output(output: str) -> Dict[str, Any]:

    """
    Parse the tool output to extract structured information.
    
    Args:
        output: The raw output string from a tool execution
        
    Returns:
        A dictionary with the parsed information
    """

    try:
        # First try to parse as JSON
        if isinstance(output, str):
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # If it's not valid JSON, return as is
                return {"raw_output": output}
        elif isinstance(output, dict):
            return output
        elif isinstance(output, list):
            return {"results": output}
        else:
            return {"raw_output": str(output)}
    except Exception as e:
        return {"error": f"Error parsing tool output: {str(e)}", "raw_output": str(output)}

def format_movie_info(movie_info: Dict[str, Any]) -> str:

    """
    Format movie information for display.
    
    Args:
        movie_info: A dictionary containing movie information
        
    Returns:
        A formatted string with the movie information
    """

    if not movie_info or "error" in movie_info:
        return f"Error retrieving movie information: {movie_info.get('error', 'Unknown error')}"
    
    # Start with the title and year
    title = movie_info.get("title", "Unknown Title")
    year = movie_info.get("release_year", "Unknown Year")
    
    formatted = f"# {title} ({year})\n\n"
    
    # Add IMDb rating if available
    if movie_info.get("imdb_rating"):
        formatted += f"**IMDb Rating:** {movie_info['imdb_rating']}/10\n\n"
    
    # Add genre if available
    if movie_info.get("genre"):
        formatted += f"**Genre:** {movie_info['genre']}\n\n"
    
    # Add director if available
    if movie_info.get("director"):
        formatted += f"**Director:** {movie_info['director']}\n\n"
    
    # Add synopsis if available
    if movie_info.get("synopsis"):
        formatted += f"### Synopsis\n{movie_info['synopsis']}\n\n"
    
    # Add sources
    if movie_info.get("sources"):
        formatted += "### Sources\n"
        for source in movie_info["sources"]:
            formatted += f"- [{source.get('title', 'Source')}]({source.get('url', '')})\n"
    
    return formatted

def format_trailer_results(trailer_results: List[Dict[str, Any]]) -> str:

    """
    Format trailer search results for display.
    
    Args:
        trailer_results: A list of dictionaries containing trailer information
        
    Returns:
        A formatted string with the trailer information
    """

    if not trailer_results:
        return "No trailer results found."
    
    if isinstance(trailer_results, list) and "error" in trailer_results[0]:
        return f"Error retrieving trailers: {trailer_results[0].get('error', 'Unknown error')}"
    
    formatted = "# Available Trailers\n\n"
    
    for trailer in trailer_results:
        title = trailer.get("title", "Unknown Title")
        url = trailer.get("url", "#")
        is_likely_trailer = trailer.get("is_likely_trailer", False)
        
        trailer_tag = " (Official Trailer)" if is_likely_trailer else ""
        
        # Create embedded YouTube link with thumbnail
        video_id = trailer.get("video_id", "")
        if video_id:
            thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            formatted += f"## [{title}{trailer_tag}]({url})\n"
            formatted += f"[![Trailer Thumbnail]({thumbnail})]({url})\n\n"
        else:
            formatted += f"## [{title}{trailer_tag}]({url})\n\n"
    
    return formatted

def log_interaction(query: str, response: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:

    """
    Log an interaction for display in the session history.
    
    Args:
        query: The user's query
        response: The assistant's response
        tool_calls: Optional list of tool calls made during the interaction
        
    Returns:
        A dictionary with the interaction log
    """

    interaction = {
        "query": query,
        "response": response,
        "timestamp": import_datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    if tool_calls:
        interaction["tool_calls"] = tool_calls
    
    return interaction

import datetime

# Create an alias to avoid the circular import problem
import_datetime = datetime