from mlos import MLOSEngine

engine = MLOSEngine()

engine.create_project(
    "Titanic",
    "Predict passenger survival",
)

engine.analyze(
    "playground/sample.csv"
)

print(engine.get_memory())