# Pit Wall Project

## Overview

This repository implements a **Pit Wall** decision‑making system for a racing simulation. Agents communicate via the Google ADK framework:

- **Tire Agent** – evaluates tire wear and suggests a pit window.
- **Weather Agent** – fetches a short‑term weather forecast from the NOAA MCP server.
- **FinOps Agent** – prices compute bursts and enforces a spend‑mandate, gating actions behind a WebAuthn MFA approval step.
- **Orchestrator** – orchestrates the above agents to produce a final pit‑strategy JSON.

The project is deliberately lightweight: pure **Python** with the ADK, no additional web frameworks.

---

## Quick Setup

```bash
# Verify ADK is installed
adk --version

# (Optional) Create a virtualenv
python -m venv .venv && .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Day 1 Verification Table
The full verification steps are described in the `implementation_plan.md` artifact. Run each command in the terminal and watch the live output – **do not rely on summaries**.

---

## Project Layout
```
.
├─ .env                # **YOUR** live API key (ignored by git)
├─ .env.example        # Placeholder for sharing
├─ .gitignore          # Standard Python ignores + .env, logs/
├─ README.md           # This file
├─ agents/            
│   ├─ finops_agent/   # FinOps logic & MFA
│   ├─ orchestrator/   # Core orchestrator
│   ├─ tire_agent/     # Tire evaluation
│   └─ weather_agent/  # Weather forecast
├─ logs/               # Runtime logs, MFA flag, spend state
├─ run_lap.py          # End‑to‑end driver script
└─ tests/             # Unit tests (not required for Day 1)
```
---

## MFA Flow
When the FinOps agent needs approval it will **auto‑open** the approval URL in your default browser. You must complete the biometric prompt manually. The script will then resume once the correct token is written to `logs/mfa_approved.flag`.

---

## License
This is a demo project – feel free to modify and experiment.
