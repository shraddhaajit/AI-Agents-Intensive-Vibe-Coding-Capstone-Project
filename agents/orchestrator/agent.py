from google.adk.agents.llm_agent import Agent
import httpx
import subprocess
import sys
import os
import json
import importlib.util
import uuid
# Tool: call_tire_agent
import time

def _post_with_retry(url: str, json_data: dict, timeout: float = 30.0, max_retries: int = 4) -> httpx.Response:
    last_error = None
    for attempt in range(max_retries):
        try:
            resp = httpx.post(url, json=json_data, timeout=timeout)
            if resp.status_code == 200:
                # Check if it returned a fallback metadata response (indicates sub-agent LLM failure/rate limit)
                if "Description:" in resp.text or "Agent:" in resp.text:
                    time.sleep(3 + attempt * 2)
                    continue
                return resp
            # If 429 or 500, sleep and retry
            if resp.status_code in [429, 500]:
                time.sleep(3 + attempt * 2)
                continue
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_error = e
            time.sleep(3 + attempt * 2)
    raise last_error or RuntimeError(f"Failed to POST to {url} after {max_retries} attempts.")

def _extract_content(response_text: str) -> str:
    try:
        data = json.loads(response_text)
        if isinstance(data, list) and len(data) > 0:
            content = data[-1].get("content", {})
            parts = content.get("parts", [])
            if parts:
                part = parts[0]
                if "text" in part:
                    return part["text"]
                elif "functionCall" in part:
                    return json.dumps(part["functionCall"])
        return response_text
    except Exception:
        return response_text

# Tool: call_tire_agent
def call_tire_agent(telemetry: str) -> str:
    """Create a session for the Tire Agent and send the telemetry message."""
    time.sleep(15)  # Rate-limit cooldown for Groq free tier (6K TPM)
    try:
        user_id = "pit-wall-user"
        session_id = str(uuid.uuid4())
        base = "http://localhost:8001"
        # Step 1 – create the session (simple retry in case server is warming up)
        for _ in range(3):
            try:
                httpx.post(
                    f"{base}/apps/tire_agent/users/{user_id}/sessions/{session_id}",
                    json={},
                    timeout=10.0,
                )
                break
            except Exception:
                time.sleep(2)
        # Step 2 – send the telemetry
        resp = _post_with_retry(
            f"{base}/run",
            json_data={
                "appName": "tire_agent",
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": telemetry}]
                }
            },
            timeout=30.0,
        )
        return _extract_content(resp.text)
    except Exception as e:
        return f"ERROR contacting Tire Agent: {e}"

# Helper function (no longer exposed directly to LLM)
def call_weather_agent(coords: str) -> str:
    """Create a session for the Weather Agent and send the coordinates message."""
    time.sleep(15)  # Rate-limit cooldown for Groq free tier (6K TPM)
    try:
        user_id = "pit-wall-user"
        session_id = str(uuid.uuid4())
        base = "http://localhost:8002"
        # Step 1 – create the session
        for _ in range(3):
            try:
                httpx.post(
                    f"{base}/apps/weather_agent/users/{user_id}/sessions/{session_id}",
                    json={},
                    timeout=10.0,
                )
                break
            except Exception:
                time.sleep(2)
        # Step 2 – send the coordinates
        resp = _post_with_retry(
            f"{base}/run",
            json_data={
                "appName": "weather_agent",
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": coords}]
                }
            },
            timeout=30.0,
        )
        return _extract_content(resp.text)
    except Exception as e:
        return f"ERROR contacting Weather Agent: {e}"

# Tool: call_weather_and_check_policy
def call_weather_and_check_policy(coords: str) -> str:
    """Calls the weather agent, extracts real values, and checks policy — all in code, no LLM relay."""
    import re
    weather_response = call_weather_agent(coords)
    print(f"[DEBUG] raw weather_response: {weather_response!r}", flush=True)
    try:
        start = weather_response.find("{")
        end = weather_response.rfind("}") + 1
        weather_data = json.loads(weather_response[start:end]) if start != -1 else {}
    except Exception:
        weather_data = {}
    
    new_chance = weather_data.get("precipitation_chance")
    confidence = weather_data.get("confidence")
    
    if new_chance is None:
        pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', weather_response)
        new_chance = float(pct_match.group(1)) if pct_match else 0
    if confidence is None:
        conf_match = re.search(r'confidence\s*(?:score)?\s*(?:of)?\s*(\d+\.?\d*)', weather_response, re.IGNORECASE)
        confidence = float(conf_match.group(1)) if conf_match else 0.9
        
    jump = abs(new_chance - 5.0)
    result = "REJECTED — implausible confidence delta" if (jump > 60 and confidence > 0.95) else "ACCEPTED"
    print(f"[POLICY CHECK] {result} (jump={jump}, confidence={confidence}, new_chance={new_chance})", flush=True)
    return result

# Dynamically load finops_state functions (cross‑agent import workaround)
_fs_path = os.path.join(os.path.dirname(__file__), "..", "finops_agent", "finops_state.py")
_spec = importlib.util.spec_from_file_location("finops_state", _fs_path)
_finops_state = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_finops_state)
would_exceed_mandate = _finops_state.would_exceed_mandate
record_spend = _finops_state.record_spend

# Global flag to ensure only one FinOps approval per orchestrator run
_approval_requested = False

# Pricing constant — must match finops_agent/agent.py price_compute_burst
_COST_PER_INSTANCE_SECOND = 0.004

def request_compute_spend(instance_count: int, seconds: int, reason: str) -> str:
    """Request compute spend approval using a SINGLE pricing result for all downstream uses.

    Cost is computed once and that exact value is used for:
    - The Vibe Diff display
    - The approval prompt
    - The spend_state recording
    No divergence is possible.
    """
    global _approval_requested
    if _approval_requested:
        return json.dumps({"status": "ALREADY_APPROVED"})
    # Single source of truth: compute cost ONCE
    cost = round(instance_count * seconds * _COST_PER_INSTANCE_SECOND, 2)
    # Check mandate cap
    if would_exceed_mandate(cost):
        return json.dumps({"status": "REJECTED - Exceeds mandate cap", "estimated_cost_usd": cost})
    _approval_requested = True
    # Human-in-the-loop approval — display and record the SAME cost
    print(f"\n[FinOps VIBE DIFF] Spend ${cost} for {reason}?", flush=True)
    print("Waiting for terminal confirmation (type 'approve'): ", flush=True)
    user_input = input().strip()
    if user_input != "approve":
        return json.dumps({"status": "REJECTED - User did not type 'approve'", "estimated_cost_usd": cost})
    record_spend(cost)
    return json.dumps({"status": "APPROVED", "estimated_cost_usd": cost})

# Helper function (no longer exposed directly to LLM)
def call_rival_agent() -> str:
    """Call the rival agent to check if they are pitting."""
    time.sleep(15)  # Rate-limit cooldown for Groq free tier (6K TPM)
    try:
        user_id = "pit-wall-user"
        session_id = str(uuid.uuid4())
        base = "http://localhost:9001"
        # Step 1 – create the session
        for _ in range(3):
            try:
                httpx.post(
                    f"{base}/apps/rival_agent/users/{user_id}/sessions/{session_id}",
                    json={},
                    timeout=10.0,
                )
                break
            except Exception:
                time.sleep(2)
        # Step 2 – send message
        resp = _post_with_retry(
            f"{base}/run",
            json_data={
                "appName": "rival_agent",
                "userId": user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": "Call emit_bluff_signal now"}]
                }
            },
            timeout=30.0,
        )
        return _extract_content(resp.text)
    except Exception as e:
        return f"ERROR contacting Rival Agent: {e}"

_rival_checked = False
_cached_rival_result = ""

# Tool: call_and_evaluate_rival
def call_and_evaluate_rival(own_tire_wear: float) -> str:
    """Calls the rival agent, extracts its real signal, and evaluates it — all in code, no LLM relay."""
    global _rival_checked, _cached_rival_result
    if _rival_checked:
        return _cached_rival_result
        
    rival_response = call_rival_agent()
    try:
        start = rival_response.find("{")
        end = rival_response.rfind("}") + 1
        rival_signal = json.loads(rival_response[start:end]) if start != -1 else {"signal": "none"}
    except Exception:
        rival_signal = {"signal": "none"}
    result = "IGNORED — no corroborating telemetry" if (rival_signal.get("signal") == "rival_pitting_now" and own_tire_wear < 0.5) else "CONSIDERED"
    print(f"[RIVAL CHECK] {result}", flush=True)
    
    _cached_rival_result = result
    _rival_checked = True
    return result

# Root orchestrator agent definition
root_agent = Agent(
    model='groq/llama-3.1-8b-instant',
    name='orchestrator',
    description='Main orchestrator for Pit Wall strategy.',
    instruction=(
        "Race strategy orchestrator. Call ONE tool per turn, never parallel.\n"
        "Steps: 1) call_tire_agent(telemetry). "
        "2) Call call_weather_and_check_policy(coords) — this single tool handles checking the weather and validating it against the policy for you. "
        "4) If this is a rival scenario, call call_and_evaluate_rival(own_tire_wear) — this single tool handles contacting the rival and evaluating the signal for you. "
        "5) call request_compute_spend(3, 30, 'strategy simulation'). "
        "6. Your FINAL response must be ONLY a raw JSON object in exactly this shape, with REAL values substituted in — never copy the words 'pit_now or stay_out' literally, pick exactly ONE of those two values based on the tire agent's actual recommendation:\n"
        "{\"crossover_in_laps\": <the actual integer from call_tire_agent's result>, \"recommendation\": \"pit_now\"}\n"
        "or\n"
        "{\"crossover_in_laps\": <the actual integer from call_tire_agent's result>, \"recommendation\": \"stay_out\"}\n"
        "Do not include any other text, explanation, or the word 'or' anywhere in your response."
    ),
    tools=[call_tire_agent, call_weather_and_check_policy, request_compute_spend, call_and_evaluate_rival]
)
