import * as React from "react";
import { CodeViewer } from "../components/CodeViewer";

export const Docs: React.FC = () => {
  const codeSample = `from mlos.sdk.project import MLProject

# 1. Initialize project
project = MLProject(
    dataset_path="data/titanic.csv",
    target_column="Survived",
    project_path="./workspace/titanic"
)

# 2. Run the automated ML lifecycle
session = project.run()

# 3. Retrieve evaluation metrics
print("Accuracy:", project.metrics())`;

  return (
    <div className="py-16 px-6 max-w-4xl mx-auto space-y-12 select-none">
      <div className="text-center space-y-3">
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-sans">
          Developer Documentation
        </h1>
        <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
          Learn how to integrate ML-OS SDK inside your automated model training pipelines and scripts.
        </p>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-foreground text-left">SDK Code Integration</h3>
        <CodeViewer code={codeSample} language="python" title="QuickStart Example" />
      </div>
    </div>
  );
};
export default Docs;
