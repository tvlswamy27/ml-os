from mlos import MLOSEngine

engine = MLOSEngine()

dataset = engine.analyze(
    "playground/sample.csv"
)

print(dataset)