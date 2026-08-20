import * as React from "react";
import { useNavigate } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Brain, Terminal, BarChart2, Beaker, CheckCircle } from "lucide-react";
import { Button } from "../components/Button";

export const Home: React.FC = () => {
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();

  const lifecycleStages = [
    { id: "problem", label: "Problem", icon: <Brain className="h-4 w-4 text-primary" /> },
    { id: "dataset", label: "Dataset", icon: <BarChart2 className="h-4 w-4 text-accent" /> },
    { id: "analysis", label: "Analysis", icon: <Beaker className="h-4 w-4 text-success" /> },
    { id: "reasoning", label: "ML Reasoning", icon: <Terminal className="h-4 w-4 text-warning" /> },
    { id: "decision", label: "Decision", icon: <CheckCircle className="h-4 w-4 text-primary" /> },
    { id: "battle", label: "Model Battle", icon: <Brain className="h-4 w-4 text-accent" /> },
    { id: "pipeline", label: "Pipeline", icon: <Terminal className="h-4 w-4 text-success" /> },
    { id: "eval", label: "Evaluation", icon: <BarChart2 className="h-4 w-4 text-warning" /> },
    { id: "learn", label: "Learning", icon: <CheckCircle className="h-4 w-4 text-primary" /> },
  ];

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : 0.08,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { type: "spring" as const, stiffness: 100 },
    },
  };

  return (
    <div className="flex flex-col min-h-full">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 px-6 text-center select-none bg-gradient-to-b from-card/30 to-background">
        <div className="max-w-4xl mx-auto space-y-6">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="inline-flex items-center space-x-2 bg-secondary/60 border border-border/80 px-3 py-1 rounded-full text-[10px] font-mono text-primary font-medium tracking-wide uppercase"
          >
            <span>Platform Release v3.6</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight leading-none text-foreground font-sans"
          >
            Machine Learning, <br className="sm:hidden" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
              with a reasoning engine.
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.25 }}
            className="text-sm sm:text-base text-muted-foreground max-w-xl mx-auto leading-relaxed tracking-tight"
          >
            ML-OS turns your dataset and ML problem into an explainable, reproducible machine learning workflow — from analysis to production-ready pipeline.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.35 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4"
          >
            <Button
              variant="primary"
              size="lg"
              className="w-full sm:w-auto text-xs"
              onClick={() => navigate("/workspace")}
            >
              Start Building
              <ArrowRight className="h-3.5 w-3.5 ml-2" />
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="w-full sm:w-auto text-xs"
              onClick={() => navigate("/how-it-works")}
            >
              Explore ML-OS
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Interactive Lifecycle Roadmap */}
      <section className="py-16 px-6 max-w-6xl mx-auto w-full select-none">
        <div className="text-center mb-12 space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            The Automated Lifecycle Loop
          </h2>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            ML-OS coordinates raw inputs and guides the lifecycle flow through explicit logical stages.
          </p>
        </div>

        {/* Animated Nodes grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-9 gap-4 relative"
        >
          {lifecycleStages.map((stage, idx) => (
            <motion.div
              key={stage.id}
              variants={itemVariants}
              className="relative p-4 rounded border border-border bg-card/40 flex flex-col items-center space-y-3 shadow-sm hover:border-primary/20 transition-colors"
            >
              <div className="h-8 w-8 rounded bg-secondary/50 border border-border flex items-center justify-center">
                {stage.icon}
              </div>
              <div className="text-center space-y-1">
                <span className="text-[9px] font-mono text-muted-foreground block">
                  0{idx + 1}
                </span>
                <span className="text-xs font-semibold text-foreground tracking-tight block">
                  {stage.label}
                </span>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>
    </div>
  );
};
export default Home;
