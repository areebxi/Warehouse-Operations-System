import io
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from scripts.pipeline_generate_packing_list_pdf.images import (
    prepare_image_from_url_impl,
    prepare_image_impl,
)


def prepare_image_runtime_impl(
    path: Path,
    max_width_pt: float,
    max_height_pt: float,
    *,
    image_dpi: int,
    image_cache: Dict[Tuple[str, int, int], bytes],
    image_module,
) -> Union[Path, io.BytesIO]:
    return prepare_image_impl(
        path,
        max_width_pt,
        max_height_pt,
        image_dpi=image_dpi,
        image_cache=image_cache,
        image_module=image_module,
    )


def prepare_image_from_url_runtime_impl(
    url: str,
    max_width_pt: float,
    max_height_pt: float,
    *,
    image_dpi: int,
    url_image_cache: Dict[Tuple[str, int, int], Optional[bytes]],
    image_module,
    timeout_sec: int,
    max_bytes: int,
) -> Optional[io.BytesIO]:
    return prepare_image_from_url_impl(
        url,
        max_width_pt,
        max_height_pt,
        image_dpi=image_dpi,
        url_image_cache=url_image_cache,
        image_module=image_module,
        timeout_sec=timeout_sec,
        max_bytes=max_bytes,
    )
