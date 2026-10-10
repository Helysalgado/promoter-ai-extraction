"""Smoke test: confirms the installed package is importable and versioned (T002)."""

from promoter_ai_extraction import __version__


def test_package_version_is_string() -> None:
    """Package has a string __version__, proving src/ layout and install work."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0
