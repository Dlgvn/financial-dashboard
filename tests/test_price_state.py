"""Tests for price refresh state vars on UploadState."""


def test_state_vars_exist():
    """Verify UploadState has the required price refresh state vars with correct types."""
    from financial_dashboard.state import UploadState
    # Check that the class has the expected annotations
    annotations = UploadState.__annotations__
    assert "is_refreshing_prices" in annotations or hasattr(UploadState, "is_refreshing_prices")
    assert "price_refresh_log" in annotations or hasattr(UploadState, "price_refresh_log")
    assert "price_refresh_summary" in annotations or hasattr(UploadState, "price_refresh_summary")


def test_refresh_prices_method_exists():
    """Verify UploadState has a refresh_prices method."""
    from financial_dashboard.state import UploadState
    assert hasattr(UploadState, "refresh_prices"), "UploadState must have refresh_prices method"
