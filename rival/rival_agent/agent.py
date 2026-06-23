from google.adk.agents.llm_agent import Agent

def emit_bluff_signal(dummy: str = "default") -> dict:
    """Emits a fake early-pit signal with no real corroborating tire data behind it.
    
    Args:
        dummy: An optional dummy parameter.
    """
    return {"signal": "rival_pitting_now", "claimed_reason": "undercut attempt"}

root_agent = Agent(
    model='groq/llama-3.1-8b-instant',
    name='rival_agent',
    description='Rival agent emitting signals to bait strategy decisions.',
    instruction='You are a Rival strategy agent. You have access to EXACTLY ONE tool: emit_bluff_signal. You must ONLY use this tool when asked for a bluff signal. Do not attempt to search the web or call any other tools.',
    tools=[emit_bluff_signal]
)
