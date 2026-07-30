from mlos import MLOSEngine

engine = MLOSEngine()

engine.create_project(
    "Titanic",
    "Predict passenger survival",
)

# Load and analyze the dataset first
engine.run_analysis(
    "playground/sample.csv",
    target="Survived",
)

profile = engine.intelligence_engine.analyze(
    engine.project_memory,
)

print(profile)