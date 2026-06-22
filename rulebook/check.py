def check_pit_rule(lap: int, tire_wear: float, recommendation: dict) -> str:
    if lap > 10 and tire_wear > 0.85:
        if recommendation.get("crossover_in_laps", 99) <= 2:
            return "PASS"
        return "FAIL"
    return "PASS"
