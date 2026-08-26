"""Tests for Missing Run PDF copy path resolution."""

from pathlib import Path

import pytest

from scripts.pipeline_missing_run_app.core import resolve_missing_pdf_copy_dir


def test_resolve_missing_pdf_copy_dir_appends_logo():
    assert resolve_missing_pdf_copy_dir(r"G:/My Drive/UK/Missing", "Missing Logo") == Path(
        r"G:/My Drive/UK/Missing/Missing Logo"
    )


def test_resolve_missing_pdf_copy_dir_appends_apparel():
    assert resolve_missing_pdf_copy_dir(r"G:/My Drive/UK/Missing", "Missing Apparel") == Path(
        r"G:/My Drive/UK/Missing/Missing Apparel"
    )


def test_resolve_missing_pdf_copy_dir_strips_existing_subtype():
    base = r"G:/My Drive/UK/Missing/Missing Logo"
    assert resolve_missing_pdf_copy_dir(base, "Missing Apparel") == Path(
        r"G:/My Drive/UK/Missing/Missing Apparel"
    )


def test_resolve_missing_pdf_copy_dir_empty_is_none():
    assert resolve_missing_pdf_copy_dir("", "Missing Logo") is None
    assert resolve_missing_pdf_copy_dir(None, "Missing Logo") is None


def test_resolve_missing_pdf_copy_dir_rejects_bad_type():
    with pytest.raises(ValueError):
        resolve_missing_pdf_copy_dir(r"G:/My Drive/UK/Missing", "Other")
