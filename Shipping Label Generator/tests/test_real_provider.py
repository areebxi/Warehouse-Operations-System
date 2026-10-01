"""RealProvider tests — stable façade re-exporting split test modules."""

from __future__ import annotations

from test_real_provider_impl1 import (  # noqa: F401
    test_create_label_requires_labeldata,
    test_create_label_returns_base64_labeldata,
    test_lookup_orders_parses_all_matches,
    test_lookup_orders_parses_order_status,
    test_lookup_orders_unexpected_shape_raises_parse_error_with_details,
)
from test_real_provider_impl2 import (  # noqa: F401
    test_fetch_label_uses_labeldownload_href_when_no_labeldata,
    test_list_shipments_each_call_hits_api,
    test_list_shipments_filters_voided_and_sorts,
    test_parse_retry_after_header_http_date,
    test_provider_http_error_exposes_retry_after,
    test_second_lookup_orders_not_delayed_after_bare_429,
    test_void_label_posts_payload,
)
from test_real_provider_impl3 import (  # noqa: F401
    test_fetch_label_returns_none_on_404,
    test_no_requests_per_sec_disables_in_process_pacing,
    test_parse_retry_after_header_seconds,
    test_requests_per_sec_positive_uses_spacing_limiter,
)
