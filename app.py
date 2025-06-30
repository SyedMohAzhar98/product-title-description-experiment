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

# Editable Features
st.sidebar.markdown("---")
st.sidebar.markdown("**Features (key:value)**")
feat_lines = [f"{k}:{v}" for k,v in product.get("features", {}).items()]
feat_str = st.sidebar.text_area(
    "(one per line, format key:value)",
    value="\n".join(feat_lines),
    height=200
)
new_feats = {}
for line in feat_str.splitlines():
    if ":" in line:
        k, v = line.split(":", 1)
        new_feats[k.strip()] = v.strip()
product['features'] = new_feats

# Language selector
st.sidebar.markdown("---")
language = st.sidebar.selectbox("Language", ["English", "Icelandic"], index=0)
product['language'] = language

model_note = "GROQ LLaMA 3 70B" if language == "English" else "OpenAI GPT-4o"
st.sidebar.markdown(f"**↳ This language will use:** {model_note}")


# Word-limit overrides
st.sidebar.markdown("---")
st.sidebar.markdown("**Word Limits**")
config = load_client_config(client)

limits = config.get("limits", {})
new_limits = {}

for field, default in limits.items():
    label = f"{field.replace('_', ' ').title()} max words"
    min_val = 0 if field != "title" else 1
    new_limits[field] = st.sidebar.number_input(label, min_value=min_val, value=default)

config["limits"] = new_limits


config_path = f"config/{client.lower()}.json"
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

# Display selected metadata
st.markdown(f"**Client:** {client}")
st.markdown(f"**Category:** {product['category'].title()}")
st.markdown("**Features:**")
for k, v in product.get("features", {}).items():
    st.markdown(f"- **{k}**: {v}")


# Load examples and config
examples = load_client_examples(client)
example = get_example_for_category(examples, category)

# Generate and render
if st.button("Generate Title & Description"):
    with st.spinner("Calling LLM…"):
        raw, used_model = generate_content(product, config, example)
    # Parse JSON
    try:
        result = json.loads(raw)
    except Exception:
        st.error("❌ LLM did not return valid JSON:")
        st.code(raw)
        st.stop()
    else:
    # Render every field according to the client’s schema & sections
        st.info(f"Using model: **{used_model}**")

        # 1) Title (always first)
        st.markdown(f"**{result.get('title','')}**")

        # 2) Optional subtitle
        if "subtitle" in result and result["subtitle"]:
            st.markdown(result["subtitle"])

        # 3) Now render each of the remaining schema keys under the matching section heading
        schema    = config["schema"]
        sections  = config.get("sections", [])

        # build an ordered list of keys without title/subtitle
        remaining_keys = [k for k in schema.keys() if k not in ("title", "subtitle")]

        for section_name, key in zip(sections, remaining_keys):
            value = result.get(key)
            if not value:
                continue

            st.markdown(f"### {section_name}")

            # dict → key: value lines
            if isinstance(value, dict):
                for subk, subv in value.items():
                    st.write(f"{subk}: {subv}")

            # list → bullet list
            elif isinstance(value, list):
                for item in value:
                    st.write(f"- {item}")

            # string → plain paragraph
            else:
                st.write(value)