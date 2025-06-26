import streamlit as st
import json, os
from generator.config_loader import load_client_config
from generator.example_loader import load_client_examples, get_example_for_category
from generator.engine import generate_content

DATA_PATH = "data/products.json"

def load_products():
    if not os.path.exists(DATA_PATH):
        return {"products": []}
    return json.load(open(DATA_PATH, encoding="utf-8"))

st.set_page_config(page_title="Content Generator", layout="wide")
st.title("🛍️ Multi-Client Product Generator")

data = load_products()
if not data["products"]:
    st.error("No products found.")
    st.stop()

# Sidebar: client, category, tags, tone, limits
clients = sorted({p["client"] for p in data["products"]})
client = st.sidebar.selectbox("Client", clients)
client_prods = [p for p in data["products"] if p["client"] == client]
category = st.sidebar.selectbox("Category", sorted({p["category"] for p in client_prods}))
product = next(p for p in client_prods if p["category"] == category)

# Tags & Tone
tags = st.sidebar.text_area("Tags (comma-separated)", ", ".join(product['tags']))
product['tags'] = [t.strip() for t in tags.split(",") if t.strip()]
tone = st.sidebar.text_input("Tone", value=product['brand_tones'][0])
product['brand_tones'] = [tone]

# Word-limit overrides
config = load_client_config(client)
title_limit = st.sidebar.number_input("Title words", 1, 20, config['title_word_limit'])
sub_limit   = st.sidebar.number_input("Subtitle words", 0, 20, config['subtitle_word_limit'])
desc_limit  = st.sidebar.number_input("Description words", 20, 500, config['description_word_limit'])
config.update({
    'title_word_limit': title_limit,
    'subtitle_word_limit': sub_limit,
    'description_word_limit': desc_limit
})

examples = load_client_examples(client)
example = get_example_for_category(examples, category)

# Generate
if st.button("Generate"):
    with st.spinner("Calling LLM…"):
        raw = generate_content(product, config, example)
    # parse JSON
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        st.error("❌ LLM did not return valid JSON:")
        st.code(raw)
    else:
        # display
        st.markdown(f"**{result['title']}**")
        if result.get('subtitle'):
            st.markdown(result['subtitle'])
        st.markdown("### Product Details")
        st.write(result['productDetails'])
        if result.get('designElements'):
            st.markdown("### Design elements")
            for key, val in result['designElements'].items():
                st.write(f"{key}: {val}")
        st.markdown("### About the Fabric")
        st.write(result['aboutTheFabric'])
