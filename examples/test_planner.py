from mlos import MLOSEngine

engine = MLOSEngine()

tasks = engine.plan()

for task in tasks:
    print(f"{task.id} - {task.title}")