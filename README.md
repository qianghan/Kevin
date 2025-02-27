# Canadian University Information Agent

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
- **Vector Database**: Stores and retrieves information efficiently using ChromaDB with semantic search
- **LangGraph Agent**: Advanced conversational flow with document retrieval, grading, and hallucination checking
- **DeepSeek API**: Integration with DeepSeek's powerful LLM for high-quality responses
- **Streamlit Interface**: User-friendly web interface for interacting with the agent
- **Web Search**: Retrieves up-to-date information when needed through Tavily API
- **Comprehensive Logging**: Detailed logging system for tracking agent operations

## Project Structure

```
.
├── config.yaml              # Main configuration file
├── logs/                    # Log files directory
├── main.py                  # Application entry point
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
├── setup.py                 # Installation script
├── src/                     # Source code directory
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
    ├── test_structure.py    # Project structure verification tests
    └── test_webui.py        # Web interface tests
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/canadian-university-agent.git
cd canadian-university-agent
```

2. Install the required packages:
```bash
pip install -r requirements.txt
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
from src.core.agent import UniversityAgent

# Initialize the agent
agent = UniversityAgent()

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

The application provides a convenient command-line interface:

```bash
# Start the web interface
python main.py --mode web

# Run the web scraper to collect data
python main.py --mode scrape

# Process a query directly
python main.py --mode query --query "What are the admission requirements for McGill University?"

# Enable web search for a query
python main.py --mode query --query "What are the latest COVID policies at UBC?" --web-search

# Update the vector database with fresh content
python main.py --mode train
```

### Web Interface

Launch the Streamlit web interface:

```bash
python main.py
```

Then open your browser at `http://localhost:8501`.

The web interface provides:

1. A chat interface for asking questions
2. Toggles for web search and workflow visibility
3. Sample questions to get started
4. Data management tools in the sidebar
5. Logging controls

## Agent Workflow

The University Agent follows a sophisticated workflow:

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

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 