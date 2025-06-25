import streamlit as st
import requests
import json
import os

from dotenv import load_dotenv



if st.secrets._secrets: 
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    # Load from .env for local development
    from dotenv import load_dotenv
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found. Please set it in .env (for local) or Streamlit Secrets (for deployed).")
    st.stop()

GROQ_MODEL = "llama3-70b-8192"

PRODUCTS_JSON = "products.json"

# Helper functions to load/save product data

def load_products():
    if not os.path.exists(PRODUCTS_JSON):
        return {"products": []}
    with open(PRODUCTS_JSON, "r") as f:
        return json.load(f)

def save_products(data):
    with open(PRODUCTS_JSON, "w") as f:
        json.dump(data, f, indent=2)

def generate_product_copy(category, tags, brand_tone):
    prompt = f"""
Generate a Shopify product title and description.

Product Category: {category}
Tags: {", ".join(tags)}
Brand Tone: {brand_tone}

Instructions:
- Title must be under 80 characters.
- Description should naturally include the tags.
- Highlight fabric, style, and best use-case.
- Keep the brand tone in mind: {brand_tone}.
- Use the category and tags only to create the content.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error {response.status_code}: {response.text}"


products_data = load_products()
products = products_data.get("products", [])

st.set_page_config(page_title="Dynamic Shopify Content Generator", layout="centered")
st.title("Product Title & Description Generator")

if not products:
    st.error("No products found in products.json. Please add some and restart.")
    st.stop()


product_names = [p["name"] for p in products]
selected_product_name = st.sidebar.selectbox("Select Product", product_names)
product_idx = product_names.index(selected_product_name)
product = products[product_idx]


st.markdown("### Product Category")
st.text_input("Category", value=product["category"], key="category", disabled=True)


st.markdown("### Tags (comma-separated)")
tags_str = st.text_area("Tags", value=", ".join(product["tags"]), height=120)


st.markdown("### Brand Tone")
selected_tone = st.selectbox("Select Brand Tone", product.get("brand_tones", []))


new_tone = st.text_input("Add New Brand Tone")
if st.button("Add Tone"):
    nt = new_tone.strip()
    if nt and nt not in product["brand_tones"]:
        product["brand_tones"].append(nt)
        selected_tone = nt
        st.success(f"Added new tone '{nt}'")
        # Save change immediately
        products[product_idx] = product
        save_products(products_data)
        st.experimental_rerun()
    elif nt in product["brand_tones"]:
        st.info(f"Tone '{nt}' already exists.")
    else:
        st.warning("Enter a valid tone.")


if st.button("Save Tags & Tone"):
    # Save tags (split by comma)
    new_tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    product["tags"] = new_tags
    product["brand_tones"] = product.get("brand_tones", [])

    if selected_tone not in product["brand_tones"]:
        product["brand_tones"].append(selected_tone)
    # Save to JSON
    products[product_idx] = product
    save_products(products_data)
    st.success("Product data saved!")

st.markdown("---")


if st.button("Generate Title & Description"):
    with st.spinner("Generating content from Groq..."):
        result = generate_product_copy(
            product["category"],
            product["tags"],
            selected_tone
        )
    if result:
        parts = result.split("\n", 1)
        title = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else ""
        st.markdown("### Generated Title")
        st.success(title)
        st.markdown("### Generated Description")
        st.write(description)