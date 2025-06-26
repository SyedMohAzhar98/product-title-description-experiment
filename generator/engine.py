import os
import requests
import json
from dotenv import load_dotenv

# 1) Try Streamlit secrets
GROQ_API_KEY = None
try:
    import streamlit as _st
    if "GROQ_API_KEY" in _st.secrets:
        GROQ_API_KEY = _st.secrets["GROQ_API_KEY"]
except ImportError:
    pass

# 2) Fallback to .env
if not GROQ_API_KEY:
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 3) Error if still missing
if not GROQ_API_KEY:
    raise RuntimeError(
        "⚠️ GROQ_API_KEY not set. "
        "Please add it to Streamlit Secrets (key = GROQ_API_KEY, value = your_key) "
        "or to a local .env file."
    )

GROQ_MODEL = "llama3-70b-8192"

def call_groq(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def build_prompt(product: dict, config: dict, example: dict) -> str:
    # JSON schema we expect back
    schema = {
      "title": "string",
      "subtitle": "string",
      "productDetails": "string",
      "designElements": {"<key>": "<value>"},
      "aboutTheFabric": "string"
    }
    example_json = json.dumps(example, indent=2) if example else "{}"
    return f"""
Generate product copy for {config['client_name']} and **output ONLY valid JSON** matching this schema:
{json.dumps(schema, indent=2)}

CONSTRAINTS:
• Title ≤ {config['title_word_limit']} words  
• Subtitle ≤ {config['subtitle_word_limit']} words  
• Each description ≤ {config['description_word_limit']} words  
• designElements keys & values must come from Tags (1–4 words each)

INPUT:
Category: {product['category']}
Tags: {', '.join(product['tags'])}
Tone: {product['brand_tones'][0]}

EXAMPLE OUTPUT:
{example_json}

Respond **only** with the JSON object—no extra text.
"""

def generate_content(product: dict, config: dict, example: dict) -> str:
    prompt = build_prompt(product, config, example)
    return call_groq(prompt)
