"""
Test Decision Engine.

Author: Vikram Tanakala
License: MIT
"""

from mlos.engine.engine import MLOSEngine

engine = MLOSEngine()

engine.create_project(
    "Titanic",
    "Predict passenger survival",
)

engine.analyze(
    "playground/sample.csv",
)

decisions = engine.decision_engine.decide(
    engine.get_memory(),
)

print(decisions)
