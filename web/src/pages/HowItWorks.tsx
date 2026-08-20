import * as React from "react";
import { Timeline } from "../components/Timeline";

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      id: "1",
      title: "01 Ingest & Analyze",
      status: "completed" as const,
      description: "Import dataset tables (CSV or Parquet) and parse column schemas, cardinalities, missing distributions, and class frequencies.",
    },
    {
      id: "2",
      title: "02 Preprocessing Decisions",
      status: "completed" as const,
      description: "The Decision Engine audits dataset telemetry to formulate feature transforms, target scaling, and imputation rules.",
    },
    {
      id: "3",
      title: "03 AutoML Model Battle",
      status: "active" as const,
      description: "Perform cross-validated hyperparameter searches across candidate model families (Random Forest, XGBoost, etc.) to evaluate scores.",
    },
    {
      id: "4",
      title: "04 Assembly & Execution",
      status: "waiting" as const,
      description: "Compile selected estimators and transforms into reproducible Python script pipelines and run local processes.",
    },
  ];

  return (
    <div className="py-16 px-6 max-w-3xl mx-auto space-y-12 select-none">
      <div className="text-center space-y-3">
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-sans">
          How ML-OS Operates
        </h1>
        <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
          Explore the unidirectional transition cycle from raw dataset to explainable, production-ready estimator.
        </p>
      </div>

      <div className="bg-card/35 rounded border border-border p-8 text-left">
        <Timeline steps={steps} />
      </div>
    </div>
  );
};
export default HowItWorks;
