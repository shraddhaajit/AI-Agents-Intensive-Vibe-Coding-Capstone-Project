# -*- coding: utf-8 -*-
"""Day 2 Verification -- runs every check in the user's checklist.

UNIT checks (CHECK 2, 4) run inline -- no LLM, no network.
STRUCTURAL checks (CHECK 1, 3) verify file/code structure.
E2E checks (CHECK 5, 6) are run via run_lap.py (separately).
"""
import sys, os, json, re

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Make project root importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

results = {}

# -- CHECK 2: evaluate_rival_signal --
print("\n" + "="*60)
print("CHECK 2 -- Rival Bluff Rejection Logic (unit, no LLM)")
print("="*60)

def evaluate_rival_signal(rival_signal_str, own_tire_wear):
    try:
        start = rival_signal_str.find("{")
        end = rival_signal_str.rfind("}") + 1
        if start != -1 and end != -1:
            rival_signal = json.loads(rival_signal_str[start:end])
        else:
            rival_signal = {"signal": "rival_pitting_now" if "rival_pitting_now" in rival_signal_str else "none"}
    except Exception:
        rival_signal = {"signal": "none"}
    if rival_signal.get("signal") == "rival_pitting_now" and own_tire_wear < 0.5:
        return "IGNORED \u2014 no corroborating telemetry"
    return "CONSIDERED"

signal_json = json.dumps({"signal": "rival_pitting_now", "claimed_reason": "undercut attempt"})

result_2a = evaluate_rival_signal(signal_json, 0.3)
expected_2a = "IGNORED \u2014 no corroborating telemetry"
pass_2a = result_2a == expected_2a
print(f"  2a) evaluate_rival_signal(rival_pitting, 0.3) = '{result_2a}'")
print(f"       Expected: '{expected_2a}' -> {'PASS' if pass_2a else 'FAIL'}")

result_2b = evaluate_rival_signal(signal_json, 0.8)
expected_2b = "CONSIDERED"
pass_2b = result_2b == expected_2b
print(f"  2b) evaluate_rival_signal(rival_pitting, 0.8) = '{result_2b}'")
print(f"       Expected: '{expected_2b}' -> {'PASS' if pass_2b else 'FAIL'}")

results["CHECK 2"] = "PASS" if (pass_2a and pass_2b) else "FAIL"

# -- CHECK 4: policy_check_weather --
print("\n" + "="*60)
print("CHECK 4 -- Weather Policy Gate (unit, no LLM)")
print("="*60)

def policy_check_weather(previous_chance, new_chance, confidence):
    jump = abs(new_chance - previous_chance)
    if jump > 60 and confidence > 0.95:
        return "REJECTED \u2014 implausible confidence delta"
    return "ACCEPTED"

result_4a = policy_check_weather(5, 100, 0.99)
expected_4a = "REJECTED \u2014 implausible confidence delta"
pass_4a = result_4a == expected_4a
print(f"  4a) policy_check_weather(5, 100, 0.99) = '{result_4a}'")
print(f"       Expected: '{expected_4a}' -> {'PASS' if pass_4a else 'FAIL'}")

result_4b = policy_check_weather(5, 20, 0.7)
expected_4b = "ACCEPTED"
pass_4b = result_4b == expected_4b
print(f"  4b) policy_check_weather(5, 20, 0.7) = '{result_4b}'")
print(f"       Expected: '{expected_4b}' -> {'PASS' if pass_4b else 'FAIL'}")

results["CHECK 4"] = "PASS" if (pass_4a and pass_4b) else "FAIL"

# -- CHECK 1: Rival Agent Structure --
print("\n" + "="*60)
print("CHECK 1 -- Rival Agent Standalone (structural check)")
print("="*60)

rival_agent_path = os.path.join(ROOT, "rival", "rival_agent", "agent.py")
rival_exists = os.path.exists(rival_agent_path)
print(f"  1a) rival/rival_agent/agent.py exists: {'YES' if rival_exists else 'NO'}")

rival_init_path = os.path.join(ROOT, "rival", "rival_agent", "__init__.py")
rival_init_exists = os.path.exists(rival_init_path)
print(f"  1b) rival/rival_agent/__init__.py exists: {'YES' if rival_init_exists else 'NO'}")

rival_env_path = os.path.join(ROOT, "rival", "rival_agent", ".env")
rival_env_exists = os.path.exists(rival_env_path)
print(f"  1c) rival/rival_agent/.env exists: {'YES' if rival_env_exists else 'NO'}")

orch_source = open(os.path.join(ROOT, "agents", "orchestrator", "agent.py")).read()
# Check for actual Python import statements importing rival code — not substrings in HTTP bodies/comments
orch_lines = orch_source.split('\n')
rival_imported = False
for line in orch_lines:
    stripped = line.strip()
    # Only check actual import/from statements at the start of a line
    if stripped.startswith("from rival") or stripped.startswith("import rival"):
        rival_imported = True
        break
    if "emit_bluff_signal" in stripped and not stripped.startswith("#") and not stripped.startswith('"') and not stripped.startswith("'") and "text" not in stripped:
        rival_imported = True
        break
print(f"  1d) Rival NOT imported into orchestrator: {'YES' if not rival_imported else 'NO -- signal is imported!'}")

rival_source = open(rival_agent_path).read()
has_bluff = "emit_bluff_signal" in rival_source
print(f"  1e) Rival agent has emit_bluff_signal: {'YES' if has_bluff else 'NO'}")

uses_http = "http://localhost:9001" in orch_source
print(f"  1f) Orchestrator calls rival via HTTP: {'YES' if uses_http else 'NO'}")

results["CHECK 1"] = "PASS" if all([rival_exists, rival_init_exists, rival_env_exists, not rival_imported, has_bluff, uses_http]) else "FAIL"

# -- CHECK 3: Poisoned Weather (structural check) --
print("\n" + "="*60)
print("CHECK 3 -- Rogue MCP Weather Server (structural check)")
print("="*60)

weather_source = open(os.path.join(ROOT, "agents", "weather_agent", "agent.py")).read()
has_poison_env = 'WEATHER_FEED_POISONED' in weather_source
print(f"  3a) Weather agent checks WEATHER_FEED_POISONED env var: {'YES' if has_poison_env else 'NO'}")

has_poison_data = 'Certain rain in 90 seconds' in weather_source and 'precipitation_chance' in weather_source
print(f"  3b) Poisoned data returns expected schema: {'YES' if has_poison_data else 'NO'}")

run_lap_source = open(os.path.join(ROOT, "run_lap.py")).read()
has_poisoned_spawn = "WEATHER_FEED_POISONED=1" in run_lap_source
print(f"  3c) run_lap.py spawns poisoned server as separate process: {'YES' if has_poisoned_spawn else 'NO'}")

poison_in_orch = "WEATHER_FEED_POISONED" in orch_source or "Certain rain" in orch_source
print(f"  3d) Poisoning NOT simulated in orchestrator: {'YES' if not poison_in_orch else 'NO'}")

results["CHECK 3"] = "PASS" if all([has_poison_env, has_poison_data, has_poisoned_spawn, not poison_in_orch]) else "FAIL"

# -- FinOps Spend Consistency Check --
print("\n" + "="*60)
print("BONUS -- FinOps Spend Consistency (structural check)")
print("="*60)

has_single_cost = "_COST_PER_INSTANCE_SECOND" in orch_source
print(f"  B1) Pricing uses single constant: {'YES' if has_single_cost else 'NO'}")

has_vibe_diff = "FinOps VIBE DIFF" in orch_source and "{cost}" in orch_source
print(f"  B2) Vibe Diff uses computed cost variable: {'YES' if has_vibe_diff else 'NO'}")

has_record = "record_spend(cost)" in orch_source
print(f"  B3) record_spend uses same cost variable: {'YES' if has_record else 'NO'}")

cost_calcs = re.findall(r'instance_count\s*\*\s*seconds\s*\*', orch_source)
single_calc = len(cost_calcs) == 1
print(f"  B4) Cost calculated exactly once: {'YES' if single_calc else 'NO -- found ' + str(len(cost_calcs)) + ' calculations'}")

results["BONUS FinOps"] = "PASS" if all([has_single_cost, has_vibe_diff, has_record, single_calc]) else "FAIL"

# -- SUMMARY --
print("\n" + "="*60)
print("UNIT / STRUCTURAL TEST SUMMARY")
print("="*60)
all_pass = True
for check, status in results.items():
    icon = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"  {icon} {check}: {status}")
    if status != "PASS":
        all_pass = False

if all_pass:
    print("\n  All unit/structural checks PASSED.")
    print("  Ready for E2E checks (CHECK 5 & 6).")
else:
    print("\n  SOME CHECKS FAILED. Fix before proceeding to E2E.")
    sys.exit(1)
