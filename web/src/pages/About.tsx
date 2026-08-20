import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/Card";

export const About: React.FC = () => {
  return (
    <div className="py-16 px-6 max-w-3xl mx-auto space-y-12 select-none text-left">
      <div className="text-center space-y-3">
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-sans">
          About ML-OS
        </h1>
        <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed text-center">
          Building a transparent operating system that makes machine learning understandable and reproducible.
        </p>
      </div>

      <Card className="bg-card/45 border-border p-6">
        <CardHeader className="p-0 pb-3 border-b border-border/10 mb-4">
          <CardTitle className="text-sm font-semibold tracking-tight text-foreground">The Vision</CardTitle>
        </CardHeader>
        <CardContent className="p-0 text-xs text-muted-foreground leading-relaxed space-y-4">
          <p>
            Traditional machine learning tools act as monolithic code compilation wrappers, hiding the decisions, trade-offs, and empirical logic behind algorithms. Engineers are presented with finished models and scores, but lack explanation maps.
          </p>
          <p>
            ML-OS establishes an <strong>open-spec lifecycle kernel</strong>. It forces every pipeline stage (understand, prepare, plan, build) to communicate through a shared blackboard state (Project Memory), outputting clean Python code modules and exposing explainability reasoning.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
export default About;
