import json, os

def load_client_config(client_name):
    path = os.path.join("config", f"{client_name.lower()}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config not found for client: {client_name}")
    return json.load(open(path, encoding="utf-8"))