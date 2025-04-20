from setuptools import setup, find_packages

setup(
    name="profiler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "psycopg2-binary",
        "pydantic",
        "pytest",
        "pytest-asyncio",
        "pytest-bdd",
        "aiohttp",
        "python-multipart",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "pyyaml",
        "uvicorn",
        "Pillow",
        "pytesseract",
        "pdf2image",
        "markdown",
        "fpdf"
    ],
    python_requires=">=3.8",
) 