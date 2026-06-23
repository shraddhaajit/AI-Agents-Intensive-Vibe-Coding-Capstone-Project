from google.adk.agents.llm_agent import Agent

def summarize_compliance(scenario: str, result: str) -> str:
    """
    A structural tool for the Tribunal Agent to formally acknowledge the log.
    
    Role & Design Rationale:
    - Forces the LLM to extract the exact scenario and result from the raw rulebook log 
      to ensure it comprehends the data before generating its prose summary.
    
    Implementation Details:
    - Accepts the extracted scenario and result.
    - Returns an internal string instructing the LLM to proceed with generating 
      the final one-paragraph human-readable compliance summary.
    """
    return f"Data extracted successfully for {scenario} ({result}). Now synthesize this into a one-paragraph human-readable compliance summary."

root_agent = Agent(
    model='groq/llama-3.1-8b-instant',
    name='tribunal_agent',
    description='An independent auditor that produces a compliance summary based ONLY on the final rulebook log.',
    instruction=(
        "You are the independent Tribunal Agent. You will be provided with the raw JSON contents "
        "of the rulebook log. You must NEVER make assumptions about the swarm's private reasoning. "
        "Steps: 1) Call summarize_compliance(scenario, result) with the exact values from the log. "
        "2) Output your final, one-paragraph human-readable compliance summary explaining what "
        "happened in the scenario and whether it complied with safety regulations."
    ),
    tools=[summarize_compliance]
)
