"""
Telemetry Aggregator Implementation.

Author: Antigravity
License: MIT
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from mlos.domain.models.project_memory import ProjectMemory


class TelemetryAggregator:
    """
    Observer layer aggregating telemetry stats across all ML-OS cognitive subsystems.
    """

    @staticmethod
    def compile_timeline(memory: ProjectMemory) -> List[Dict[str, Any]]:
        """
        Builds a sorted chronological list of execution events across all subsystems.
        """
        events = []

        # Planning
        for idx, p_session in enumerate(memory.planning_sessions):
            p_tel = p_session.telemetry
            start_t = (
                p_tel.run_context.start_time
                if (p_tel and p_tel.run_context)
                else datetime.now()
            )
            dur_sec = (p_tel.latency_ms / 1000.0) if p_tel else 0.0
            events.append(
                {
                    "subsystem": "planning",
                    "start": start_t.isoformat(),
                    "finish": (start_t + timedelta(seconds=dur_sec)).isoformat(),
                    "duration": dur_sec,
                    "provider": p_tel.provider if p_tel else "N/A",
                    "model": p_tel.model if p_tel else "N/A",
                    "cache": "HIT" if (p_tel and p_tel.cache_hit) else "MISS",
                    "validation": (
                        "Passed" if (p_tel and p_tel.validation_passed) else "N/A"
                    ),
                    "fallback": "Yes" if (p_tel and p_tel.fallback_used) else "No",
                    "tokens": sum(p_tel.token_usage.values()) if p_tel else 0,
                    "estimated_cost": p_tel.estimated_cost if p_tel else 0.0,
                }
            )

        # Reflection
        for idx, r_session in enumerate(memory.reflection_sessions):
            r_tel = r_session.telemetry
            start_t = (
                r_tel.run_context.start_time
                if (r_tel and r_tel.run_context)
                else datetime.now()
            )
            dur_sec = (r_tel.latency_ms / 1000.0) if r_tel else 0.0
            events.append(
                {
                    "subsystem": "reflection",
                    "start": start_t.isoformat(),
                    "finish": (start_t + timedelta(seconds=dur_sec)).isoformat(),
                    "duration": dur_sec,
                    "provider": r_tel.provider if r_tel else "N/A",
                    "model": r_tel.model if r_tel else "N/A",
                    "cache": "HIT" if (r_tel and r_tel.cache_hit) else "MISS",
                    "validation": (
                        "Passed" if (r_tel and r_tel.validation_passed) else "N/A"
                    ),
                    "fallback": "Yes" if (r_tel and r_tel.fallback_used) else "No",
                    "tokens": sum(r_tel.token_usage.values()) if r_tel else 0,
                    "estimated_cost": r_tel.estimated_cost if r_tel else 0.0,
                }
            )

        # Learning
        for idx, l_session in enumerate(memory.learning_sessions):
            l_tel = l_session.telemetry
            start_t = (
                l_tel.run_context.start_time
                if (l_tel and l_tel.run_context)
                else datetime.now()
            )
            dur_sec = (l_tel.latency_ms / 1000.0) if l_tel else 0.0
            events.append(
                {
                    "subsystem": "learning",
                    "start": start_t.isoformat(),
                    "finish": (start_t + timedelta(seconds=dur_sec)).isoformat(),
                    "duration": dur_sec,
                    "provider": l_tel.provider if l_tel else "N/A",
                    "model": l_tel.model if l_tel else "N/A",
                    "cache": "HIT" if (l_tel and l_tel.cache_hit) else "MISS",
                    "validation": (
                        "Passed" if (l_tel and l_tel.validation_passed) else "N/A"
                    ),
                    "fallback": "Yes" if (l_tel and l_tel.fallback_used) else "No",
                    "tokens": sum(l_tel.token_usage.values()) if l_tel else 0,
                    "estimated_cost": l_tel.estimated_cost if l_tel else 0.0,
                }
            )

        # Knowledge
        for idx, k_session in enumerate(memory.knowledge_sessions):
            k_tel = k_session.telemetry
            start_t = (
                k_tel.run_context.start_time
                if (k_tel and k_tel.run_context)
                else datetime.now()
            )
            dur_sec = (k_tel.latency_ms / 1000.0) if k_tel else 0.0
            events.append(
                {
                    "subsystem": "knowledge",
                    "start": start_t.isoformat(),
                    "finish": (start_t + timedelta(seconds=dur_sec)).isoformat(),
                    "duration": dur_sec,
                    "provider": k_tel.provider if k_tel else "N/A",
                    "model": k_tel.model if k_tel else "N/A",
                    "cache": "HIT" if (k_tel and k_tel.cache_hit) else "MISS",
                    "validation": (
                        "Passed" if (k_tel and k_tel.validation_passed) else "N/A"
                    ),
                    "fallback": "Yes" if (k_tel and k_tel.fallback_used) else "No",
                    "tokens": sum(k_tel.token_usage.values()) if k_tel else 0,
                    "estimated_cost": k_tel.estimated_cost if k_tel else 0.0,
                }
            )

        # Sort events chronologically by start time
        events.sort(key=lambda ev: str(ev["start"]))
        return events

    @staticmethod
    def get_summary(memory: ProjectMemory) -> Dict[str, Any]:
        """
        Aggregates timeline metrics into a per-subsystem summary dict.
        """
        timeline = TelemetryAggregator.compile_timeline(memory)
        summary: Dict[str, Any] = {
            "total_latency_sec": sum(e["duration"] for e in timeline),
            "total_tokens": sum(e["tokens"] for e in timeline),
            "total_cost": sum(e["estimated_cost"] for e in timeline),
            "subsystems": {},
        }

        subsystems_list = ["planning", "reflection", "learning", "knowledge"]
        for sub in subsystems_list:
            sub_events = [e for e in timeline if e["subsystem"] == sub]
            if not sub_events:
                summary["subsystems"][sub] = {
                    "count": 0,
                    "avg_latency_sec": 0.0,
                    "cache_hit_rate": 0.0,
                    "validation_pass_rate": 0.0,
                    "fallback_frequency": 0.0,
                }
                continue

            hits = sum(1 for e in sub_events if e["cache"] == "HIT")
            passes = sum(1 for e in sub_events if e["validation"] == "Passed")
            fallbacks = sum(1 for e in sub_events if e["fallback"] == "Yes")

            summary["subsystems"][sub] = {
                "count": len(sub_events),
                "avg_latency_sec": sum(e["duration"] for e in sub_events)
                / len(sub_events),
                "cache_hit_rate": hits / len(sub_events),
                "validation_pass_rate": passes / len(sub_events),
                "fallback_frequency": fallbacks / len(sub_events),
            }

        return summary
