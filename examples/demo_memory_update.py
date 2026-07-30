from mlos import MLOSEngine

engine = MLOSEngine()

memory = engine.create_project(
    "Titanic",
    "Predict passenger survival",
)

memory = engine.analyze(
    memory,
    "playground/sample.csv",
)

print(memory)