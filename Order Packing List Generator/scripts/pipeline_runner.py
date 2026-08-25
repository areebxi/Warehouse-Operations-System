"""Backward-compatible import path for the 8-step pipeline runner."""

from scripts.pipeline_runtime import run_missing_logos_pipeline, run_pipeline

__all__ = ["run_pipeline", "run_missing_logos_pipeline"]
