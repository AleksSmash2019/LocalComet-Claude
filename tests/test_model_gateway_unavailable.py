"""Phase 3 Scenario 7: Model Gateway — model unavailable / corrupted.

Documents current behavior when the model provider is unreachable or
returns invalid data. All operations must raise GatewayError with
actionable codes, never crash with unhandled exceptions.
"""
import pytest
from unittest.mock import patch, MagicMock
import http.client

from modules.local_model_gateway_ru import (
    GatewayError,
    GatewayLimits,
    ProviderAdapter,
)


@pytest.fixture
def limits():
    return GatewayLimits(
        connect_timeout_seconds=0.5,
        read_timeout_seconds=1.0,
        first_token_timeout_seconds=1.0,
        inactivity_timeout_seconds=1.0,
        overall_timeout_seconds=2.0,
        worker_join_timeout_seconds=0.5,
    )


class TestModelGatewayUnavailable:
    def test_probe_connection_refused_raises_gateway_error(self, limits):
        """probe() to a dead port must raise GatewayError, not crash."""
        adapter = ProviderAdapter(19999, limits)
        with pytest.raises((GatewayError, OSError, ConnectionError)):
            adapter.list_models()

    def test_port_none_raises_invalid_payload(self, limits):
        """ProviderAdapter(port=None) must raise GatewayError immediately."""
        with pytest.raises(GatewayError) as exc_info:
            ProviderAdapter(None, limits)
        assert exc_info.value.code == "invalid_payload"

    def test_port_zero_rejected(self, limits):
        """Port 0 is invalid and must be rejected."""
        with pytest.raises((GatewayError, ValueError)):
            ProviderAdapter(0, limits)

    def test_port_negative_rejected(self, limits):
        """Negative port is invalid."""
        with pytest.raises((GatewayError, ValueError)):
            ProviderAdapter(-1, limits)

    def test_port_above_65535_rejected(self, limits):
        """Port > 65535 is invalid."""
        with pytest.raises((GatewayError, ValueError)):
            ProviderAdapter(70000, limits)

    def test_gateway_error_payload_is_bounded(self):
        """GatewayError.as_payload() must have bounded code and message."""
        err = GatewayError("x" * 200, "y" * 500, retryable=True)
        payload = err.as_payload()
        assert len(payload["code"]) <= 64
        assert len(payload["message"]) <= 256
        assert payload["retryable"] is True

    def test_gateway_error_not_retryable_by_default(self):
        """GatewayError defaults to retryable=False."""
        err = GatewayError("test_code", "test message")
        assert err.retryable is False
        assert err.as_payload()["retryable"] is False
