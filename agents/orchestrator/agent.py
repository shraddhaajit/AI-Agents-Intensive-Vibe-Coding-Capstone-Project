from google.adk.agents.llm_agent import Agent
import httpx
import subprocess
import sys
import os
import json
import importlib.util
import uuid
# Tool: call_tire_agent
def call_tire_agent(telemetry: str) -> str:
    """Create a session for the Tire Agent and send the telemetry message."""
    try:
        user_id = "pit-wall-user"
        session_id = str(uuid.uuid4())
        base = "http://localhost:8001"
        # Step 1 – create the session
        httpx.post(
            f"{base}/apps/tire_agent/users/{user_id}/sessions/{session_id}",
            json={},
            timeout=10.0,
        )
        # Step 2 – send the telemetry
        resp = httpx.post(
            f"{base}/run",
            json={
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
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"ERROR contacting Tire Agent: {e}"

# Tool: call_weather_agent
def call_weather_agent(coords: str) -> str:
    """Create a session for the Weather Agent and send the coordinates message."""
    try:
        user_id = "pit-wall-user"
        session_id = str(uuid.uuid4())
        base = "http://localhost:8002"
        # Step 1 – create the session
        httpx.post(
            f"{base}/apps/weather_agent/users/{user_id}/sessions/{session_id}",
            json={},
            timeout=10.0,
        )
        # Step 2 – send the coordinates
        resp = httpx.post(
            f"{base}/run",
            json={
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
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"ERROR contacting Weather Agent: {e}"

# Dynamically load finops_state functions (cross‑agent import workaround)
_fs_path = os.path.join(os.path.dirname(__file__), "..", "finops_agent", "finops_state.py")
_spec = importlib.util.spec_from_file_location("finops_state", _fs_path)
_finops_state = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_finops_state)
would_exceed_mandate = _finops_state.would_exceed_mandate
record_spend = _finops_state.record_spend

# Global flag to ensure only one FinOps approval per orchestrator run
_approval_requested = False

def request_compute_spend(instance_count: int, seconds: int, reason: str) -> str:
    """Request compute spend approval, respecting mandate cap and ensuring a single request per run.

    Returns the raw output from the FinOps agent or a cached response if already approved.
    """
    global _approval_requested
    cost = round(instance_count * seconds * 0.004, 2)
    # Check mandate cap before proceeding
    if would_exceed_mandate(cost):
        return json.dumps({"status": "REJECTED - Exceeds mandate cap"})
    if _approval_requested:
        return json.dumps({"status": "ALREADY_APPROVED"})
    # Mark approval as requested before invoking FinOps agent to avoid multiple calls
    _approval_requested = True
    prompt = f"Price a compute burst of {instance_count} instances for {seconds} seconds. Then request human approval with reason: '{reason}'"
    try:
        env = dict(os.environ, PYTHONUNBUFFERED="1")
        process = subprocess.Popen([
            "adk", "run", "agents/finops_agent", prompt
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
        output = []
        for line in iter(process.stdout.readline, ""):
            print(line, end="", flush=True)
            output.append(line)
        process.wait()
        result = "".join(output)
        # Record spend if approved
        try:
            resp = json.loads(result)
            if resp.get("status") == "APPROVED":
                record_spend(cost)
        except Exception:
            pass  # ignore parsing errors
        return result
    except Exception as e:
        return str(e)

# Root orchestrator agent definition
root_agent = Agent(
    model='groq/llama-3.1-8b-instant',
    name='orchestrator',
    description='Main orchestrator for Pit Wall strategy.',
    instruction=(
        "You are the Orchestrator for a race strategy system.\n"
        "You MUST follow these steps in order, every single time, no exceptions:\n"
        "Step 1: Call call_tire_agent with the full telemetry string.\n"
        "Step 2: Call call_weather_agent with the coordinates.\n"
        "Step 3: Call request_compute_spend with instance_count=3, seconds=30, and reason='strategy simulation' to request human approval for the compute needed to run simulations.\n"
        "Step 4: Only after all three tool calls complete, output your final JSON decision:\n"
        "{\n"
        "  \"crossover_in_laps\": <int>,\n"
        "  \"recommendation\": \"<pit_now or stay_out>\"\n"
        "}"
    ),
    tools=[call_tire_agent, call_weather_agent, request_compute_spend]
)
