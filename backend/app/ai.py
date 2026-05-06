import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_infra(prompt: str, infra_type: str):

    full_prompt = f"""
You are a senior DevOps engineer.

Generate ONLY valid {infra_type} configuration.

Rules:
- production-ready
- secure defaults
- no markdown
- no explanations
- return only code

User request:
{prompt}
"""

    response = model.generate_content(full_prompt)

    return response.text