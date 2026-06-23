def check_pit_rule(lap: int, tire_wear: float, recommendation: dict) -> str:
    if lap > 10 and tire_wear > 0.85:
        if recommendation.get("crossover_in_laps", 99) <= 2:
            return "PASS"
        return "FAIL - High tire wear requires immediate pit"
    return "PASS"

def check_rain_safety_car_rule(rain_chance: float, safety_car_active: bool, recommendation: dict) -> str:
    if rain_chance > 50.0 and safety_car_active:
        if recommendation.get("recommendation") == "pit_now":
            return "PASS"
        return "FAIL - Safety rules require immediate pit under rain + safety car conditions"
    return "PASS"
