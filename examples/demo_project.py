from mlos import MLOSEngine

engine = MLOSEngine()

engine.create_project(
    name="Titanic",
    goal="Predict passenger survival",
)