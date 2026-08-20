import * as React from "react";
import { ShieldCheck, FileCode, GraduationCap, Cpu } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/Card";

export const Features: React.FC = () => {
  const feats = [
    {
      title: "Automated Code Compilation",
      desc: "ML-OS compiles clean, human-inspectable Python source files instead of black-box binary blobs, guaranteeing deployability.",
      icon: <FileCode className="h-5 w-5 text-success" />,
    },
    {
      title: "Contextual ML Reasoning",
      desc: "Every preprocessor transformation and model selection is mapped to an explanation: what happened, why it matters, and warnings.",
      icon: <ShieldCheck className="h-5 w-5 text-primary" />,
    },
    {
      title: "Interactive ML Mentor",
      desc: "Explain Simply vs Technical modes help engineers audit algorithms and build conceptual intuition directly from run status states.",
      icon: <GraduationCap className="h-5 w-5 text-accent" />,
    },
    {
      title: "Local-First Architecture",
      desc: "Project memories, artifacts, and experiments are stored inside your project directories, maintaining absolute data privacy.",
      icon: <Cpu className="h-5 w-5 text-warning" />,
    },
  ];

  return (
    <div className="py-16 px-6 max-w-5xl mx-auto space-y-12 select-none">
      <div className="text-center space-y-3">
        <span className="text-[10px] font-mono text-primary font-bold uppercase tracking-wider">
          Core Capabilities
        </span>
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-sans">
          An Intelligent Engineering Environment
        </h1>
        <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
          Traditional AutoML runs silently and hides its logic. ML-OS makes every decision inspectable.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 pt-6">
        {feats.map((f, i) => (
          <Card key={i} className="bg-card/45 border-border hover:border-border/60 hover:bg-card/75 transition-all">
            <CardHeader className="flex flex-row items-center space-x-3 pb-2">
              <div className="p-2 rounded bg-secondary/50 border border-border/20">
                {f.icon}
              </div>
              <CardTitle className="text-sm font-semibold tracking-tight text-foreground">{f.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground text-left leading-relaxed">
                {f.desc}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
export default Features;
