from google.adk.agents.llm_agent import Agent

def evaluate_tire_degradation(tire_wear: float, laps_remaining: int) -> dict:
    """
    Calculates the exact lap the tires will cross over the degradation cliff.

    Role & Design Rationale:
    - Offloads complex, deterministic math from the LLM. LLMs are notoriously bad at 
      arithmetic and threshold logic. By wrapping this in a strict Python tool, we 
      ensure the crossover lap is always mathematically correct based on telemetry.
    
    Implementation Details:
    - Calculates crossover as `max(1, int((1.0 - tire_wear) * 20))`.
    - Returns a strict JSON structure containing the crossover lap, a hard recommendation 
      to pit if crossover <= 3, and a tire compound suggestion.
    """
    crossover = max(1, int((1.0 - tire_wear) * 20))
    return {
        "crossover_in_laps": crossover,
        "recommendation": "pit_now" if crossover <= 3 else "stay_out",
        "compound_suggestion": "soft" if laps_remaining < 15 else "medium"
    }

root_agent = Agent(
    model='groq/llama-3.1-8b-instant',
    name='tire_agent',
    description='Evaluates tire degradation to recommend pit strategies.',
    instruction='You evaluate tire telemetry using the evaluate_tire_degradation tool and return the exact JSON result.',
    tools=[evaluate_tire_degradation]
)
