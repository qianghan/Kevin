# Kevin

An AI-powered agent that provides accurate and up-to-date information about Canadian universities using web scraping, Retrieval-Augmented Generation (RAG), and LangGraph. This system helps prospective students explore programs, admission requirements, tuition costs, and scholarship opportunities across Canadian institutions.

## Project Overview

This project implements a modular, extensible information retrieval system with:

- **Conversational Interface**: Natural language interaction through chat UI
- **Dynamic Information Sources**: Combines pre-scraped data with real-time web search
- **Smart Workflow**: Evaluates document relevance and checks for hallucinations
- **Robust Architecture**: Modular design with comprehensive logging
- **Extensible Design**: Easy to add new universities or information sources

## Features

- **Web Scraping**: Collects information from top Canadian university websites and provincial application portals
- **Vector Database**: Stores and retrieves information efficiently using FAISS vector storage with semantic search
- **LangGraph Agent**: Advanced conversational flow with document retrieval, grading, and hallucination checking
- **DeepSeek API**: Integration with DeepSeek's powerful LLM for high-quality responses
- **Streamlit Interface**: User-friendly web interface for interacting with the agent
- **Web Search**: Retrieves up-to-date information when needed through Tavily API
- **Comprehensive Logging**: Detailed logging system for tracking agent operations
- **REST API**: FastAPI-based REST API with streaming capabilities for building custom applications
- **API-Based Web UI**: A Streamlit-based web interface that communicates with the REST API instead of directly using core modules

## System Architecture

The Kevin system is built around three core components that work together in a pipeline:

### Component Overview

1. **Scrape Component**
   - Crawls Canadian university websites to gather information
   - Processes HTML content into clean text documents
   - Saves documents to the `data/raw` directory for training

2. **Train Component**
   - Loads documents created by the scrape component
   - Cleans and chunks documents into smaller segments
   - Creates embeddings using HuggingFace models
   - Builds a FAISS vector database for efficient retrieval
   - Saves the vector database to `data/vectordb`

3. **RAG Component**
   - Loads the vector database created during training
   - Embeds user queries for semantic matching
   - Retrieves relevant documents based on query similarity
   - Generates accurate answers using retrieved context
   - Provides detailed, factual responses to user queries

### Pipeline Flow

```
┌────────────┐      ┌────────────┐      ┌────────────┐
│            │      │            │      │            │
│   Scrape   │─────▶│   Train    │─────▶│    RAG     │
│ Component  │      │ Component  │      │ Component  │
│            │      │            │      │            │
└────────────┘      └────────────┘      └────────────┘
     │                    │                   │
     ▼                    ▼                   ▼
┌────────────┐      ┌────────────┐      ┌────────────┐
│            │      │            │      │            │
│  Raw Data  │─────▶│   Vector   │─────▶│  Response  │
│            │      │  Database  │      │ Generation │
│            │      │            │      │            │
└────────────┘      └────────────┘      └────────────┘
```

### Detailed Data Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                  Scrape Component                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────────────┐    │
│  │             │         │             │         │                     │    │
│  │  WebScraper │────────▶│ HTML Parser │────────▶│ Document Generator  │    │
│  │             │         │             │         │                     │    │
│  └─────────────┘         └─────────────┘         └─────────────────────┘    │
│                                                            │                 │
└────────────────────────────────────────────────────────────┼─────────────────┘
                                                             │
                                                             ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                                  Train Component                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐      ┌─────────────┐      ┌──────────────────────┐     │
│  │                 │      │             │      │                      │     │
│  │ Document Reader │─────▶│ Text Chunker│─────▶│ Embedding Generator  │     │
│  │                 │      │             │      │                      │     │
│  └─────────────────┘      └─────────────┘      └──────────────────────┘     │
│                                                           │                  │
│                                                           │                  │
│  ┌─────────────────┐                                      │                  │
│  │                 │                                      │                  │
│  │  FAISS Vector   │◀─────────────────────────────────────┘                  │
│  │    Database     │                                                         │
│  │                 │                                                         │
│  └─────────────────┘                                                         │
│         │                                                                    │
└─────────┼────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                                   RAG Component                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐      ┌─────────────────┐      ┌─────────────────┐          │
│  │             │      │                 │      │                 │          │
│  │ Query Input │─────▶│ Query Embedding │─────▶│ Vector Retrieval│          │
│  │             │      │                 │      │                 │          │
│  └─────────────┘      └─────────────────┘      └─────────────────┘          │
│                                                        │                     │
│                                                        │                     │
│  ┌─────────────────┐      ┌─────────────────┐         │                     │
│  │                 │      │                 │         │                     │
│  │ Response Output │◀─────│ Answer Generator│◀────────┘                     │
│  │                 │      │                 │                               │
│  └─────────────────┘      └─────────────────┘                               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### File Structure and Data Storage

- **Scraper Output**: `data/raw/*.{txt,html,md}` - Raw document files with metadata
- **Training Output**: `data/vectordb/` - FAISS index files and metadata
- **RAG Input/Output**: Uses vectordb for retrieval and provides answers via CLI or API

### Integration Points

1. **Scraper to Training**: 
   - The scraper saves documents to `data/raw`
   - The `DocumentProcessor` in the training component loads these documents using loaders for different file types

2. **Training to RAG**:
   - Training creates a FAISS vector database in `data/vectordb`
   - The RAG engine loads this database during initialization
   - Both components use compatible embedding models to ensure proper retrieval

### Key Classes and Responsibilities

- **WebScraper**: Manages the entire scraping process for university websites
- **DocumentProcessor**: Handles document loading, cleaning, and database operations
- **Trainer**: Orchestrates the embedding and vector database creation process
- **CustomHuggingFaceEmbeddings**: Creates high-quality embeddings for documents
- **RAGEngine**: Manages retrieval and answer generation
- **SimpleEmbeddings**: Provides consistent embedding functionality for testing

Each component can be run independently through the command line interface, but they're designed to work together seamlessly in sequence.

## Project Structure

```
.
├── config.yaml              # Main configuration file
├── logs/                    # Log files directory
├── main.py                  # Application entry point
├── README.md                # Project documentation
├── pyproject.toml           # Project dependencies and metadata
├── setup.py                 # Installation script
├── src/                     # Source code directory
│   ├── api/                 # REST API implementation
│   │   ├── app.py           # FastAPI application
│   │   ├── models.py        # Pydantic data models
│   │   ├── routers/         # API route definitions
│   │   └── services/        # API service implementations
│   ├── core/                # Core application components
│   │   ├── agent.py         # LangGraph agent implementation
│   │   ├── agent_setup.py   # Agent configuration utilities
│   │   └── document_processor.py  # Document handling for RAG
│   ├── data/                # Data handling components
│   │   └── scraper.py       # Web scraper for university websites
│   ├── models/              # LLM and embedding models
│   │   └── deepseek_client.py  # DeepSeek API client
│   ├── utils/               # Utility modules
│   │   ├── logger.py        # Logging system
│   │   └── web_search.py    # Web search utility
│   └── web/                 # Web interface
│       └── app.py           # Streamlit application
└── tests/                   # Test directory
    ├── api/                 # API tests
    ├── test_structure.py    # Project structure verification tests
    └── test_webui.py        # Web interface tests
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/qianghan/Kevin.git
cd Kevin
```

2. Install the package and its dependencies:
```bash
pip install -e .
```

3. Set up your API keys in `.env` file:
```
DEEPSEEK_API_KEY=your_deepseek_api_key
TAVILY_API_KEY=your_tavily_api_key
```

4. Configure the application in `config.yaml` as needed.

## Main API Overview

The system provides several APIs for different use cases:

### Core Agent API

```python
from src.core.agent import Kevin

# Initialize the agent
agent = Kevin()

# Basic query
response = agent.query("What are the admission requirements for international students at UBC?")

# Query with web search enabled
response = agent.query(
    "What are the latest COVID-19 policies at McGill University?", 
    use_web_search=True
)
```

### Document Processing API

```python
from src.core.document_processor import DocumentProcessor

# Initialize the processor
processor = DocumentProcessor()

# Search for documents
documents = processor.search_documents(
    "scholarship requirements for international students",
    k=5  # Number of results to return
)

# Add new documents to the knowledge base
from langchain.schema import Document
processor.add_documents([
    Document(page_content="...", metadata={"source": "university website", "title": "..."})
])
```

### Web Scraping API

```python
from src.data.scraper import WebScraper

# Initialize the scraper
scraper = WebScraper()

# Scrape all universities defined in config
documents = scraper.scrape_all_universities()

# Scrape a specific university
university_config = {
    "name": "University of Toronto",
    "base_url": "https://www.utoronto.ca",
    "focus_urls": ["https://www.utoronto.ca/admissions", "https://www.utoronto.ca/academics"]
}
documents = scraper.scrape_university(university_config)
```

### DeepSeek LLM API

```python
from src.models.deepseek_client import DeepSeekAPI

# Initialize the DeepSeek client
llm = DeepSeekAPI()

# Generate a response
response = llm.invoke("What are the main features of Canadian universities?")

# Get embeddings
embedding = llm.get_embedding("Text to embed")
```

### Web Search API

```python
from src.utils.web_search import search_web

# Search the web for current information
documents = search_web(
    "recent changes to international student policies in Canada",
    max_results=5,
    search_depth="comprehensive"  # "basic" or "comprehensive"
)
```

## Usage Examples

### Command Line Interface

The application provides a convenient command-line interface with different modes that correspond to the three main components:

```bash
# 1. SCRAPE: Collect data from university websites
kevin --mode scrape                           # Scrape all universities in config
kevin --mode scrape --university "University of Toronto"  # Scrape specific university
kevin --mode scrape --max-pages 100           # Limit pages per university

# 2. TRAIN: Process documents and create vector database
kevin --mode train                            # Process all documents and create/update the vector database
kevin --mode train --force                    # Rebuild vector database from scratch

# 3. RAG: Run the RAG engine to answer questions
kevin --mode rag                              # Start interactive RAG session
kevin --mode query --query "What are the admission requirements for McGill University?"  # One-off query

# OTHER OPTIONS:
# Start the standard web interface (direct core integration)
kevin --mode web

# Start the REST API server
kevin --mode api                              # Run the API server with defaults
kevin --mode api --host localhost --port 8000   # Specify host and port
kevin --mode api --reload --debug             # Enable development mode

# Start the API-based web UI (connects to the API server)
kevin --mode webapi                           # Start the Web UI with defaults
kevin --mode webapi --host localhost --port 8501  # Specify host and port
kevin --mode webapi --api-url http://api-server:8000  # Connect to a different API server

# Enable web search for a query
kevin --mode query --query "What are the latest COVID policies at UBC?" --web-search
```

A typical workflow would involve running these commands in sequence:
1. First scrape university websites to collect raw data
2. Then train the system to create a vector database
3. Finally use the RAG mode to answer questions using the collected knowledge

### Web Interface

Launch the Streamlit web interface:

```bash
kevin --mode web
```

Then open your browser at `http://localhost:8501`.

The web interface provides:

1. A chat interface for asking questions
2. Toggles for web search and workflow visibility
3. Sample questions to get started
4. Data management tools in the sidebar
5. Logging controls

### REST API

Launch the FastAPI server:

```bash
kevin --mode api
```

Then access the API at `http://localhost:8000`. API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### API Endpoints Overview

The REST API provides the following endpoints:

**Chat Endpoints**
- `POST /api/chat/query`: Submit a chat query, with optional streaming
- `GET /api/chat/query/stream`: Stream a chat query with real-time updates
- `GET /api/chat/conversations/{conversation_id}`: Retrieve conversation history

**Search Endpoints**
- `GET /api/search/documents`: Search documents in the vector store
- `GET /api/search/web`: Search the web for information

**Document Endpoints**
- `GET /api/documents/get/{document_id}`: Retrieve a document by ID
- `GET /api/documents/url`: Retrieve a document by URL

**Admin Endpoints**
- `POST /api/admin`: Perform administrative actions
  - Rebuild the vector index
  - Clear caches
  - Get system status

**Utility Endpoints**
- `GET /api/health`: Check the API health
- `GET /`: Get API information

#### API Documentation

Kevin uses FastAPI's built-in OpenAPI specification generation to document the API. This provides:

1. **Interactive Documentation**: Swagger UI at `http://localhost:8000/docs` lets you try the API directly in your browser
2. **Alternative Documentation**: ReDoc at `http://localhost:8000/redoc` provides a more readable reference
3. **OpenAPI JSON**: The raw OpenAPI specification is available at `http://localhost:8000/openapi.json`

The OpenAPI specification includes:
- All available endpoints and operations
- Operation parameters (both required and optional)
- Authentication methods (when configured)
- Response schemas and examples
- Expected error responses

This documentation is automatically generated from the code, ensuring it's always up-to-date with the actual implementation.

#### Example API Usage

```python
import requests

# Base URL for the API
base_url = "http://localhost:8000"

# Chat query
response = requests.post(
    f"{base_url}/api/chat/query",
    json={
        "query": "What are the admission requirements for UBC?",
        "use_web_search": True,
        "stream": False
    }
)
print(response.json())

# Search documents
response = requests.get(
    f"{base_url}/api/search/documents",
    params={"query": "scholarship requirements", "limit": 5}
)
print(response.json())

# Admin action
response = requests.post(
    f"{base_url}/api/admin",
    json={"action": "get_system_status"}
)
print(response.json())
```

For streaming responses, use a streaming-compatible client:

```python
import requests
import json
import sseclient

# Issue a streaming request
response = requests.get(
    f"{base_url}/api/chat/query/stream",
    params={"query": "What are the admission requirements for UBC?", "use_web_search": True},
    stream=True
)

# Process the streaming response
client = sseclient.SSEClient(response)
for event in client.events():
    if event.event == "thinking_start":
        print("Thinking...")
    elif event.event == "answer_chunk":
        data = json.loads(event.data)
        print(data["chunk"], end="", flush=True)
    elif event.event == "done":
        print("\nDone!")
        break
```

### API-Based Web UI Architecture

The Kevin system provides a separation of concerns between the backend API and the frontend UI. This architecture allows for:

1. **Scalability**: The FastAPI backend can be deployed separately from the Streamlit UI
2. **Flexibility**: Multiple UIs can be developed that communicate with the same API
3. **Maintainability**: Backend logic changes don't require UI changes and vice versa

Here's how the components work together:

```
┌────────────────────────┐      ┌───────────────────────┐
│                        │      │                       │
│  Streamlit Web UI      │◄─────┤  FastAPI Backend      │
│  (src/web/api_app.py)  │      │  (src/api/app.py)     │
│                        │─────►│                       │
└────────────────────────┘      └───────────────────────┘
                                           │
                                           │
                                           ▼
                                 ┌───────────────────────┐
                                 │                       │
                                 │  Core Kevin System    │
                                 │  (src/core/*)         │
                                 │                       │
                                 └───────────────────────┘
```

#### Web UI Integration Flow

The API-based Web UI follows this flow:

1. **UI Initialization**:
   - Streamlit app connects to the FastAPI backend on startup
   - Health check confirms API availability
   - UI components are rendered based on API capabilities

2. **User Interaction**:
   - User enters a query in the chat interface
   - UI sends the query to the API with appropriate parameters
   - For streaming responses, SSE (Server-Sent Events) connection is established

3. **Real-time Updates**:
   - API streams thinking steps and answer chunks via SSE
   - UI displays "thinking" indicators during processing
   - Answer is displayed with typing animation as it's received
   - Documents are rendered as citations with proper formatting

4. **Conversation Management**:
   - Chat history is maintained and displayed from conversations API
   - Context is preserved between questions in the same conversation
   - UI supports creating new conversations or continuing existing ones

#### Starting the API-Based Web UI

To use the API-based Web UI, first start the FastAPI backend:

```bash
kevin --mode api
```

Then, in a separate terminal, start the Streamlit-based Web UI:

```bash
kevin --mode webapi
```

The Web UI will be available at `http://localhost:8501` and will connect to the API at `http://localhost:8000`.

If port 8501 is already in use, the system will automatically find an available port.

#### Backend Communication

The KevinApiClient class in `src/web/api_app.py` handles all communication with the backend API, providing:

- Regular (synchronous) query handling
- Streaming query handling with callback functions
- Document and web search functionality
- Conversation history retrieval
- Admin operations

This client abstracts away the API details, allowing the UI code to focus on presentation rather than communication logic.

## Agent Workflow

The Kevin agent follows a sophisticated workflow:

1. **Router** - Decides whether to search the knowledge base or the web based on the query
2. **Retriever** - Gets relevant documents from the chosen source
3. **Document Grader** - Assesses if the documents are relevant to the query
4. **Answer Generator** - Creates a response based on the relevant documents
5. **Hallucination Checker** - Ensures the response is factual and supported by documents
6. **Response Finalizer** - Delivers the answer and optionally updates the knowledge base

If documents from the knowledge base aren't relevant, the agent will automatically search the web.

## Configuration

### DeepSeek API Configuration

This agent uses the DeepSeek API for generating high-quality responses. To configure:

1. Get your API key from DeepSeek
2. Set it in your `config.yaml` file:
   ```yaml
   llm:
     provider: "deepseek"
     api_key: "your_api_key_here"
     model_name: "deepseek-chat"
     temperature: 0.1
     max_tokens: 1000
     fallback_to_huggingface: true
     fallback_model: "deepseek-ai/deepseek-coder-1.3b-base"
   ```
3. Or set it as an environment variable in your `.env` file:
   ```
   DEEPSEEK_API_KEY=your_api_key_here
   ```

### University Configuration

Add universities to scrape in the `config.yaml` file:

```yaml
universities:
  - name: "University of Toronto"
    base_url: "https://www.utoronto.ca"
    focus_urls:
      - "https://www.utoronto.ca/admissions"
      - "https://www.utoronto.ca/academics"
      - "https://www.utoronto.ca/tuition-fees"
  
  - name: "McGill University"
    base_url: "https://www.mcgill.ca"
    focus_urls:
      - "https://www.mcgill.ca/undergraduate-admissions"
      - "https://www.mcgill.ca/studentaid"
```

## Testing

Run the tests using:

```bash
python -m unittest tests/test_structure.py
python -m unittest tests/test_webui.py
```

The test suite includes:
- Structure tests that verify the project organization
- Web UI tests that verify the Streamlit interface
- Mock tests that don't require external dependencies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request to https://github.com/qianghan/Kevin.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Monorepo Structure

This repository is organized as a monorepo containing both the Kevin backend and the Next.js web UI:

- **Backend (root directory)**: The main Kevin AI backend built with FastAPI
- **Web UI (`/ui` directory)**: A modern Next.js web application that interfaces with the Kevin API

### Backend

The backend provides the core AI functionality, including:
- Chat API with streaming support
- Document management
- Search capabilities
- Admin functions

For more details on the backend, see the main README content above.

### Web UI

The web UI provides a modern interface for interacting with Kevin:
- Next.js-based frontend with TypeScript and Tailwind CSS
- Authentication with Google, Facebook, and email/password
- User roles (student and parent)
- Real-time chat with streaming responses
- MongoDB integration for storing users and chat sessions

To learn more about the web UI, see the [UI README](ui/README.md).

## Development

### Running the Backend

```bash
# Activate the virtual environment
source kevin_venv/bin/activate

# Run the backend
python -m src.main
```

### Running the Web UI

```bash
# Navigate to the UI directory
cd ui

# Install dependencies
npm install

# Run the development server
npm run dev
```

Visit http://localhost:3000 to access the web UI, which will connect to the backend running on http://localhost:8000. 