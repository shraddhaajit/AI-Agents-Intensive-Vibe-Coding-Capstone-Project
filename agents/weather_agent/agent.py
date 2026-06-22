from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='groq/llama-3.1-8b-instant',
    name='weather_agent',
    description='Checks weather using the NOAA MCP server.',
    instruction='You check the weather forecast using the NOAA MCP server. Use the get_precipitation tool.',
    mcp_servers=["agents/weather_mcp/weather_server.py"]
)
