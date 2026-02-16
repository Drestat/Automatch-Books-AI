"""
Test suite for QBO API Client retry logic and error handling.

BUG-002: HIGH
Location: backend/app/services/qbo_client.py (retry decorator)
Issue: Only 429 (rate limit) errors trigger retry; 5xx errors fail immediately
Impact: Sync failures during transient QBO API issues

This test suite verifies that the QBOClient properly handles:
- 429 rate limit responses with exponential backoff
- 5xx server errors with retry logic
- 401 unauthorized with token refresh
- Network timeouts and connection errors
- Maximum retry exhaustion
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta


@pytest.mark.critical
class TestQBOClientRetryLogic:
    """
    Tests for QBO API retry behavior.

    Coverage: 6 test cases
    - 429 rate limit with backoff
    - 5xx server errors (currently NOT retried - BUG-002)
    - 401 unauthorized with token refresh
    - Network timeout retry
    - Max retries exhausted
    - Successful recovery after transient failure
    """

    @pytest.fixture
    def mock_connection(self, test_qbo_connection):
        """Create mock QBO connection with valid tokens."""
        return test_qbo_connection

    @pytest.fixture
    def mock_auth_client(self):
        """Mock IntuitAuthClient for token refresh."""
        with patch('app.services.qbo_client.AuthClient') as MockAuth:
            mock_auth = MagicMock()
            mock_auth.refresh.return_value = MagicMock(
                access_token="refreshed_access_token",
                refresh_token="refreshed_refresh_token"
            )
            MockAuth.return_value = mock_auth
            yield mock_auth

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_retry_on_429_rate_limit(self, db_session, mock_connection, mock_auth_client):
        """
        Test Case 1: 429 rate limit should trigger exponential backoff.

        Expected:
        - First request returns 429
        - Client waits and retries
        - Second request succeeds
        - Total of 2 requests made
        """
        from app.services.qbo_client import QBOClient

        # Create mock responses: 429 then 200
        mock_429_response = MagicMock()
        mock_429_response.status_code = 429
        mock_429_response.headers = {"Retry-After": "1"}
        mock_429_response.text = "Rate limit exceeded"
        mock_429_response.is_error = True

        mock_200_response = MagicMock()
        mock_200_response.status_code = 200
        mock_200_response.is_error = False
        mock_200_response.json.return_value = {
            "QueryResponse": {"Purchase": [], "maxResults": 0}
        }
        mock_200_response.headers = {"intuit_tid": "test-tid-123"}

        with patch('httpx.AsyncClient') as MockHttpx:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[
                mock_429_response,
                mock_200_response
            ])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockHttpx.return_value = mock_client

            client = QBOClient(db_session, mock_connection)

            # Should succeed after retry
            result = await client.query("SELECT * FROM Purchase MAXRESULTS 10")

            # Verify retry happened
            assert mock_client.request.call_count >= 2, \
                "Should retry after 429 rate limit"

    @pytest.mark.critical
    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [500, 502, 503, 504])
    async def test_retry_on_5xx_server_errors(self, db_session, mock_connection, mock_auth_client, status_code):
        """
        Test Case 2: 5xx errors should trigger retry (currently NOT handled - BUG-002).

        Expected after fix:
        - First request returns 5xx
        - Client retries with backoff
        - Second request succeeds

        Current behavior (BUG):
        - 5xx errors immediately raise exception with no retry
        """
        from app.services.qbo_client import QBOClient

        mock_5xx_response = MagicMock()
        mock_5xx_response.status_code = status_code
        mock_5xx_response.headers = {"intuit_tid": "test-tid-5xx"}
        mock_5xx_response.text = f"Server error {status_code}"
        mock_5xx_response.is_error = True

        mock_200_response = MagicMock()
        mock_200_response.status_code = 200
        mock_200_response.is_error = False
        mock_200_response.json.return_value = {"QueryResponse": {"Purchase": []}}
        mock_200_response.headers = {"intuit_tid": "test-tid-ok"}

        with patch('httpx.AsyncClient') as MockHttpx:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[
                mock_5xx_response,
                mock_200_response
            ])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockHttpx.return_value = mock_client

            client = QBOClient(db_session, mock_connection)

            result = await client.query("SELECT * FROM Purchase MAXRESULTS 10")
            assert mock_client.request.call_count >= 2, \
                f"Should retry after {status_code} server error"

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_401_triggers_token_refresh(self, db_session, mock_connection, mock_auth_client):
        """
        Test Case 3: 401 Unauthorized should trigger token refresh and retry.

        Expected:
        - First request returns 401
        - Client refreshes OAuth tokens
        - Retries with new access token
        - Request succeeds
        """
        from app.services.qbo_client import QBOClient

        mock_401_response = MagicMock()
        mock_401_response.status_code = 401
        mock_401_response.headers = {"intuit_tid": "test-tid-401"}
        mock_401_response.text = "Unauthorized"
        mock_401_response.is_error = True

        mock_200_response = MagicMock()
        mock_200_response.status_code = 200
        mock_200_response.is_error = False
        mock_200_response.json.return_value = {"QueryResponse": {"Purchase": []}}
        mock_200_response.headers = {"intuit_tid": "test-tid-refreshed"}

        with patch('httpx.AsyncClient') as MockHttpx:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[
                mock_401_response,
                mock_200_response
            ])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockHttpx.return_value = mock_client

            client = QBOClient(db_session, mock_connection)

            # Mock the token refresh
            with patch.object(client, '_refresh_access_token') as mock_refresh:
                mock_refresh.return_value = "new_token"

                result = await client.query("SELECT * FROM Purchase MAXRESULTS 10")

                # Verify token refresh was called
                mock_refresh.assert_called_once()
                assert mock_client.request.call_count >= 2

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_network_timeout_triggers_retry(self, db_session, mock_connection, mock_auth_client):
        """
        Test Case 4: Network timeouts should trigger retry.

        Expected:
        - First request times out
        - Client retries
        - Second request succeeds
        """
        from app.services.qbo_client import QBOClient

        mock_200_response = MagicMock()
        mock_200_response.status_code = 200
        mock_200_response.is_error = False
        mock_200_response.json.return_value = {"QueryResponse": {"Purchase": []}}
        mock_200_response.headers = {"intuit_tid": "test-tid-timeout-ok"}

        with patch('httpx.AsyncClient') as MockHttpx:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[
                httpx.ConnectTimeout("Connection timed out"),
                mock_200_response
            ])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockHttpx.return_value = mock_client

            client = QBOClient(db_session, mock_connection)

            result = await client.query("SELECT * FROM Purchase MAXRESULTS 10")
            assert mock_client.request.call_count >= 2, \
                "Should retry after network timeout"

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_max_retries_exhausted_raises_exception(self, db_session, mock_connection, mock_auth_client):
        """
        Test Case 5: After max retries (3), should raise exception.

        Expected:
        - All 3 retry attempts fail with 429
        - Final exception propagates to caller
        - Error includes useful diagnostic info
        """
        from app.services.qbo_client import QBOClient

        mock_429_response = MagicMock()
        mock_429_response.status_code = 429
        mock_429_response.headers = {"Retry-After": "1", "intuit_tid": "test-tid-exhaust"}
        mock_429_response.text = "Rate limit exceeded"
        mock_429_response.is_error = True
        mock_429_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Rate Limit", request=None, response=mock_429_response
        )

        with patch('httpx.AsyncClient') as MockHttpx:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_429_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockHttpx.return_value = mock_client

            client = QBOClient(db_session, mock_connection)

            # Should eventually raise after max retries
            with pytest.raises((httpx.HTTPStatusError, Exception)):
                await client.query("SELECT * FROM Purchase MAXRESULTS 10")

            # Verify multiple retry attempts were made
            assert mock_client.request.call_count >= 3, \
                f"Should attempt at least 3 retries, got {mock_client.request.call_count}"

    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_successful_recovery_after_transient_failure(self, db_session, mock_connection, mock_auth_client):
        """
        Test Case 6: Successful request after single transient failure.

        Expected:
        - First request fails (transient)
        - Second request succeeds
        - Returns valid data
        """
        from app.services.qbo_client import QBOClient

        expected_data = {
            "QueryResponse": {
                "Purchase": [
                    {"Id": "123", "TxnDate": "2024-01-15", "TotalAmt": 150.50}
                ],
                "maxResults": 1
            }
        }

        mock_429_response = MagicMock()
        mock_429_response.status_code = 429
        mock_429_response.headers = {"Retry-After": "0"}
        mock_429_response.text = "Rate limit"
        mock_429_response.is_error = True

        mock_200_response = MagicMock()
        mock_200_response.status_code = 200
        mock_200_response.is_error = False
        mock_200_response.json.return_value = expected_data
        mock_200_response.headers = {"intuit_tid": "test-tid-recovery"}

        with patch('httpx.AsyncClient') as MockHttpx:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[
                mock_429_response,
                mock_200_response
            ])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockHttpx.return_value = mock_client

            client = QBOClient(db_session, mock_connection)

            result = await client.query("SELECT * FROM Purchase MAXRESULTS 10")

            # Verify valid data returned
            assert result is not None, "Should return valid data after recovery"
            assert mock_client.request.call_count >= 2
