# ML-OS Cognitive Architecture Guide

Describes the core pipeline and subsystems lifecycle orchestration.

## Orchestration Loop
The orchestrator drives iterations in the sequence:
1. Analysis
2. Planning
3. Decision
4. Generation
5. Assembly
6. Execution
7. Evaluation
8. Reflection
9. Learning
10. Knowledge Management

## Decoupled Boundaries
Cognitive engines read state through window-constrained contexts and propose changes without executing mutations directly. Fallback structures protect core engines from external failure.
