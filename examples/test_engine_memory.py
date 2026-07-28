from mlos import MLOSEngine

engine = MLOSEngine()

memory = engine.create_project(
    name="Titanic",
    goal="Predict passenger survival",
)

print(memory)