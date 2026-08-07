from pathlib import Path

from mlos import MLOSEngine

engine = MLOSEngine()

engine.create_workspace(
    name="ML-OS Workspace",
    root_path=Path("playground/demo_workspace"),
)

print("Workspace created successfully!")
