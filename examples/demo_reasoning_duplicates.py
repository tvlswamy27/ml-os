from mlos import MLOSEngine
from mlos.reasoning.reasoning_engine import ReasoningEngine

engine = MLOSEngine()

engine.create_project(
    "Titanic",
    "Predict passenger survival",
)

engine.analyze("playground/sample.csv")

reasoning = ReasoningEngine()

recommendations = reasoning.reason(engine.get_memory())

for recommendation in recommendations:
    print(recommendation)
