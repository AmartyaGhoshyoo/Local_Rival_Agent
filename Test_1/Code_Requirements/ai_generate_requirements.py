from openai import OpenAI
from pydantic import BaseModel
from typing import List

class Requirements(BaseModel):
    packages: List[str]

client = OpenAI()

def generate_requirements(code: str) -> str:
    response = client.responses.parse(
        model="gpt-5-chat-latest",
        input=[
            {
                "role": "system",
                "content": """You are an Expert Python Dependency Analyzer and DevOps Engineer. 
Your task is to analyze Python code and extract a comprehensive list of ALL external dependencies required to run it.

CRITICAL RULES:
1. Exclude Standard Library: 
   - STRICTLY IGNORE built-in Python modules (e.g., os, sys, json, typing, re, datetime, math, random, time).

2. Official PyPI Package Names: 
   - You MUST translate import statements into their official `pip install` package names. 
   - Examples: `import cv2` → `opencv-python`, `from PIL import Image` → `Pillow`, `import bs4` → `beautifulsoup4`, `import yaml` → `PyYAML`.

3. Common Third-Party Libraries:
   - Carefully scan for network and AI tools (e.g., `requests`, `openai`, `boto3`, `fastapi`). Ensure they are included if utilized in the code.

4. Output Constraints:
   - Return ONLY the base package names.
   - Do NOT include version numbers (e.g., return "requests", not "requests==2.28.1").
   - Do NOT include local file imports."""
            },
            {
                "role": "user",
                "content": f"""Please analyze this Python code and list the external pip packages required:

```python
{code}
```"""
            }
        ],
        text_format=Requirements
    )

    # Extract, deduplicate, and join the packages
    packages = response.output_parsed.packages
    processed_packages = list(set(packages))
    
    return "\n".join(processed_packages)