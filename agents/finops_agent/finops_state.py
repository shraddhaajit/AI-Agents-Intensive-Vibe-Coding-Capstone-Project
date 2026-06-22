import json, os

MANDATE_CAP = 50.0
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "spend_state.json")

def get_spent():
    if not os.path.exists(STATE_FILE): return 0.0
    with open(STATE_FILE, "r") as f:
        return json.load(f).get("spent", 0.0)

def record_spend(amount):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    spent = get_spent()
    with open(STATE_FILE, "w") as f:
        json.dump({"spent": spent + amount}, f)

def would_exceed_mandate(amount):
    return (get_spent() + amount) > MANDATE_CAP
