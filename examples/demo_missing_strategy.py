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

for decision in decisions:
    print("=" * 50)
    print(decision.title)
    print("Strategy :", decision.strategy)
    print("Reason   :", decision.reason)
