"""Warehouse path registry — stable public API.

Import as ``from shared.paths import cl_csv_path`` or ``from shared import paths as wh``.
"""

from __future__ import annotations

from shared.paths.catalog import *  # noqa: F403
from shared.paths.packing import *  # noqa: F403
from shared.paths.po import *  # noqa: F403
from shared.paths.queue import *  # noqa: F403
from shared.paths.root import *  # noqa: F403
from shared.paths.shared_io import *  # noqa: F403
from shared.paths.shipping import *  # noqa: F403
from shared.paths.sorter import *  # noqa: F403
from shared.paths.catalog import __all__ as _catalog_all
from shared.paths.packing import __all__ as _packing_all
from shared.paths.po import __all__ as _po_all
from shared.paths.queue import __all__ as _queue_all
from shared.paths.root import __all__ as _root_all
from shared.paths.shared_io import __all__ as _shared_io_all
from shared.paths.shipping import __all__ as _shipping_all
from shared.paths.sorter import __all__ as _sorter_all

__all__ = [
    *_root_all,
    *_catalog_all,
    *_packing_all,
    *_sorter_all,
    *_queue_all,
    *_po_all,
    *_shipping_all,
    *_shared_io_all,
]
