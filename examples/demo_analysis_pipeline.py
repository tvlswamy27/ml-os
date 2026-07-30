from mlos import MLOSEngine

engine = MLOSEngine()

engine.create_project(
    "Titanic",
    "Predict passenger survival",
)

report = engine.run_analysis(
    "playground/sample.csv",
    target="Survived",
)

print(report.dataset)
print(report.decisions)
print(report.recommendations)
print(report.dataset.target)
