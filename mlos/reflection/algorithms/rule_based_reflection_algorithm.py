"""
Rule-based Reflection Algorithm implementation.

Author: Antigravity
License: MIT
"""

import math
from datetime import datetime
from mlos.domain.models.reflection.reflection_context import (
    ReflectionContext,
    EvaluationSummary,
    ExecutionSummary,
    PlanningSummary,
)
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.models.reflection.reflection_reasoning_state import (
    MetricStats,
    ExecutionStats,
    PlanningStats,
    TrendStats,
    ReflectionReasoningState,
)
from mlos.domain.models.reflection.reflection_insight import ReflectionInsight
from mlos.domain.models.reflection.reflection_feedback import ReflectionFeedback
from mlos.domain.models.reflection.reflection_confidence import ReflectionConfidence
from mlos.reflection.algorithms.reflection_algorithm import ReflectionAlgorithm


class RuleBasedReflectionAlgorithm(ReflectionAlgorithm):
    """
    Concrete ReflectionAlgorithm that evaluates performance using typed statistics and heuristics.
    """

    def can_reflect(self, context: ReflectionContext) -> bool:
        """RuleBasedReflectionAlgorithm is always capable of execution."""
        return True

    def _analyze_history(self, context: ReflectionContext) -> ReflectionReasoningState:
        """
        Step 1: Extract, index, and organize raw metric histories for querying.
        """
        # 1. Compile metric histories
        eval_summaries: list[EvaluationSummary] = []
        if context.latest_evaluation is not None:
            # We insert historical ones first, then latest
            eval_summaries.extend(context.historical_evaluations)
            eval_summaries.append(context.latest_evaluation)
        else:
            eval_summaries.extend(context.historical_evaluations)

        metric_history: dict[str, tuple[float, ...]] = {}
        for ev in eval_summaries:
            for k, v in ev.metrics.items():
                if k not in metric_history:
                    metric_history[k] = ()
                metric_history[k] = metric_history[k] + (v,)

        # 2. Compute MetricStats
        metrics_stats: dict[str, MetricStats] = {}
        for key, values in metric_history.items():
            if not values:
                metrics_stats[key] = MetricStats(0.0, 0.0, 0.0, 0.0, 0.0)
                continue
            mean_val = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            latest_val = values[-1]
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_val = math.sqrt(variance)
            metrics_stats[key] = MetricStats(
                mean=mean_val,
                std=std_val,
                min_val=min_val,
                max_val=max_val,
                latest_val=latest_val,
            )

        # 3. Compute ExecutionStats
        exec_summaries: list[ExecutionSummary] = []
        if context.latest_execution is not None:
            exec_summaries.extend(context.historical_executions)
            exec_summaries.append(context.latest_execution)
        else:
            exec_summaries.extend(context.historical_executions)

        total_runs = len(exec_summaries)
        fail_count = sum(1 for e in exec_summaries if e.status == "FAILED")
        success_rate = (total_runs - fail_count) / total_runs if total_runs > 0 else 1.0
        avg_dur = (
            sum(e.duration_seconds for e in exec_summaries) / total_runs
            if total_runs > 0
            else 0.0
        )
        execution_stats = ExecutionStats(
            success_rate=success_rate,
            fail_count=fail_count,
            total_runs=total_runs,
            avg_duration=avg_dur,
        )

        # 4. Compute PlanningStats
        plan_summaries: list[PlanningSummary] = []
        if context.latest_planning is not None:
            plan_summaries.extend(context.historical_plannings)
            plan_summaries.append(context.latest_planning)
        else:
            plan_summaries.extend(context.historical_plannings)

        strat_counts: dict[str, int] = {}
        for p in plan_summaries:
            if p.selected_strategy:
                strat_counts[p.selected_strategy] = (
                    strat_counts.get(p.selected_strategy, 0) + 1
                )
        most_freq = (
            max(strat_counts, key=strat_counts.get) if strat_counts else None  # type: ignore[arg-type]
        )
        planning_stats = PlanningStats(
            strategy_counts=strat_counts, most_frequent_strategy=most_freq
        )

        # 5. Compute TrendStats
        trend_stats: dict[str, TrendStats] = {}
        for key, values in metric_history.items():
            if len(values) < 2:
                trend_stats[key] = TrendStats(
                    metric_key=key, direction="STABLE", slope=0.0, history=values
                )
                continue
            # Simple slope: change between successive runs
            diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
            avg_slope = sum(diffs) / len(diffs)

            # Determine direction based on slope and standard deviation threshold
            threshold = 0.001
            if avg_slope > threshold:
                direction = "IMPROVING"
            elif avg_slope < -threshold:
                direction = "DEGRADING"
            else:
                direction = "STABLE"

            trend_stats[key] = TrendStats(
                metric_key=key, direction=direction, slope=avg_slope, history=values
            )

        # 6. Baseline Metrics (metrics from the first available evaluation)
        baseline_metrics: dict[str, float] = {}
        if context.historical_evaluations:
            baseline_metrics = dict(context.historical_evaluations[0].metrics)
        elif context.latest_evaluation is not None:
            baseline_metrics = dict(context.latest_evaluation.metrics)

        return ReflectionReasoningState(
            metric_history=metric_history,
            metrics_stats=metrics_stats,
            execution_stats=execution_stats,
            planning_stats=planning_stats,
            trend_stats=trend_stats,
            run_comparisons=(),
            baseline_metrics=baseline_metrics,
        )

    def _compare_runs(
        self, context: ReflectionContext, state: ReflectionReasoningState
    ) -> ReflectionReasoningState:
        """
        Step 2: Contrast the latest evaluation with past runs.
        """
        comparisons: list[dict] = []
        eval_list = list(context.historical_evaluations)
        if context.latest_evaluation is not None:
            eval_list.append(context.latest_evaluation)

        for i in range(1, len(eval_list)):
            prev = eval_list[i - 1]
            curr = eval_list[i]
            delta: dict[str, float] = {}
            for k, val in curr.metrics.items():
                if k in prev.metrics:
                    delta[k] = val - prev.metrics[k]
            comparisons.append(delta)

        # Return a new state containing comparisons
        return ReflectionReasoningState(
            metric_history=state.metric_history,
            metrics_stats=state.metrics_stats,
            execution_stats=state.execution_stats,
            planning_stats=state.planning_stats,
            trend_stats=state.trend_stats,
            run_comparisons=tuple(comparisons),
            baseline_metrics=state.baseline_metrics,
        )

    def _detect_patterns(
        self, context: ReflectionContext, state: ReflectionReasoningState
    ) -> tuple[ReflectionInsight, ...]:
        """
        Step 3: Analyze performance transitions to generate unified ReflectionInsights.
        """
        insights: list[ReflectionInsight] = []
        idx = 1

        # 1. Regressions and Successes based on comparisons
        if state.run_comparisons:
            latest_delta = state.run_comparisons[-1]
            for metric, diff in latest_delta.items():
                stats = state.metrics_stats.get(metric)
                if stats is None or stats.mean == 0.0:
                    continue

                pct_change = (diff / stats.mean) * 100.0

                # Check for regression (significant drop in metrics like accuracy/score)
                # Note: Lower values are worse for accuracy/F1/R2, but better for loss/MSE.
                # We assume standard metrics where higher is better for simplicity, or specify based on key.
                is_loss = any(
                    x in metric.lower() for x in ["loss", "error", "mse", "mae"]
                )
                is_regression = (pct_change < -2.0 and not is_loss) or (
                    pct_change > 2.0 and is_loss
                )
                is_improvement = (pct_change > 2.0 and not is_loss) or (
                    pct_change < -2.0 and is_loss
                )

                if is_regression:
                    severity = "CRITICAL" if abs(pct_change) > 10.0 else "WARNING"
                    insights.append(
                        ReflectionInsight(
                            insight_id=f"INS-REG-{idx:03d}",
                            insight_type="REGRESSION",
                            severity=severity,
                            summary=f"Significant regression detected in metric '{metric}': dropped by {abs(pct_change):.2f}% in the latest run.",
                            evidence=(f"Latest delta: {diff:.4f}",),
                            confidence=0.85,
                        )
                    )
                    idx += 1
                elif is_improvement:
                    insights.append(
                        ReflectionInsight(
                            insight_id=f"INS-SUC-{idx:03d}",
                            insight_type="SUCCESS",
                            severity="LOW",
                            summary=f"Improvement detected in metric '{metric}': increased by {abs(pct_change):.2f}% in the latest run.",
                            evidence=(f"Latest delta: {diff:.4f}",),
                            confidence=0.90,
                        )
                    )
                    idx += 1

        # 2. Execution Failures
        if (
            context.latest_execution is not None
            and context.latest_execution.status == "FAILED"
        ):
            insights.append(
                ReflectionInsight(
                    insight_id=f"INS-FAIL-{idx:03d}",
                    insight_type="FAILURE",
                    severity="CRITICAL",
                    summary=f"Execution pipeline failed with exit code {context.latest_execution.exit_code}.",
                    evidence=(
                        f"Status: {context.latest_execution.status}",
                        f"Error: {context.latest_execution.error_message or 'Unknown runtime error'}",
                    ),
                    confidence=1.0,
                )
            )
            idx += 1

        # 3. Metric trends
        for metric, trend in state.trend_stats.items():
            if trend.direction == "DEGRADING":
                insights.append(
                    ReflectionInsight(
                        insight_id=f"INS-TRD-{idx:03d}",
                        insight_type="METRIC_TREND",
                        severity="WARNING",
                        summary=f"Metric '{metric}' demonstrates a degrading trend over the last {len(trend.history)} runs.",
                        evidence=(
                            f"Slope: {trend.slope:.4f}",
                            f"History: {trend.history}",
                        ),
                        confidence=0.80,
                    )
                )
                idx += 1

        # 4. Fallback if no history/empty
        if not insights and not state.metric_history:
            insights.append(
                ReflectionInsight(
                    insight_id=f"INS-INIT-001",
                    insight_type="METRIC_TREND",
                    severity="LOW",
                    summary="No execution history found. Workspace is initialized.",
                    evidence=(),
                    confidence=1.0,
                )
            )

        return tuple(insights)

    def _generate_recommendations(
        self,
        context: ReflectionContext,
        state: ReflectionReasoningState,
        insights: tuple[ReflectionInsight, ...],
    ) -> tuple[ReflectionFeedback, ...]:
        """
        Step 4: Translate insights into structured, machine-readable ReflectionFeedback.
        """
        feedback_list: list[ReflectionFeedback] = []
        idx = 1

        for ins in insights:
            if ins.insight_type == "REGRESSION":
                # Recommend parameters adjustment
                feedback_list.append(
                    ReflectionFeedback(
                        feedback_id=f"FB-REG-{idx:03d}",
                        target_subsystem="decision",
                        target_component="ModelGenerator",
                        action_type="ADJUST_PARAM",
                        parameters={
                            "learning_rate": "decrease",
                            "regularization": "increase",
                        },
                        priority="HIGH",
                        reason=ins.summary,
                        expected_outcome="Reduce overfitting and stabilize score variance.",
                    )
                )
                idx += 1
            elif ins.insight_type == "FAILURE":
                # Recommend strategy change
                feedback_list.append(
                    ReflectionFeedback(
                        feedback_id=f"FB-FAIL-{idx:03d}",
                        target_subsystem="planning",
                        target_component="RuleBasedPlanningAlgorithm",
                        action_type="CHANGE_STRATEGY",
                        parameters={"fallback_strategy": "RuleBasedPipeline"},
                        priority="CRITICAL",
                        reason=ins.summary,
                        expected_outcome="Verify pipeline structure validity and restore execution flow.",
                    )
                )
                idx += 1
            elif ins.insight_type == "METRIC_TREND" and ins.severity == "WARNING":
                # Recommend enabling preprocessing steps
                feedback_list.append(
                    ReflectionFeedback(
                        feedback_id=f"FB-TRD-{idx:03d}",
                        target_subsystem="decision",
                        target_component="ScalingGenerator",
                        action_type="ENABLE_IMPUTATION",
                        parameters={"scaling_method": "standard"},
                        priority="MEDIUM",
                        reason=ins.summary,
                        expected_outcome="Improve convergence speed and metric performance stability.",
                    )
                )
                idx += 1

        # Fallback if no recommendations generated
        if not feedback_list:
            feedback_list.append(
                ReflectionFeedback(
                    feedback_id="FB-INIT-001",
                    target_subsystem="planning",
                    target_component="HeuristicPlanningAlgorithm",
                    action_type="ENABLE_IMPUTATION",
                    parameters={"pipeline_type": "baseline"},
                    priority="CRITICAL",
                    reason="No execution metrics available in history.",
                    expected_outcome="Run baseline execution pipeline to establish initial metrics.",
                )
            )

        return tuple(feedback_list)

    def _construct_session(
        self,
        insights: tuple[ReflectionInsight, ...],
        feedback: tuple[ReflectionFeedback, ...],
        state: ReflectionReasoningState,
    ) -> ReflectionSession:
        """
        Step 5: Assemble insights and feedback into a final ReflectionSession, computing confidence.
        """
        # Calculate uncertainty based on historical data volume
        history_length = len(state.metric_history.get("accuracy", ()))
        if history_length == 0:
            uncertainty = 0.8
            score = 0.5
        else:
            # More history reduces uncertainty
            uncertainty = max(0.1, 1.0 / (history_length + 1))
            # Score is based on success rates and trend stability
            score = min(0.95, 0.5 + (0.5 * state.execution_stats.success_rate))

        # Check acceptance threshold: score >= 0.7 and uncertainty <= 0.3
        # In a real environment, or for tests, we can derive this:
        accepted = (score >= 0.7) and (uncertainty <= 0.3)

        evidence_ids = tuple(ins.insight_id for ins in insights)
        explanation = (
            f"Reflection completed based on {len(insights)} insights and {history_length} historical runs. "
            f"Success rate stands at {state.execution_stats.success_rate * 100:.1f}%."
        )

        confidence = ReflectionConfidence(
            score=score,
            uncertainty=uncertainty,
            evidence=evidence_ids,
            explanation=explanation,
            accepted=accepted,
        )

        # Assemble summary string
        summary = (
            f"Reflection detected {len(insights)} insights (including "
            f"{sum(1 for i in insights if i.insight_type == 'REGRESSION')} regressions and "
            f"{sum(1 for i in insights if i.insight_type == 'FAILURE')} failures) "
            f"generating {len(feedback)} corrective actions. Confidence level: "
            f"{'ACCEPTED' if accepted else 'REJECTED'} (score={score:.2f}, uncertainty={uncertainty:.2f})."
        )

        return ReflectionSession(
            summary=summary,
            insights=list(insights),
            feedback=list(feedback),
            confidence=confidence,
        )
