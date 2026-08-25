from __future__ import annotations

from typing import Any


def default_config_dict() -> dict[str, Any]:
    return {
        "concurrency": {
            "max_workers": 20,
            "request_timeout_sec": 15,
            "label_timeout_sec": 35,
            "max_retries": 2,
            "retry_min_wait_sec": 1,
            "retry_max_wait_sec": 8,
        },
        "rate_limit": {
            "fallback_wait_sec": 60,
            # When true, multiple running copies coordinate pacing + cooldown via a shared state file.
            # This is recommended if you sometimes run two instances at once.
            "shared_across_processes": False,
            # Path relative to logs_dir unless absolute.
            "state_file": "rate_limit_state.json",
            # Optional: set requests_per_sec for fixed-spacing pacing; omit or 0 for none (429-driven throttle).
        },
        "paths": {
            "output_dir": "output",
            "logs_dir": "logs",
            "reports_dir": "Reports",
            "desfiles_dir": "desfiles",
            "orders_csv": "Order Numbers.csv",
            "void_csv": "void_labels.csv",
        },
        "manual_print": {
            "input_csv": "Manual Print Input/Order Numbers.csv",
        },
        "logging": {
            "format": "json",
            "level": "INFO",
            "redact_keys": ["labelData", "Authorization", "apiKey", "apiSecret"],
        },
        "batch": {
            "notes": "CreateAndProcessBatchByOrderIds",
            "processed_by": "Automated",
            "ship_from": "Dudley",
        },
        "security": {"restrict_output_permissions": True},
        "weight": {"ounce_carriers": ["royal_mail", "stamps_com"]},
        "service_map": {},
        "provider": {
            "test_label": False,
            "label_format": "PDF",
            "label_layout": "4x6",
            "label_download_type": "url",
        },
    }
