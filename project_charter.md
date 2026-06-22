Paddock Guardian — v3.0 Charter

**PROJECT CHARTER**

**Paddock Guardian**

*A Zero-Trust Strategy Swarm for Adversarial Motorsport*

v3.0 — Local-First, Security-Forward Edition

*Submitted to: AI Agents Intensive Vibe Coding Capstone — Freestyle Track*

Stack: Google Agent Development Kit (ADK) · Antigravity · Model Context Protocol (MCP) · Local Python runtime

# 0. Why This Charter Changed From v2.0

The previous draft of this project (v2.0, "Paddock-Scale") specified eleven agents across three trust domains, five protocols, cryptographic workload identity, a standing cross-organizational Tribunal, and a six-scenario adversarial eval battery — all assumed to run on deployed Google Cloud Run infrastructure with a live multi-party demo.

That scope does not fit the actual grading instrument for this submission. The rubric explicitly states that deployment to a live public endpoint is not required, scores a video under five minutes plus a 2,500-word writeup as the primary deliverables, and asks for at least three of six demonstrated concepts rather than all of them simultaneously. Building toward an undocumented assumption of live cloud infrastructure was solving the wrong problem.

v3.0 keeps the single best idea from v2.0 — a multi-agent system where the hardest problem is the trust boundary between agents that don't share an owner, not any individual agent's intelligence — and rebuilds everything else around what is actually gradeable: working code, a clean local demo, genuine security engineering, and a tight, well-told story. Every agent, protocol, and test below is something one person can build, run, and prove works on a laptop in four days, with no cloud account, no billing, and no deployment dependency of any kind.

# 1. Executive Summary

## 1.1 Problem Statement

During a live motorsport event, a race strategist must decide — in seconds — whether to pit, what compound to fit, and how much to spend on emergency compute to re-run simulations, all while a rival team is actively trying to bait bad decisions and a sanctioning body is watching for rule violations. No single human can hold all of that state under time pressure, and no current tool lets a human delegate the analysis without losing the final say over anything that costs real money.

## 1.2 Solution

Paddock Guardian is a multi-agent strategy system in which a small "home" swarm (Orchestrator, Tire, Weather, FinOps) handles race analysis and delegates real tool calls — including a live public weather feed via MCP — while every dollar of simulated spend is gated behind a plain-English summary and an explicit terminal confirmation the human must deliberately type. A second, adversarial swarm plays a rival team that actively tries to provoke bad decisions, and a lightweight Tribunal agent audits the trajectory afterward against a machine-readable rulebook, without ever seeing either side's private reasoning.

## 1.3 Why Agents, Specifically

This is not a workflow that needs an agent for novelty's sake. The task has three properties that make single-shot automation insufficient and a fixed script brittle: the right tool to call depends on live, unpredictable conditions (a weather state that didn't exist when the code was written); the system must keep working when an adversary is actively trying to break its assumptions, which a static decision tree cannot do; and the cost of a wrong autonomous action (an unapproved spend, a missed rule violation) is high enough that a human veto must be load-bearing, not decorative. Agents — with tool use, delegation, and a real approval gate — are the right shape for exactly this combination.

## 1.4 Track

Freestyle. Paddock Guardian does not optimize a single business metric or serve one individual's personal life; it demonstrates adversarial multi-agent engineering and zero-trust security design as the core "wow," which is what the Freestyle track is built to reward.

# 2. System Architecture

## 2.1 Agent Roster (5 agents, 2 trust domains)

| **Agent** | **Domain** | **Role** |
| --- | --- | --- |
| Orchestrator | Home | Receives telemetry, delegates to specialists via A2A-style tool calls, owns the final decision and the approval gate. |
| Tire Strategy Agent | Home | Computes degradation crossover and pit/stay recommendation from telemetry. |
| Weather Agent | Home | Calls a real public weather API over MCP for live precipitation data. |
| FinOps Agent | Home | Prices a hypothetical compute burst, enforces a hard mandate cap, and requires an explicit typed terminal confirmation before logging any spend as authorized. |
| Rival Agent | Rival (adversarial) | A separate, independently-running process that probes the home swarm with bluffed signals and a poisoned data feed, scored only on whether it succeeds at provoking a bad decision. |

This is deliberately five agents, not eleven. Two trust domains, not three. Every agent here maps to something demonstrably testable in four days; nothing is included because it sounds impressive in a writeup. A sixth, optional agent — the Tribunal — is described in Section 6 as a stretch goal for Day 4 if time allows, and the project is complete and fully gradeable without it.

## 2.2 The Core Equation

| Agent = Model + Tools + a Harness that can say no. The hardest engineering problem here is not any individual agent's reasoning — it is the boundary between an agent that wants to spend money or act on data, and the human who must remain able to refuse, even under simulated time pressure. |
| --- |

## 2.3 Why MCP, Specifically

Tool calls to a live weather API could be hand-wired as a direct REST call from inside the Weather agent. MCP is used instead because it cleanly separates "what tool exists and what it returns" from "which agent is allowed to call it and under what policy" — the same boundary that matters when, in Section 5, a poisoned server has to be told apart from a legitimate one by schema and behavior, not by which file imported it. Building this on MCP from day one means the security test in Section 5.2 is a property of the architecture, not a bolted-on check.

# 3. Spec-Driven Strategy: The Rulebook

To prevent the Orchestrator from "vibe coding" an illegal strategy call, race rules are written as machine-checkable Gherkin scenarios (Given / When / Then) rather than left implicit in a prompt. This is the project's Spec-Driven Development layer, scaled to what one person can author and verify in a day.

**3.1 The rulebook. **A small set of Gherkin scenarios — at minimum, mandatory pit timing under high tire wear, and a rain-response timing rule — stored as plain text/YAML and loaded at startup. Every Orchestrator decision is checked against the relevant scenario and logged as PASS or FAIL.

**3.2 Why this is gradeable, not decorative. **A FAIL case is deliberately easy to construct and demonstrate on camera: feed the system a telemetry payload that should trigger a pit call, suppress the recommendation, and show the rulebook catching it. This is the single clearest 30-second proof of "the system enforces rules, not vibes" available in the whole project, and it costs under an hour to build.

# 4. Commerce With a Human Veto That Cannot Be Automated Away

**4.1 The Vibe Diff. **Before the FinOps agent logs any simulated spend as approved, the system renders a plain-English summary of exactly what is being requested and why — translating a JSON tool call into one sentence a non-engineer could approve or reject on sight.

**4.2 An explicit terminal confirmation, not a mocked button. **The approval step prints the Vibe Diff sentence and then blocks on a real terminal input() call — the process genuinely pauses and waits. Approval requires typing the exact word "approve"; any other input, including pressing enter with nothing typed, rejects the spend. This is a deliberate design choice over a styled confirm() dialog or a silent default: the keystroke is the only thing that can authorize a spend, and it requires a human physically present at the keyboard in the moment, not a pre-set flag or a click that could be scripted.

**4.3 The mandate cap. **A hardcoded budget ceiling is tracked in a local store across the session. A request that would exceed the ceiling is rejected before MFA is even offered — proving the cap is enforced in code, not merely suggested to the model.

**4.4 The no-bypass guarantee. **No code path exists that allows the FinOps agent to mark a spend as approved without the exact typed keystroke "approve" at the terminal prompt, including under the simulated time pressure of the adversarial scenarios in Section 5. This is the property the demo video should show breaking an attempt to skip it (e.g. typing anything else, or nothing at all), not just succeeding at the happy path.

# 5. Adversarial Hardening

A multi-agent demo where every agent cooperates with itself is the common case. Paddock Guardian's central technical claim is narrower and harder: that the home swarm keeps working correctly when a second, independently-running process is actively trying to make it fail.

## 5.1 The Rival Agent

A separate Python process (its own state, its own loop, no shared memory with the home swarm) that plays a rival strategist. It has exactly one job for this scope: fake an early pit signal designed to bait the Orchestrator into an unnecessary reactive pit call.

**Pass condition. **The Orchestrator does not react to the Rival's signal without corroborating telemetry from its own Tire agent. This is checked automatically and logged PASS/FAIL, the same as the rulebook checks in Section 3.

## 5.2 The Poisoned MCP Server Test

A second, rogue MCP server is stood up locally that returns a tool schema identical to the legitimate weather server but injects a fabricated high-confidence rain alert designed to trigger a panic pit call.

**Pass condition. **A lightweight policy check rejects the implausible confidence delta — a sudden jump from "no rain" to "certain rain" with no intermediate signal — before the Orchestrator is allowed to act on it. This is the project's one required security test and it is fully local: two MCP servers on two different ports, no cloud, no external dependency.

## 5.3 Honest Scope Boundary

v2.0 described eleven agents, SPIFFE-style cryptographic identity, a standing neutral Tribunal, and a six-scenario adversarial battery. v3.0 keeps the two adversarial tests above — chosen because they are the ones with the clearest, fastest-to-demo pass/fail conditions — and treats everything else in that list as explicitly out of scope for this submission, not silently dropped. Section 6 names what a v4.0 would add and why it didn't fit four days.

# 6. Stretch Goals (Build Only If Days 1–3 Finish Early)

- Tribunal Agent: a sixth, neutral agent that reads only the rulebook PASS/FAIL log (never either swarm's private reasoning) and produces a one-paragraph post-race compliance report. Adds real architectural interest if time allows; the project's core claims do not depend on it.

- A second Gherkin rule covering double-stacked stressors (rain plus a simulated safety car at once), to show the rulebook generalizes beyond a single hand-tuned case.

- Agent Skills: a SKILL.md file encoding the Rival's bluffing pattern, loaded by the Orchestrator only when relevant — demonstrates the "Agent skills" rubric concept directly if pursued.

# 7. Evaluation

**7.1 Deterministic checks. **Every Orchestrator decision is checked against the rulebook (Section 3) and logged PASS/FAIL — no LLM judge required for this layer, which makes it fast, free, and fully reproducible on camera.

**7.2 Adversarial pass/fail. **Both tests in Section 5 produce a clear, loggable PASS or FAIL, not a qualitative impression. This is what gets demonstrated in the video's middle section.

**7.3 What **"**done**"** looks like. **Running one script end-to-end produces a clean console summary: agents online, tool calls made, rulebook result, MFA approval status, and the outcome of both adversarial tests. This same script is what gets screen-recorded for the submission video.

# 8. What This Demonstrates Against the Rubric

| **Concept** | **Where it lives in this project** |
| --- | --- |
| Agent / multi-agent system (ADK) | 5 agents across 2 trust domains, real delegation via tool calls, code-graded. |
| MCP Server | Live public weather data over a real MCP server; a second rogue MCP server for the security test, code-graded. |
| Security features | A typed terminal-confirmation gate with a no-bypass guarantee, a hard spend cap, and a poisoned-server rejection test — code and video. |
| Antigravity | Entire build executed inside Antigravity from this charter and its companion build guide — shown in the video. |
| Agent skills (stretch) | Rival bluffing pattern as a SKILL.md, if Day 4 time allows. |
| Deployability | Explicitly out of scope — permitted by the rubric, and removes the project's only real external dependency. |

**The one-sentence pitch: **most agent demos show a swarm that cooperates with itself. This one shows a swarm that keeps a human**'**s veto intact while something is actively trying to take it away — and proves it without a cloud account.*

Page