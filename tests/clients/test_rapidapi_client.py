import pytest
from src.clients.rapidapi_client import RapidAPIClient
from src.data_models.rapidapi_lead import RapidAPILead
import aiohttp
from unittest.mock import AsyncMock, Mock
from src.exceptions import RapidAPIRequestError, DataExtractionError

@pytest.mark.asyncio
async def test_fetch_leads_success(mocker, caplog):
    mock_response_data = [{"lead_id": "1", "first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "source": "API"}]
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)

    mock_aiohttp_session = mocker.patch('aiohttp.ClientSession')
    mock_session_instance = AsyncMock()
    mock_session_instance.get = AsyncMock(return_value=mock_response)
    mock_aiohttp_session.return_value.__aenter__.return_value = mock_session_instance

    client = RapidAPIClient()
    leads = await client.fetch_leads()

    mock_aiohttp_session.assert_called_once()
    mock_session_instance.get.assert_called_once()
    assert isinstance(leads, list)
    assert len(leads) == 1
    assert isinstance(leads[0], RapidAPILead)
    assert leads[0].first_name == "John"
    assert "Successfully fetched" in caplog.text


@pytest.mark.asyncio
async def test_fetch_leads_http_error(mocker, caplog):
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.raise_for_status = Mock(side_effect=aiohttp.ClientResponseError(None, None))

    mock_aiohttp_session = mocker.patch('aiohttp.ClientSession')
    mock_session_instance = AsyncMock()
    mock_session_instance.get = AsyncMock(return_value=mock_response)
    mock_aiohttp_session.return_value.__aenter__.return_value = mock_session_instance

    client = RapidAPIClient()
    with pytest.raises(RapidAPIRequestError) as exc_info:
        await client.fetch_leads()

    assert "AIOHTTP Client Error" in str(exc_info.value)
    assert "Error fetching data from RapidAPI" in caplog.text

@pytest.mark.asyncio
async def test_fetch_leads_unexpected_error(mocker, caplog):
    mock_aiohttp_session = mocker.patch('aiohttp.ClientSession')
    mock_session_instance = AsyncMock()
    mock_session_instance.get = Mock(side_effect=ValueError("Unexpected error"))
    mock_aiohttp_session.return_value.__aenter__.return_value = mock_session_instance

    client = RapidAPIClient()
    with pytest.raises(DataExtractionError) as exc_info:
        await client.fetch_leads()

    assert "Unexpected error during RapidAPI data fetching" in str(exc_info.value)
    assert "Unexpected error during RapidAPI data fetching" in caplog.text


@pytest.mark.asyncio
async def test_fetch_leads_validation_error(mocker, caplog):
    mock_response_data = [{"lead_id": "2", "first_name": "Jane", "last_name": "Doe", "email": "invalid-email", "source": "API"}]
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)

    mock_aiohttp_session = mocker.patch('aiohttp.ClientSession')
    mock_session_instance = AsyncMock()
    mock_session_instance.get = AsyncMock(return_value=mock_response)
    mock_aiohttp_session.return_value.__aenter__.return_value = mock_session_instance

    client = RapidAPIClient()
    leads = await client.fetch_leads()
    assert len(leads) == 0
    assert "Pydantic validation error" in caplog.text
    assert "Successfully fetched and validated 0 leads" in caplog.text

@pytest.mark.asyncio
async def test_fetch_leads_retry_success_after_failure(mocker, caplog):
    mock_response_data = [{"lead_id": "3", "first_name": "Retry", "last_name": "Lead", "email": "retry.lead@example.com", "source": "API"}]
    mock_response_success = AsyncMock()
    mock_response_success.status = 200
    mock_response_success.json = AsyncMock(return_value=mock_response_data)

    mock_response_failure = AsyncMock()
    mock_response_failure.status = 503
    mock_response_failure.raise_for_status = Mock(side_effect=aiohttp.ClientResponseError(None, None))

    mock_aiohttp_session = mocker.patch('aiohttp.ClientSession')
    mock_session_instance = AsyncMock()
    mock_session_instance.get = Mock(side_effect=[mock_response_failure, mock_response_success])
    mock_aiohttp_session.return_value.__aenter__.return_value = mock_session_instance

    client = RapidAPIClient()
    leads = await client.fetch_leads()

    assert len(leads) == 1
    assert "Wait 2 seconds then retry" in caplog.text
    assert mock_session_instance.get.call_count == 2
    assert "Successfully fetched" in caplog.text
