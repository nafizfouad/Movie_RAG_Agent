# Movie RAG Agent

A Retrieval Augmented Generation (RAG) system that searches for and provides information about movies and TV shows. The agent can search the web for details, extract IMDb ratings and release dates, and find YouTube trailers.

## Features

- **Web Search Integration**: Uses DuckDuckGo to search for information
- **YouTube Search**: Finds relevant videos and trailers
- **Movie Information Extraction**: Gets IMDb ratings, release dates, and more
- **Interactive GUI**: Built with Streamlit for easy interaction
- **Session History**: Displays the conversation and tool calls history

## Setup Instructions

### Prerequisites

- Python 3.9+ installed
- OpenAI API key
- YouTube Data API key (optional, for enhanced YouTube functionality)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nafizfouad/Movie-RAG-Agent.git
   cd Movie-RAG-Agent
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   YOUTUBE_API_KEY=your_youtube_api_key_here  # Optional
   ```

### Running the Application

1. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

2. Open your web browser and navigate to `http://localhost:8501`

## Project Structure

- `app.py`: Main Streamlit application
- `rag/`: Module containing the RAG agent implementation
  - `agent.py`: Core RAG agent logic
  - `tools/`: Search and information retrieval tools
    - `search.py`: Web search functionality
    - `youtube.py`: YouTube search functionality
  - `utils.py`: Utility functions for formatting and parsing
- `data/`: Directory for storing data (e.g., vector database)
- `requirements.txt`: List of required Python packages

## Usage Examples

- **Movie Information**: "Tell me about Inception"
- **TV Show Details**: "What is the IMDb rating of Breaking Bad?"
- **Find Trailers**: "Show me trailers for The Matrix"
- **General Questions**: "Who directed Pulp Fiction?"

## Development Challenges

During the development of this project, several challenges were encountered:

1. **Information Extraction**: Extracting structured information from search results required careful parsing.
2. **Tool Error Handling**: Ensuring the agent gracefully handles tool failures.
3. **User Experience**: Balancing detailed information display with a clean interface.

## Future Improvements

- Add caching to reduce API calls for repeated queries
- Implement more specific movie data extraction (e.g., cast, genres)
- Add support for personalized recommendations
- Improve error handling and edge cases
- Enhance the UI with more interactive elements
- Add support for other languages