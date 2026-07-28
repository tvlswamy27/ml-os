from mlos import MLOSEngine

engine = MLOSEngine()

engine.create_project(
    "Titanic",
    "Predict passenger survival",
)

report = engine.run_analysis(
    "playground/sample.csv",
)

generated = engine.generator_engine.generate(
    report.decisions,
)

for code in generated:
    print(code)
