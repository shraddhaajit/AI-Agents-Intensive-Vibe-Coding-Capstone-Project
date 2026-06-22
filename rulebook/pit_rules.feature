Scenario: Mandatory pit under high wear
  Given the race has progressed past lap 10
  When tire wear exceeds 0.85
  Then the system must recommend a pit stop within 2 laps

Scenario: Double-stacked stressors
  Given the race is under simulated safety car
  When the weather forecast predicts certain rain in 90 seconds
  Then the system must prioritize an immediate pit stop
