from __future__ import annotations

import sys

_STD_INPUT_HANDLE = -10
_ENABLE_EXTENDED_FLAGS = 0x0080
_ENABLE_QUICK_EDIT_MODE = 0x0040


def configure_windows_console() -> bool:
    """
    Disable Windows console Quick Edit Mode so clicking the CMD window does not
    pause stdout/stderr and freeze long-running print jobs.
    """
    if sys.platform != "win32":
        return False

    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(_STD_INPUT_HANDLE)
    if handle in (0, -1):
        return False

    mode = ctypes.c_uint()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return False

    new_mode = (mode.value | _ENABLE_EXTENDED_FLAGS) & ~_ENABLE_QUICK_EDIT_MODE
    return bool(kernel32.SetConsoleMode(handle, new_mode))
