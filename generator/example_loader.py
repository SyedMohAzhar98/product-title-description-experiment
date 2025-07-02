import json, os

def load_client_examples(client_name):
    path = os.path.join("examples", f"{client_name.lower()}_examples.json")
    print(f"Path ----{path}")
    if not os.path.exists(path):
        print(f"exists")
        return {}
    return json.load(open(path, encoding="utf-8"))

def get_example_for_category(examples, category):
    # first try exact match
    if category in examples:
        return examples[category]

    # then try case‑insensitive
    lower = category.lower()
    for key, val in examples.items():
        if key.lower() == lower:
            return val

    # nothing found
    return {}