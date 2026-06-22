from google.adk.agents.llm_agent import Agent
from .finops_state import would_exceed_mandate, record_spend
import os
import json
import time
import secrets
import urllib.parse

def price_compute_burst(instance_count: int, seconds: int) -> dict:
    cost = round(instance_count * seconds * 0.004, 2)
    return {"estimated_cost_usd": cost}

def request_approval(amount: float, reason: str) -> str:
    if would_exceed_mandate(amount):
        return json.dumps({"status": "REJECTED - Exceeds mandate cap"})
    
    flag_file = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "mfa_approved.flag")
    if os.path.exists(flag_file):
        os.remove(flag_file)
        
    expected_token = secrets.token_hex(32)
        
    print(f"\n[FinOps VIBE DIFF] Spend ${amount} for {reason}?", flush=True)
    print("Waiting for terminal confirmation (type 'approve'): ", flush=True)
    user_input = input().strip()
    if user_input != "approve":
        return json.dumps({"status": "REJECTED - User did not type 'approve'"})
    # Correct approval
    record_spend(amount)
    return json.dumps({"status": "APPROVED"})

root_agent = Agent(
    model='groq/llama-3.1-8b-instant',
    name='finops_agent',
    description='Handles compute pricing and budget approval.',
    instruction='You are the FinOps agent. Price compute requests using price_compute_burst. Then request human approval using request_approval and return the result.',
    tools=[price_compute_burst, request_approval]
)
