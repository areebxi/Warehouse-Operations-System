from scripts.app.util.win_console import configure_windows_console


def test_configure_windows_console_is_safe_on_all_platforms() -> None:
    # Should not raise on Windows or non-Windows.
    result = configure_windows_console()
    assert isinstance(result, bool)
