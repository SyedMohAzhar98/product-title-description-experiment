# ---------- app.py ----------
import streamlit as st
import json, os
from generator.config_loader import load_client_config
from generator.example_loader import load_client_examples, get_example_for_category

# Early import check for API key errors
try:
    from generator.engine import generate_content
except RuntimeError as e:
    st.error(str(e))
    st.stop()

DATA_PATH = "data/products.json"

def load_products():
    if not os.path.exists(DATA_PATH):
        return {"products": []}
    return json.load(open(DATA_PATH, encoding="utf-8"))

st.set_page_config(page_title="Content Generator", layout="wide")
st.title("🛍️ Multi-Client Product Generator")

data = load_products()
if not data["products"]:
    st.error("No products found in data/products.json")
    st.stop()

# Sidebar controls
clients = sorted({p["client"] for p in data["products"]})
client = st.sidebar.selectbox("Client", clients)
client_prods = [p for p in data["products"] if p["client"] == client]
category = st.sidebar.selectbox("Category", sorted({p["category"] for p in client_prods}))
product = next(p for p in client_prods if p["category"] == category)

# Editable Tags
st.sidebar.markdown("---")
st.sidebar.markdown("**Tags**")
tags_str = st.sidebar.text_area("(comma-separated)", value=", ".join(product['tags']), height=100)
product['tags'] = [t.strip() for t in tags_str.split(",") if t.strip()]

# Editable Tone
st.sidebar.markdown("---")
st.sidebar.markdown("**Brand Tone**")
tone = st.sidebar.text_input("Tone", value=product['brand_tones'][0])
product['brand_tones'] = [tone]

# Word-limit overrides
st.sidebar.markdown("---")
st.sidebar.markdown("**Word Limits**")
config = load_client_config(client)
title_limit = st.sidebar.number_input("Title max words", min_value=1, value=config['title_word_limit'])
sub_limit = st.sidebar.number_input("Subtitle max words", min_value=0, value=config['subtitle_word_limit'])
desc_limit = st.sidebar.number_input("Description max words", min_value=20, value=config['description_word_limit'])
config.update({
    'title_word_limit': title_limit,
    'subtitle_word_limit': sub_limit,
    'description_word_limit': desc_limit
})

# Display selected metadata
st.markdown(f"**Client:** {client}")
st.markdown(f"**Category:** {product['category'].title()}")
st.markdown(f"**Tags:** {', '.join(product['tags'])}")
st.markdown(f"**Tone:** {tone}")

# Load examples and config
examples = load_client_examples(client)
example = get_example_for_category(examples, category)

# Generate and render
if st.button("Generate Title & Description"):
    with st.spinner("Calling LLM…"):
        raw = generate_content(product, config, example)
    # Parse JSON
    try:
        result = json.loads(raw)
    except Exception:
        st.error("❌ LLM did not return valid JSON:")
        st.code(raw)
    else:
        # Title & Subtitle
        st.markdown(f"**{result.get('title','')}**")
        subtitle = result.get('subtitle','')
        if subtitle:
            st.markdown(subtitle)

        # Product Details
        details = result.get('productDetails','')
        if details:
            st.markdown("### Product Details")
            st.write(details)

        # Design Elements
        design = result.get('designElements', {})
        if design:
            st.markdown("### Design elements")
            for key, val in design.items():
                st.write(f"{key}: {val}")

        # About the Fabric
        fabric = result.get('aboutTheFabric','')
        if fabric:
            st.markdown("### About the Fabric")
            st.write(fabric)
