from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .constants import PIPELINE_STAGES

if TYPE_CHECKING:
    from .core import LunaProfiler

logger = logging.getLogger(__name__)


def log_summary(profiler: LunaProfiler) -> None:
    summary = profiler.get_stage_summary()
    bottlenecks = profiler.get_bottlenecks()

    logger.info("=" * 70)
    logger.info("[PROFILER] RESUMO DE PERFORMANCE LUNA")
    logger.info("=" * 70)

    for stage, stats in sorted(summary.items(), key=lambda x: x[1]["avg_ms"], reverse=True):
        status_icon = "OK" if stats["status"] == "OK" else ("!!" if stats["status"] == "CRITICAL" else "?")
        logger.info(
            f"  [{status_icon}] {stage:20} | "
            f"avg:{stats['avg_ms']:7.1f}ms | "
            f"p50:{stats['p50_ms']:7.1f}ms | "
            f"p95:{stats['p95_ms']:7.1f}ms | "
            f"n={stats['count']}"
        )

    if bottlenecks:
        logger.info("-" * 70)
        logger.info("[PROFILER] GARGALOS DETECTADOS:")
        for b in bottlenecks:
            logger.info(f"  [{b['severity']}] {b['stage']}: {b['avg_ms']:.1f}ms (threshold: {b['threshold_ms']}ms)")
            logger.info(f"           Recomendacao: {b['recommendation']}")

    logger.info("=" * 70)


def log_diagnostics(profiler: LunaProfiler) -> str:
    lines = []
    summary = profiler.get_stage_summary()
    bottlenecks = profiler.get_bottlenecks()

    lines.append("=" * 60)
    lines.append("DIAGNOSTICO LUNA - ONDE ESTAMOS LENTOS?")
    lines.append("=" * 60)

    if not summary:
        lines.append("Nenhuma metrica coletada ainda. Execute algumas interacoes.")
        return "\n".join(lines)

    lines.append("\nLATENCIA POR ESTAGIO:")
    for stage in PIPELINE_STAGES:
        if stage in summary:
            s = summary[stage]
            bar_len = min(int(s["avg_ms"] / 100), 30)
            bar = "=" * bar_len
            lines.append(f"  {stage:20} | {s['avg_ms']:7.1f}ms |{bar}| [{s['status']}]")

    if bottlenecks:
        lines.append("\nGARGALOS CRITICOS:")
        for b in bottlenecks:
            lines.append(f"  [{b['severity']}] {b['stage']}")
            lines.append(f"      Latencia: {b['avg_ms']:.1f}ms (limite: {b['threshold_ms']}ms)")
            lines.append(f"      Acao: {b['recommendation']}")

    recent = profiler.get_recent_traces(5)
    if recent:
        lines.append("\nULTIMAS INTERACOES:")
        for t in recent:
            dur = t.get("duration_ms", 0)
            lines.append(f"  #{t['id']}: {dur:.0f}ms - '{t.get('user_input', '')[:30]}...'")

    lines.append("=" * 60)
    return "\n".join(lines)
