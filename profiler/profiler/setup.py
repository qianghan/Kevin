from setuptools import setup, find_packages

setup(
    name="profiler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.22.0",
        "pyyaml>=6.0",
        "pytest>=7.3.1",
        "httpx>=0.24.0",
        "chromadb>=0.4.6",
        "pydantic>=1.10.7",
        "asyncio>=3.4.3",
        "python-dotenv>=1.0.0",
        "openai>=0.27.0",
        "langchain>=0.0.200",
        "numpy>=1.24.0",
        "pandas>=2.0.0"
    ],
    python_requires=">=3.8",
) 