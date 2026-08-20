import * as React from "react";
import { Check } from "lucide-react";
import { Card, CardHeader, CardContent, CardFooter } from "../components/Card";
import { Button } from "../components/Button";

export const Pricing: React.FC = () => {
  const tiers = [
    {
      name: "Local Community",
      price: "$0",
      period: "forever",
      desc: "Perfect for local ML project prototyping.",
      features: [
        "Local-first execution runtime",
        "Explainable decisions list",
        "Automated python pipeline generation",
        "Command line wizard interface",
      ],
      action: "Start Building",
      variant: "secondary" as const,
    },
    {
      name: "Enterprise Studio",
      price: "$49",
      period: "per user/month",
      desc: "For small teams and production deployment.",
      features: [
        "Everything in Community tier",
        "SQLite workspace persistence",
        "SSE streaming execution timeline",
        "Collaborative multi-user controls",
        "Staging model registries",
      ],
      action: "Upgrade to Studio",
      variant: "primary" as const,
    },
  ];

  return (
    <div className="py-16 px-6 max-w-5xl mx-auto space-y-12 select-none">
      <div className="text-center space-y-3">
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-sans">
          Simple, Transparent Pricing
        </h1>
        <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
          Select the option matching your machine learning engineering workload demands.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto pt-6">
        {tiers.map((tier, idx) => (
          <Card key={idx} className="bg-card/45 border-border hover:border-border/60 hover:bg-card/75 transition-all flex flex-col justify-between">
            <CardHeader className="text-left pb-4 border-b border-border/10">
              <span className="text-[10px] font-mono text-primary font-bold uppercase tracking-wider">
                {tier.name}
              </span>
              <div className="flex items-baseline space-x-2 mt-2">
                <span className="text-3xl font-bold font-mono tracking-tight text-foreground">{tier.price}</span>
                <span className="text-xs text-muted-foreground font-mono">/{tier.period}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">{tier.desc}</p>
            </CardHeader>
            <CardContent className="flex-1 py-6">
              <ul className="space-y-3 text-xs text-muted-foreground text-left">
                {tier.features.map((feat, fidx) => (
                  <li key={fidx} className="flex items-center space-x-3">
                    <Check className="h-4 w-4 text-success flex-shrink-0" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter className="pt-4 border-t border-border/10">
              <Button variant={tier.variant} className="w-full text-xs h-9">
                {tier.action}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
};
export default Pricing;
