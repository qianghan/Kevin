from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="canadian_university_agent",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI agent for retrieving Canadian university information",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/canadian-university-agent",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "uni-agent=main:main",
        ],
    },
) 