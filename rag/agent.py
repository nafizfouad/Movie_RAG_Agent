"""
RAG agent implementation.
"""
import os
from typing import Dict, Any, List, Optional, Tuple

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

from rag.tools import WebSearchTool, MovieInfoSearchTool, YouTubeSearchTool, MovieTrailerSearchTool
from rag.utils import parse_tool_output, format_movie_info, format_trailer_results

class MovieRAGAgent:
    """
    RAG agent for movie and TV show information retrieval.
    """
    
    def __init__(self, 
                openai_api_key: Optional[str] = None, 
                model_name: str = "gpt-4o-mini",
                temperature: float = 0.7):
        """
        Initialize the RAG agent.
        
        Args:
            openai_api_key: OpenAI API key (if None, will look for OPENAI_API_KEY env var)
            model_name: Name of the OpenAI model to use
            temperature: Temperature parameter for the model
        """
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Please set the OPENAI_API_KEY environment variable or pass it as a parameter.")
        
        # Initialize the tools
        self.tools = [
            WebSearchTool(),
            MovieInfoSearchTool(),
            YouTubeSearchTool(),
            MovieTrailerSearchTool()
        ]
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self.openai_api_key,
        )
        
        # Create the agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful movie and TV show information assistant. 
            You can search the web for information, find specific details about movies and TV shows, 
            and search for trailers on YouTube.
            
            When asked about a movie or TV show:
            1. First use the movie_info_search tool to get basic information about the title
            2. Then use the movie_trailer_search tool to find relevant trailers
            3. Combine the information and present it in a well-structured format
            
            For general queries, use the appropriate search tools and provide helpful, concise answers.
            
            Always be polite and helpful. If you don't know something, say so and offer to search for it.
            """),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}"),
        ])
        
        # Create the agent executor
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True  # Make sure we return all steps
        )
        
        # Store the conversation history
        self.conversation_history = []
        self.tool_calls_history = []
        
    def process_query(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process a user query and return the response.
        
        Args:
            query: The user's query
            
        Returns:
            A tuple containing (response, tool_calls)
        """
        tool_calls = []
        
        # Check if this is a movie or TV show query
        is_movie_query = any(keyword in query.lower() for keyword in 
                           ["movie", "film", "show", "series", "tv", "watch", 
                            "trailer", "actor", "actress", "director", "imdb", 
                            "rating", "plot", "synopsis", "cast"])
        
        # Add to conversation history
        self.conversation_history.append(HumanMessage(content=query))
        
        try:
            # Execute the agent
            result = self.agent_executor.invoke({"input": query})
            response = result.get("output", "I'm sorry, I couldn't process your request.")
            
            # Extract tool calls from the trace
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 2:
                        tool = step[0]
                        tool_output = step[1]
                        
                        tool_call = {
                            "tool": tool.tool,
                            "input": tool.tool_input,
                            "output": parse_tool_output(tool_output)
                        }
                        tool_calls.append(tool_call)
                        self.tool_calls_history.append(tool_call)
            
            # Format response for movie queries
            if is_movie_query and tool_calls:
                # Extract movie info and trailer results
                movie_info = None
                trailer_results = None
                
                for call in tool_calls:
                    if call["tool"] == "movie_info_search":
                        movie_info = call["output"]
                    elif call["tool"] == "movie_trailer_search":
                        trailer_results = call["output"]
                
                # If we have both movie info and trailers, format a structured response
                if movie_info and trailer_results:
                    formatted_movie_info = format_movie_info(movie_info)
                    formatted_trailers = format_trailer_results(trailer_results)
                    
                    # Adding a separator between movie info and trailers for better readability
                    structured_response = f"{formatted_movie_info}\n---\n\n{formatted_trailers}"
                    
                    # Only override if we have good structured data
                    if len(structured_response) > 100:
                        response = structured_response
            
            # Add to conversation history
            self.conversation_history.append(AIMessage(content=response))
            
            return response, tool_calls
        
        except Exception as e:
            error_message = f"I encountered an error while processing your request: {str(e)}"
            self.conversation_history.append(AIMessage(content=error_message))
            return error_message, tool_calls
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get the conversation history.
        
        Returns:
            A list of conversation messages
        """
        formatted_history = []
        
        for i, message in enumerate(self.conversation_history):
            if i % 2 == 0:  # Human message
                formatted_history.append({"role": "human", "content": message.content})
            else:  # AI message
                # Find the corresponding tool calls if any
                tool_calls_for_message = []
                if i // 2 < len(self.tool_calls_history):
                    tool_calls_for_message = self.tool_calls_history[i // 2]
                
                formatted_history.append({
                    "role": "ai", 
                    "content": message.content,
                    "tool_calls": tool_calls_for_message if tool_calls_for_message else None
                })
        
        return formatted_history