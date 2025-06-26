import json, os

def load_client_examples(client_name):
    path = os.path.join("examples", f"{client_name.lower()}_examples.json")
    if not os.path.exists(path):
        return {}
    return json.load(open(path, encoding="utf-8"))

def get_example_for_category(examples, category):
    return examples.get(category, {})