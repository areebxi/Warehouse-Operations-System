"""Backward-compatible wrapper for the Packing List GUI app."""

from scripts.pipeline_packing_list_app.app import PackingListApp, main

__all__ = ["PackingListApp", "main"]


if __name__ == "__main__":
    main()
