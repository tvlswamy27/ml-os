import time
from datetime import datetime
from typing import Any
from uuid import uuid4

from mlos.intelligence.cache.llm_cache import LLMCache
from mlos.intelligence.config import ProviderConfig
from mlos.intelligence.provider_factory import ProviderFactory
from mlos.intelligence.schemas.llm_request import LLMRequest
from mlos.intelligence.schemas.llm_response import LLMResponse
from mlos.intelligence.telemetry.call_metrics import CallMetrics
from mlos.intelligence.telemetry.token_usage import TokenUsage
from mlos.intelligence.validation.schema_validator import SchemaValidator


class IntelligenceService:
    """
    Coordinates context building, caching, token usage, validations, and provider invocation.
    """

    def __init__(self, default_config: ProviderConfig, cache: LLMCache | None = None):
        self.default_config = default_config
        self.cache = cache or LLMCache()

    def execute(self, request: LLMRequest) -> LLMResponse:
        """
        Executes a strongly typed LLMRequest and returns an LLMResponse.
        Coordinates lookup in LLMCache, retries, and schema/range validations.
        """
        provider_name = request.provider or self.default_config.provider
        model_name = request.model or self.default_config.model
        temperature = (
            request.temperature
            if request.temperature is not None
            else self.default_config.temperature
        )
        max_tokens = (
            request.max_tokens
            if request.max_tokens is not None
            else self.default_config.max_tokens
        )
        seed = request.seed if request.seed is not None else self.default_config.seed

        config = ProviderConfig(
            provider=provider_name,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            timeout=self.default_config.timeout,
            retry_limit=self.default_config.retry_limit,
            endpoint=self.default_config.endpoint,
            api_key=self.default_config.api_key,
        )

        provider_config_dict = {
            "provider": config.provider,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "seed": config.seed,
        }

        # Check Cache
        cached_output, cache_hit = self.cache.lookup(
            request.system_prompt,
            request.developer_prompt,
            request.user_prompt,
            request.response_schema,
            provider_config_dict,
        )

        if cache_hit:
            from pydantic import BaseModel

            if (
                request.response_schema is not None
                and isinstance(request.response_schema, type)
                and issubclass(request.response_schema, BaseModel)
            ):
                if isinstance(cached_output, dict):
                    try:
                        cached_output = request.response_schema.model_validate(
                            cached_output
                        )
                    except Exception:
                        pass

            dummy_metrics = CallMetrics(
                request_id=f"cached-{uuid4()}",
                provider=config.provider,
                model=config.model,
                latency_ms=0.0,
                token_usage=TokenUsage(0, 0, 0),
                cost=0.0,
                cache_hit=True,
                timestamp=datetime.utcnow(),
            )
            return LLMResponse(
                parsed_output=cached_output,
                raw_response=str(cached_output),
                call_metrics=dummy_metrics,
                cache_hit=True,
                provider=config.provider,
                model=config.model,
                latency=0.0,
                cost=0.0,
                retry_count=0,
                validation_passed=True,
            )

        # Cache miss, instantiate provider
        provider = ProviderFactory.create_provider(config)

        retry_count = 0
        last_error = None
        parsed_output = None
        raw_response = ""
        metrics = CallMetrics(
            request_id=f"failed-{uuid4()}",
            provider=config.provider,
            model=config.model,
            latency_ms=0.0,
            token_usage=TokenUsage(0, 0, 0),
            cost=0.0,
            cache_hit=False,
            timestamp=datetime.utcnow(),
            error_message="Initialization placeholder",
        )
        validation_passed = False

        while retry_count <= config.retry_limit:
            try:
                if request.response_schema is not None:
                    parsed_output, metrics = provider.structured_generate(
                        system_prompt=request.system_prompt,
                        user_prompt=request.user_prompt,
                        response_schema=request.response_schema,
                        developer_prompt=request.developer_prompt,
                    )
                    raw_response = str(parsed_output)
                    validation_passed = parsed_output is not None
                else:
                    raw_response, metrics = provider.generate(
                        system_prompt=request.system_prompt,
                        user_prompt=request.user_prompt,
                        developer_prompt=request.developer_prompt,
                    )
                    parsed_output, validation_passed = (
                        SchemaValidator.validate_and_parse(
                            raw_response, request.response_schema
                        )
                    )

                if validation_passed:
                    # Store in cache
                    self.cache.store(
                        request.system_prompt,
                        request.developer_prompt,
                        request.user_prompt,
                        request.response_schema,
                        provider_config_dict,
                        parsed_output,
                    )
                    break
            except Exception as e:
                last_error = e
                retry_count += 1
                time.sleep(0.1 * retry_count)

        if not validation_passed:
            metrics = CallMetrics(
                request_id=f"failed-{uuid4()}",
                provider=config.provider,
                model=config.model,
                latency_ms=10.0,
                token_usage=TokenUsage(0, 0, 0),
                cost=0.0,
                cache_hit=False,
                timestamp=datetime.utcnow(),
                error_message=str(last_error) if last_error else "Validation failed",
            )

        return LLMResponse(
            parsed_output=parsed_output,
            raw_response=raw_response,
            call_metrics=metrics,
            cache_hit=False,
            provider=config.provider,
            model=config.model,
            latency=metrics.latency_ms if metrics else 0.0,
            cost=metrics.cost if metrics else 0.0,
            retry_count=retry_count,
            validation_passed=validation_passed,
        )

    def execute_subsystem(
        self, subsystem: str, context: Any, response_schema: Any
    ) -> LLMResponse:
        """
        Loads the template prompt for a subsystem, builds prompt variables from the context,
        and executes the LLMRequest.
        """
        from mlos.intelligence.prompts.prompt_manager import PromptManager
        from mlos.intelligence.schemas.llm_request import LLMRequest

        prompt_manager = PromptManager()
        prompt = prompt_manager.get_prompt(subsystem, f"default_{subsystem}")

        if subsystem == "planning":
            variables = self._build_planning_variables(context)
        elif subsystem == "reflection":
            variables = self._build_reflection_variables(context)
        elif subsystem == "learning":
            variables = self._build_learning_variables(context)
        elif subsystem == "knowledge":
            variables = self._build_knowledge_variables(context)
        else:
            variables = {}

        user_prompt = prompt_manager.format_user_prompt(prompt, **variables)

        request = LLMRequest(
            system_prompt=prompt.system_prompt,
            developer_prompt=prompt.developer_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        return self.execute(request)

    def _build_planning_variables(self, context: Any) -> dict[str, str]:
        """
        Constructs formatting variables for the default planning prompt template.
        """
        project_summary = f"Project Name: {context.project_name}"

        # Dataset profile
        dataset_obs = [
            obs for obs in context.observations if obs.source_subsystem == "dataset"
        ]
        profile_lines = []
        for obs in dataset_obs:
            profile_lines.append(f"- {obs.metric_key}: {obs.metric_value}")
        dataset_profile = (
            "\n".join(profile_lines)
            if profile_lines
            else "No dataset profile available."
        )

        # Knowledge summary and active rules
        rules_lines = []
        for rule in context.knowledge_summary.rules:
            rules_lines.append(
                f"- Subsystem: {rule.subsystem}, Component: {rule.component}, "
                f"Parameters: {rule.parameters}, Confidence: {rule.confidence_score}"
            )
        knowledge_summary = (
            "\n".join(rules_lines)
            if rules_lines
            else "No active knowledge rules available."
        )
        active_rules = knowledge_summary

        # Reasoning facts
        facts_lines = []
        for obs in context.observations:
            facts_lines.append(f"- {obs.metric_key}: {obs.metric_value}")
        reasoning_facts = (
            "\n".join(facts_lines) if facts_lines else "No reasoning facts available."
        )

        # Historical observations
        obs_lines = []
        for obs in context.observations:
            obs_lines.append(
                f"- [{obs.source_subsystem}] {obs.metric_key} = {obs.metric_value} "
                f"(observed at {obs.observed_at})"
            )
        historical_observations = (
            "\n".join(obs_lines)
            if obs_lines
            else "No historical observations available."
        )

        # Planning goals
        goals_lines = []
        for goal in context.goals:
            goals_lines.append(
                f"- Goal: {goal.name}, Metric: {goal.metric}, Target: {goal.target_value}"
            )
        planning_goals = (
            "\n".join(goals_lines) if goals_lines else "No planning goals specified."
        )

        return {
            "project_name": context.project_name,
            "goals": (
                ", ".join([g.name for g in context.goals]) if context.goals else "None"
            ),
            "project_summary": project_summary,
            "dataset_profile": dataset_profile,
            "knowledge_summary": knowledge_summary,
            "reasoning_facts": reasoning_facts,
            "historical_observations": historical_observations,
            "active_rules": active_rules,
            "planning_goals": planning_goals,
        }

    def _build_reflection_variables(self, context: Any) -> dict[str, str]:
        """
        Constructs formatting variables for the default reflection prompt template.
        """
        project_summary = (
            f"Project Name: {context.project_name}, Goal: {context.project_goal}"
        )

        # 1. Compile metric histories
        eval_summaries = list(context.historical_evaluations)
        if context.latest_evaluation is not None:
            eval_summaries.append(context.latest_evaluation)

        metric_history: dict[str, tuple[float, ...]] = {}
        for ev in eval_summaries:
            for k, v in ev.metrics.items():
                if k not in metric_history:
                    metric_history[k] = ()
                metric_history[k] = metric_history[k] + (v,)

        # 2. Compute metric statistics
        import math

        lines = []
        for key, values in metric_history.items():
            if not values:
                continue
            mean_val = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            latest_val = values[-1]
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_val = math.sqrt(variance)
            lines.append(
                f"- {key}: mean={mean_val:.4f}, std={std_val:.4f}, min={min_val:.4f}, max={max_val:.4f}, latest={latest_val:.4f}"
            )
        metric_statistics = (
            "\n".join(lines) if lines else "No metric statistics available."
        )

        # 3. Compute execution statistics
        exec_summaries = list(context.historical_executions)
        if context.latest_execution is not None:
            exec_summaries.append(context.latest_execution)
        total_runs = len(exec_summaries)
        fail_count = sum(1 for e in exec_summaries if e.status == "FAILED")
        success_rate = (total_runs - fail_count) / total_runs if total_runs > 0 else 1.0
        avg_dur = (
            sum(e.duration_seconds for e in exec_summaries) / total_runs
            if total_runs > 0
            else 0.0
        )
        execution_statistics = f"Success Rate: {success_rate * 100:.1f}%, Fails: {fail_count}, Total Runs: {total_runs}, Avg Duration: {avg_dur:.2f}s"

        # 4. Compute planning statistics
        planning_summaries = list(context.historical_plannings)
        if context.latest_planning is not None:
            planning_summaries.append(context.latest_planning)
        strategy_counts: dict[str, int] = {}
        for p in planning_summaries:
            if p.selected_strategy:
                strategy_counts[p.selected_strategy] = (
                    strategy_counts.get(p.selected_strategy, 0) + 1
                )
        most_frequent = (
            max(strategy_counts, key=lambda k: strategy_counts[k])
            if strategy_counts
            else None
        )
        planning_statistics = f"Most Frequent Strategy: {most_frequent}, Strategy Counts: {strategy_counts}"

        # 5. Compute trend statistics
        trend_lines = []
        for key, values in metric_history.items():
            if len(values) < 2:
                direction = "STABLE"
                slope = 0.0
            else:
                n = len(values)
                x = list(range(n))
                mean_x = sum(x) / n
                mean_y = sum(values) / n
                num = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
                den = sum((x[i] - mean_x) ** 2 for i in range(n))
                slope = num / den if den > 0 else 0.0

                if slope > 0.005:
                    direction = "IMPROVING"
                elif slope < -0.005:
                    direction = "DEGRADING"
                else:
                    direction = "STABLE"
            trend_lines.append(
                f"- {key}: direction={direction}, slope={slope:.4f}, history={values}"
            )
        trend_statistics = (
            "\n".join(trend_lines) if trend_lines else "No trend statistics available."
        )

        # 6. Compute reflection history summary
        reflection_history = (
            f"Historical Runs Count: {len(context.historical_evaluations)}"
        )

        # 7. Compute knowledge summary
        rules_lines = []
        for rule in getattr(context.knowledge_summary, "rules", []):
            rules_lines.append(
                f"- Subsystem: {rule.subsystem}, Component: {rule.component}, "
                f"Parameters: {rule.parameters}, Confidence: {rule.confidence_score}"
            )
        knowledge_summary = (
            "\n".join(rules_lines)
            if rules_lines
            else "No active knowledge rules available."
        )

        return {
            "project_name": context.project_name,
            "project_summary": project_summary,
            "metric_statistics": metric_statistics,
            "execution_statistics": execution_statistics,
            "planning_statistics": planning_statistics,
            "trend_statistics": trend_statistics,
            "reflection_history": reflection_history,
            "knowledge_summary": knowledge_summary,
        }

    def _build_learning_variables(self, context: Any) -> dict[str, str]:
        """
        Constructs formatting variables for the default learning prompt template.
        """
        project_summary = (
            f"Project Name: {context.project_name}, Goal: {context.project_goal}"
        )

        ref = context.latest_reflection
        if ref:
            reflection_summary = (
                f"Latest Session ID: {ref.session_id}, Summary: {ref.summary}, "
                f"Accepted: {ref.confidence_accepted}, Feedback Actions Count: {len(ref.feedback)}"
            )
        else:
            reflection_summary = "No reflection summary available."

        all_reflections = list(context.historical_reflections)
        if context.latest_reflection is not None:
            all_reflections.append(context.latest_reflection)

        total_feedback_count = 0
        priority_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        subsystem_counts: dict[str, int] = {}
        for r in all_reflections:
            for fb in r.feedback:
                total_feedback_count += 1
                prio = fb.priority.upper() if fb.priority else "MEDIUM"
                priority_counts[prio] = priority_counts.get(prio, 0) + 1
                subsystem_counts[fb.target_subsystem] = (
                    subsystem_counts.get(fb.target_subsystem, 0) + 1
                )

        feedback_statistics = (
            f"Total Feedback Count: {total_feedback_count}, "
            f"Priorities: {priority_counts}, Subsystems: {subsystem_counts}"
        )

        action_frequencies: dict[str, int] = {}
        for r in all_reflections:
            for fb in r.feedback:
                key = f"{fb.action_type}:{fb.target_component}"
                action_frequencies[key] = action_frequencies.get(key, 0) + 1
        action_statistics = f"Action Frequencies: {action_frequencies}"

        acceptance_history = []
        for r in all_reflections:
            acceptance_history.append(1.0 if r.confidence_accepted else 0.0)
        stable_rate = (
            sum(acceptance_history) / len(acceptance_history)
            if acceptance_history
            else 0.0
        )
        trend_statistics = (
            f"Stable Rate: {stable_rate:.4f}, Acceptance History: {acceptance_history}"
        )

        learning_history = f"Number of historical reflections analyzed: {len(context.historical_reflections)}"

        rules_lines = []
        for rule in getattr(context.knowledge_summary, "rules", []):
            rules_lines.append(
                f"- Subsystem: {rule.subsystem}, Component: {rule.component}, "
                f"Parameters: {rule.parameters}, Confidence: {rule.confidence_score}"
            )
        knowledge_summary = (
            "\n".join(rules_lines)
            if rules_lines
            else "No active knowledge rules available."
        )

        return {
            "project_name": context.project_name,
            "project_summary": project_summary,
            "reflection_summary": reflection_summary,
            "feedback_statistics": feedback_statistics,
            "action_statistics": action_statistics,
            "trend_statistics": trend_statistics,
            "learning_history": learning_history,
            "knowledge_summary": knowledge_summary,
        }

    def _build_knowledge_variables(self, context: Any) -> dict[str, str]:
        """
        Constructs formatting variables for the default knowledge prompt template.
        """
        project_summary = (
            f"Project Name: {context.project_name}, Goal: {context.project_goal}"
        )

        ls = context.latest_learning
        if ls:
            learning_summary = (
                f"Latest Session ID: {ls.session_id}, Updates Count: {len(ls.updates)}, "
                f"Accepted: {ls.confidence_accepted}"
            )
        else:
            learning_summary = "No learning summary available."

        all_learnings = list(context.historical_learnings)
        if context.latest_learning is not None:
            all_learnings.append(context.latest_learning)

        total_updates = 0
        update_types: dict[str, int] = {}
        for l in all_learnings:
            for u in l.updates:
                total_updates += 1
                u_type = str(u.update_type)
                update_types[u_type] = update_types.get(u_type, 0) + 1
        proposal_statistics = (
            f"Total Learning Updates: {total_updates}, Types: {update_types}"
        )

        active_entries = []
        if context.existing_knowledge is not None:
            active_entries = list(context.existing_knowledge.active_entries)

        active_policy_statistics = f"Total Active Policies: {len(active_entries)}"
        promotion_history = f"Number of historical learnings analyzed: {len(context.historical_learnings)}"

        total_usages = sum(getattr(e, "usage_count", 0) for e in active_entries)
        knowledge_usage_statistics = f"Total Policy Usages: {total_usages}"

        overlaps = 0
        incoming_keys = set()
        if context.latest_learning:
            for u in context.latest_learning.updates:
                incoming_keys.add((u.target_subsystem, u.target_component))
        for e in active_entries:
            if (e.target_subsystem, e.target_component) in incoming_keys:
                overlaps += 1
        conflict_statistics = f"Overlapping Subsystem/Component policies: {overlaps}"

        version_counts: dict[int, int] = {}
        for e in active_entries:
            v = e.version.version_number
            version_counts[v] = version_counts.get(v, 0) + 1
        version_statistics = f"Version Distribution: {version_counts}"

        # Get policy summaries
        policy_lines = []
        for e in active_entries:
            policy_lines.append(
                f"- Component: {e.target_component}, Subsystem: {e.target_subsystem}, Version: {e.version.version_number}"
            )
        active_knowledge = (
            "\n".join(policy_lines) if policy_lines else "No active policies."
        )

        return {
            "project_name": context.project_name,
            "project_summary": project_summary,
            "learning_summary": learning_summary,
            "proposal_statistics": proposal_statistics,
            "active_knowledge": active_knowledge,
            "deprecated_knowledge": "Deprecated statistics monitored offline.",
            "version_statistics": version_statistics,
            "conflict_statistics": conflict_statistics,
            "promotion_candidates": f"Candidates Count: {len(context.latest_learning.updates) if context.latest_learning else 0}",
            "active_policy_statistics": active_policy_statistics,
            "promotion_history": promotion_history,
            "knowledge_usage_statistics": knowledge_usage_statistics,
        }
