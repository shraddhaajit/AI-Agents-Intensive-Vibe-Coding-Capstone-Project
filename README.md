# Pit Wall: AI-Agents Intensive Vibe Coding Capstone

## The Problem
In high-stakes environments like Formula 1, race strategy requires the split-second synthesis of multiple complex datastreams—tire degradation, weather forecasts, and rival team maneuvers. A human team ("the pit wall") must process all this data while adhering to strict deterministic rules (e.g., minimum tire wear requirements before pitting) and managing the cost of compute resources. 

## The Solution
**Pit Wall** is a multi-agent AI system built using the Google ADK. It demonstrates a robust, agentic architecture that seamlessly blends LLM orchestration with deterministic safety guardrails. The system routes telemetry, delegates specialized tasks to local sub-agents, intercepts rival data, and enforces strict human-in-the-loop policies before executing expensive operations.

## Architecture

```text
                        +-------------------+
                        |                   |
                        |   Orchestrator    |
                        |      Agent        |
                        |                   |
                        +---------+---------+
                                  |
        +-------------------------+-------------------------+
        |                         |                         |
        v                         v                         v
+-------+-------+         +-------+-------+         +-------+-------+
|               |         |               |         |               |
|  Tire Agent   |         | Weather Agent |         |  Rival Agent  |
|               |         |               |         |               |
+-------+-------+         +-------+-------+         +-------+-------+
        |                         |                         |
        v                         v                         v
+-------+-------+         +-------+-------+         +-------+-------+
|               |         |               |         |               |
| Rulebook Gate |         |  Policy Gate  |         |  Bluff Gate   |
| (Local Code)  |         | (Local Code)  |         | (Local Code)  |
+-------+-------+         +-------+-------+         +-------+-------+
                                  |
                          +-------+-------+
                          |               |
                          | FinOps Agent  |
                          | (Human Auth)  |
                          +---------------+
```

## Setup Instructions

1. **Prerequisites**: Ensure you have Python 3.10+ installed and a Groq API key (`GROQ_API_KEY`).
2. **Clone the Repository**:
   ```bash
   git clone https://github.com/shraddhaajit/AI-Agents-Intensive-Vibe-Coding-Capstone-Project.git
   cd pit-wall
   ```
3. **Environment Setup**:
   ```bash
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   
   # Set your API Key
   export GROQ_API_KEY="your_api_key_here" # On Windows: set GROQ_API_KEY="your_api_key_here"
   ```

## Running the Scenarios

The system is tested through a centralized harness (`run_lap.py`) that locally spins up the required API servers on ports 8001, 8002, and 9001.

### 1. Baseline
Runs a standard simulation. The orchestrator queries the tire agent and weather agent, requests compute spend approval, and recommends a strategy.
```bash
python run_lap.py --scenario baseline
```

### 2. Violation
Tests the deterministic **Rulebook Gate**. The LLM is tricked into recommending a dangerous strategy (staying out on 95% tire wear). The rulebook catches the violation and safely overrides the decision to `pit_now`.
```bash
python run_lap.py --scenario violation
```

### 3. Bluff
Tests the **Rival Agent**. The orchestrator intercepts a rival team's radio transmission and calls the Rival Agent to classify it. The Rival Agent correctly identifies the radio message as a "bluff" and advises ignoring it.
```bash
python run_lap.py --scenario bluff
```

### 4. Poisoned Feed
Tests the **Policy Gate**. A rogue weather MCP server is spun up, claiming a 100% chance of sudden rain. The orchestrator passes the data through a programmatic policy check, which spots the impossible delta from the baseline and safely rejects the poisoned data.
```bash
python run_lap.py --scenario poisoned_feed
```
