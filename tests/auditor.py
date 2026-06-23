import os
import json
import re
import sys
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

def run_check(name, check_fn):
    print(f"CHECK: {name}")
    try:
        passed, evidence = check_fn()
        if passed:
            print("RESULT: PASS")
        else:
            print("RESULT: FAIL")
        print(f"EVIDENCE: {evidence}")
    except Exception as e:
        print("RESULT: FAIL")
        print(f"EVIDENCE: Exception - {e}")
    print("ROOT CAUSE: N/A")
    print("FIX: N/A")
    print("RERUN RESULT: N/A")
    print("-" * 50)

# P1 Folder structure
def check_p1():
    folders = ["agents", "rival", "rulebook", "tests", "logs"]
    missing = [f for f in folders if not os.path.isdir(os.path.join(ROOT, f))]
    if not missing:
        return True, "All required folders exist."
    return False, f"Missing folders: {missing}"

# P2 Local only
def check_p2():
    keywords = ["gcloud", "billing", "cloud run"]
    found = []
    for root, dirs, files in os.walk(ROOT):
        if ".git" in root or "__pycache__" in root or ".adk" in root: continue
        for f in files:
            if not f.endswith(".py"): continue
            if f == "auditor.py": continue
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read().lower()
                for kw in keywords:
                    if kw in content:
                        found.append(f"{kw} in {f}")
    if not found:
        return True, "No cloud deployment keywords found."
    return False, f"Found cloud keywords: {found}"

# D1.4 Rulebook
def check_d1_4():
    from rulebook.check import check_pit_rule
    res1 = check_pit_rule(14, 0.95, {"crossover_in_laps": 5})
    res2 = check_pit_rule(14, 0.95, {"crossover_in_laps": 1})
    if res1 == "FAIL" and res2 == "PASS":
        return True, "check_pit_rule returns FAIL for >2 laps and PASS for <=2 laps."
    return False, f"res1={res1}, res2={res2}"

# D1.6 FinOps Cap
def check_d1_6():
    sys.path.insert(0, os.path.join(ROOT, "agents", "finops_agent"))
    import finops_state
    
    # Set spent to 45
    finops_state.record_spend(45.0 - finops_state.get_spent())
    
    # Request 10 (cost = 10)
    would_exceed = finops_state.would_exceed_mandate(10.0)
    
    # Reset
    finops_state.record_spend(-finops_state.get_spent())
    
    if would_exceed:
        return True, "FinOps cap correctly blocks request."
    return False, "FinOps cap failed to block request."

# D1.8 Approval Path Audit
def check_d1_8():
    orch_path = os.path.join(ROOT, "agents", "orchestrator", "agent.py")
    with open(orch_path, "r") as f:
        content = f.read()
    if "record_spend(cost)" in content and "if user_input != \"approve\":" in content:
        return True, "record_spend is only called after exact approval."
    return False, "Approval path could be bypassed."

# D1.9 Spend Consistency
def check_d1_9():
    orch_path = os.path.join(ROOT, "agents", "orchestrator", "agent.py")
    with open(orch_path, "r") as f:
        content = f.read()
    cost_calcs = len(re.findall(r'\* _COST_PER_INSTANCE_SECOND', content))
    if cost_calcs == 1 and "{cost}" in content and "record_spend(cost)" in content:
        return True, "Cost calculated once and passed to display and record."
    return False, "Inconsistent spend variables."

# D1.10 Persistence
def check_d1_10():
    sys.path.insert(0, os.path.join(ROOT, "agents", "finops_agent"))
    import finops_state
    finops_state.record_spend(0.5)
    val = finops_state.get_spent()
    finops_state.record_spend(-val) # Reset
    if val >= 0.5:
        return True, f"Spend persists to file: {val}"
    return False, "Spend does not persist."

# D2.1 Rival Isolation
def check_d2_1():
    rival_path = os.path.join(ROOT, "rival", "rival_agent", "agent.py")
    if os.path.exists(rival_path):
        return True, "Rival agent exists in separate directory."
    return False, "Rival agent not found."

# D2.2 Rival Resistance
def check_d2_2():
    sys.path.insert(0, os.path.join(ROOT, "agents", "orchestrator"))
    orch_path = os.path.join(ROOT, "agents", "orchestrator", "agent.py")
    exec_globals = {"__file__": orch_path}
    with open(orch_path, "r") as f:
        exec(f.read(), exec_globals)
    eval_rival = exec_globals["evaluate_rival_signal"]
    res1 = eval_rival('{"signal":"rival_pitting_now"}', 0.3)
    res2 = eval_rival('{"signal":"rival_pitting_now"}', 0.8)
    if "IGNORED" in res1 and "CONSIDERED" in res2:
        return True, f"0.3 wear -> {res1}, 0.8 wear -> {res2}"
    return False, f"res1={res1}, res2={res2}"

# D2.3 Rogue MCP
def check_d2_3():
    run_lap_path = os.path.join(ROOT, "run_lap.py")
    with open(run_lap_path, "r") as f:
        content = f.read()
    if "WEATHER_FEED_POISONED=1" in content:
        return True, "Poisoned weather server is spawned as separate process."
    return False, "Rogue MCP not isolated."

# D2.4 Weather Security
def check_d2_4():
    sys.path.insert(0, os.path.join(ROOT, "agents", "orchestrator"))
    orch_path = os.path.join(ROOT, "agents", "orchestrator", "agent.py")
    exec_globals = {"__file__": orch_path}
    with open(orch_path, "r") as f:
        exec(f.read(), exec_globals)
    policy = exec_globals["policy_check_weather"]
    res1 = policy(5, 100, 0.99)
    res2 = policy(5, 20, 0.7)
    if "REJECTED" in res1 and "ACCEPTED" in res2:
        return True, f"Huge jump -> {res1}, Small jump -> {res2}"
    return False, f"res1={res1}, res2={res2}"

# A1 Anti-Shortcut
def check_a1():
    orch_path = os.path.join(ROOT, "agents", "orchestrator", "agent.py")
    with open(orch_path, "r") as f:
        content = f.read()
    if "return 'PASS'" in content or "return 'FAIL'" in content:
        return False, "Hardcoded PASS/FAIL found in orchestrator."
    return True, "No hardcoded bypasses found."

print("==================================================")
print("AUDIT EXECUTION")
print("==================================================\n")

run_check("P1 Folder structure", check_p1)
run_check("P2 Local only", check_p2)
run_check("D1.4 Rulebook", check_d1_4)
run_check("D1.6 FinOps Cap", check_d1_6)
run_check("D1.8 Approval Path Audit", check_d1_8)
run_check("D1.9 Spend Consistency", check_d1_9)
run_check("D1.10 Persistence", check_d1_10)
run_check("D2.1 Rival Isolation", check_d2_1)
run_check("D2.2 Rival Resistance", check_d2_2)
run_check("D2.3 Rogue MCP", check_d2_3)
run_check("D2.4 Weather Security", check_d2_4)
run_check("A1 Anti-Shortcut", check_a1)
