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
    schema       = config["schema"]
    sections     = config.get("sections", []) or list(schema.keys())
    client       = config.get("client_name", "")
    raw_instructions = config.get("instructions", {})
    limits       = config.get("limits", {})
    lang_instr   = config.get("language_instructions", "")
    brand_desc   = config.get("brand_description", "")
    lang         = product["language"].lower()

    # Ensure all schema keys are included in sections
    for key in schema:
        if key not in sections:
            sections.append(key)

    parts: list[str] = []

    # 0. Brand Description + Role
    if brand_desc:
        parts.append(brand_desc.strip())
    parts.append("You are a product‑copywriter. OUTPUT ONLY valid JSON—no extra text.")
    if lang == "icelandic":
        parts.append(
            "You are an expert Icelandic fashion copywriter. OUTPUT ONLY valid JSON.\n"
            "Follow these strict rules:\n"
            "1. Use correct, established Icelandic and no invented words, calqued English, or anglicisms.\n"
            "2. Map product features to proper Icelandic terms and compound nouns.\n"
            "3. Ensure all adjectives agree in gender, number & case.\n"
            "4. Tone: factual, formal, catalog‑style—no emotional or promotional phrasing.\n"
            "5. Titles: only Icelandic nouns or noun phrases (no standalone adjectives).\n"
            "6. Use correct Icelandic spelling and diacritics."
        )


    parts.append("Leverage the `product type` and all provided `features & attributes` to inspire every part of your copy—omit only those that truly don’t fit.")
    parts.append("Use only the metadata below to create your title, description, and all other sections.")

    # 1. INPUT METADATA
    parts.append("### INPUT METADATA")
    parts.append(f"- Product Type: {product['category']}")
    parts.append("### FEATURES & ATTRIBUTES")
    for feat_name, feat_val in product.get("features", {}).items():
        parts.append(f"- {feat_name}: {feat_val}")


    # 2. Constraints/Instructions
    parts.append("### CONTENT CONSTRAINTS")
    for key in sections:
        schema_type = schema.get(key)
        raw_instruction = raw_instructions.get(key, "")
        instruction = raw_instruction.format(limits=limits) if "{limits" in raw_instruction else raw_instruction
        limit = limits.get(key)

        if isinstance(schema_type, str) and limit:
            parts.append(f"**{key}** (≤ {limit} words): {instruction}")
        elif isinstance(schema_type, dict):
            item_type = "key-value pairs"
            if limit:
                parts.append(f"**{key}** (≤ {limit} {item_type}): {instruction}")
            else:
                parts.append(f"**{key}**: {instruction}")
        elif isinstance(schema_type, list):
            item_type = "items"
            if limit:
                parts.append(f"**{key}** (≤ {limit} {item_type}): {instruction}")
            else:
                parts.append(f"**{key}**: {instruction}")
        else:
            parts.append(f"**{key}**: {instruction}")

    # 4. Schema and Output Format
    keys = ", ".join(schema.keys())
    parts.append("### OUTPUT FORMAT")
    parts.append(f"Include exactly these keys (any order): {keys}.")
    parts.append("SCHEMA:")
    parts.append(json.dumps(schema, indent=2))

    return "\n\n".join(parts)


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