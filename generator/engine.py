import os
import requests
import json
import openai
from dotenv import load_dotenv
from openai import OpenAI


# 1) Try Streamlit secrets
GROQ_API_KEY = None
try:
    import streamlit as _st
    # DEBUG: show what keys Streamlit actually has
    print("DEBUG: st.secrets keys =", list(_st.secrets.keys()))
    if "GROQ_API_KEY" in _st.secrets:
        GROQ_API_KEY = _st.secrets["GROQ_API_KEY"]
        print("DEBUG: Loaded GROQ_API_KEY from st.secrets")
except Exception as e:
    # will catch both ImportError and missing .secrets failures
    print("DEBUG: could not load from st.secrets:", e)

# 2) Fallback to .env
if not GROQ_API_KEY:
    load_dotenv()
    env_val = os.getenv("GROQ_API_KEY")
    print("DEBUG: Env GROQ_API_KEY exists?", bool(env_val))
    GROQ_API_KEY = env_val

    
# 3) Error if still missing
if not GROQ_API_KEY:
    raise RuntimeError(
        "⚠️ GROQ_API_KEY not set. "
        "Please add it to Streamlit Secrets (key = GROQ_API_KEY, value = your_key) "
        "or to a local .env file."
    )

GROQ_MODEL = "llama3-70b-8192"


OPENAI_API_KEY = None


try:
    import streamlit as _st
    # DEBUG: show what keys Streamlit actually has
    print("DEBUG: st.secrets keys =", list(_st.secrets.keys()))
    if "OPENAI_API_KEY" in _st.secrets:
        OPENAI_API_KEY = _st.secrets["OPENAI_API_KEY"]
        print("DEBUG: Loaded OPENAI_API_KEY from st.secrets")
except Exception as e:
    # will catch both ImportError and missing .secrets failures
    print("DEBUG: could not load from st.secrets:", e)

# 2) Fallback to .env
if not OPENAI_API_KEY:
    load_dotenv()
    env_val = os.getenv("OPENAI_API_KEY")
    print("DEBUG: Env OPENAI_API_KEY exists?", bool(env_val))
    OPENAI_API_KEY = env_val

    
# 3) Error if still missing
if not OPENAI_API_KEY:
    raise RuntimeError(
        "⚠️ OPENAI_API_KEY not set. "
        "Please add it to Streamlit Secrets (key = OPENAI_API_KEY, value = your_key) "
        "or to a local .env file."
    )



openai.api_key = OPENAI_API_KEY
GPT4O_MODEL = "gpt-4o"


def call_groq(prompt: str) -> str:
    headers = { "Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json" }
    payload = { "model": GROQ_MODEL, "messages":[{"role":"user","content":prompt}], "temperature": 0.7 }
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
                         headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    # content is already a JSON-formatted string
    return resp.json()["choices"][0]["message"]["content"]

def call_gpt4o(prompt: str) -> str:
    try:
        resp = openai.ChatCompletion.create(
            model=GPT4O_MODEL,
            messages=[{"role":"user","content":prompt}],
            temperature=0.7,
        )
    except Exception as e:
        raise RuntimeError(f"GPT-4o call failed: {e}")
    # content is already a JSON-formatted string
    return resp.choices[0].message.content

def call_gpt4o_mini(prompt: str) ->str:
    try:
        client = OpenAI(
            api_key=OPENAI_API_KEY
            )

        completion = client.chat.completions.create(
        model=GPT4O_MODEL,
        store=True,
        messages=[
            {"role": "user", "content": prompt}
        ]
        )
    except Exception as e:
        raise RuntimeError(f"GPT-4o call failed: {e}")
    # content is already a JSON-formatted string
    raw = completion.choices[0].message.content

    # Strip leading/trailing markdown code fences if present
    if raw.strip().startswith("```"):
        # remove first line ```json and last ```
        lines = raw.strip().splitlines()
        # if fence on first line, drop it
        if lines[0].startswith("```"):
            lines = lines[1:]
        # if fence on last line, drop it
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines)

    return raw


def build_prompt(product: dict, config: dict, example: dict) -> str:
    # JSON schema we expect back
    schema = {
      "title": "string",
      "subtitle": "string",
      "productDetails": "string",
      "designElements": {"<key>": "<value>"},
      "aboutTheFabric": "string"
    }
    ti = config["title_instructions"].format(**config)
    si = config["subtitle_instructions"].format(**config) if config.get("subtitle_instructions") else ""
    gi = config["global_instructions"]
    
    example_json = json.dumps(example, indent=2) if example else "{}"
    return f"""
You are writing for {config['client_name']} using an {gi} tone.

TITLE INSTRUCTIONS:
{ti}

SUBTITLE INSTRUCTIONS:
{si}

GLOBAL CONSTRAINTS:
• Title ≤ {config['title_word_limit']} words  
• Subtitle ≤ {config['subtitle_word_limit']} words  
• Description ≤ {config['description_word_limit']} words  
• designElements keys/values from Tags (1–4 words)

OUTPUT LANGUAGE:
Please write the entire output in {product['language']}.

INPUT:
Category: {product['category']}
Tags: {', '.join(product['tags'])}
Tone: {product['brand_tones'][0]}
Language: {product['language']}

EXAMPLE OUTPUT:
{example_json}

Respond ONLY with a VALID JSON object matching this schema:
{json.dumps(schema, indent=2)}
"""

def generate_content(product: dict, config: dict, example: dict) -> tuple[str,str]:
    prompt = build_prompt(product, config, example)
    lang = product.get("language","english").lower()
    
    if lang == "english":
        result = call_groq(prompt)
        model = "GROQ LLaMA 3 70B"
    else:
        result = call_gpt4o_mini(prompt)
        model = "OpenAI GPT-4o"
    
    return result, model

