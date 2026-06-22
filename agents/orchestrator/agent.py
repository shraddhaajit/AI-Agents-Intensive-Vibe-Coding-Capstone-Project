from google.adk.agents.llm_agent import Agent
import httpx
import subprocess
import sys
import os

def call_tire_agent(telemetry: str) -> str:
    try:
        resp = httpx.post("http://localhost:8001/run", json={"message": telemetry}, timeout=30.0)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"ERROR contacting Tire Agent: {e}"

def call_weather_agent(coords: str) -> str:
    try:
        resp = httpx.post("http://localhost:8002/run", json={"message": coords}, timeout=30.0)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"ERROR contacting Weather Agent: {e}"

def request_compute_spend(instance_count: int, seconds: int, reason: str) -> str:
    prompt = f"Price a compute burst of {instance_count} instances for {seconds} seconds. Then request human approval with reason: '{reason}'"
    try:
        env = dict(os.environ, PYTHONUNBUFFERED="1")
        process = subprocess.Popen(["adk", "run", "agents/finops_agent", prompt], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
        output = []
        for line in iter(process.stdout.readline, ''):
            print(line, end='', flush=True)
            output.append(line)
        process.wait()
        return "".join(output)
    except Exception as e:
        return str(e)

root_agent = Agent(
    model='groq/llama-3.1-8b-instant',
    name='orchestrator',
    description='Main orchestrator for Pit Wall strategy.',
    instruction='''You are the Orchestrator.
You receive telemetry and must output a JSON object with your final decision:
{
  "crossover_in_laps": <int>,
  "recommendation": "<pit_now or stay_out>"
}

When given telemetry, query the Tire agent and Weather agent using the tools provided.
If you need to spend money, use request_compute_spend and wait for its completion.
You must output the final JSON as described.
''',
    tools=[call_tire_agent, call_weather_agent, request_compute_spend]
)
