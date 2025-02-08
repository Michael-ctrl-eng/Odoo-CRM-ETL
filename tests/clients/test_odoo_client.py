import pytest
import xmlrpc.client
from src.clients.odoo_client import OdooClient
from unittest.mock import patch, Mock, AsyncMock
from src.exceptions import OdooAPIError, DataLoadError
import asyncio

@pytest.fixture
def odoo_client():
    with patch('xmlrpc.client.ServerProxy') as MockServerProxy:
        client = OdooClient()
        client.models = MockServerProxy.return_value
        return client

@pytest.mark.asyncio
async def test_odoo_client_create_lead_success(odoo_client, caplog):
    mock_lead_id = 123
    odoo_client.models.execute_kw.return_value = mock_lead_id

    test_lead_data = Mock()
    test_lead_data.name = "Test Lead"
    test_lead_data.email = "test@example.com"

    lead_id = await odoo_client.create_lead(test_lead_data)

    assert lead_id == mock_lead_id
    odoo_client.models.execute_kw.assert_called_once()
    assert "Lead created in Odoo" in caplog.text

@pytest.mark.asyncio
async def test_odoo_client_create_lead_api_error(odoo_client, caplog):
    odoo_client.models.execute_kw.side_effect = xmlrpc.client.Fault(100, "Odoo API Error")

    test_lead_data = Mock()
    test_lead_data.name = "Test Lead"
    test_lead_data.email = "test@example.com"

    with pytest.raises(OdooAPIError) as exc_info:
        await odoo_client.create_lead(test_lead_data)

    assert "Odoo API Fault" in str(exc_info.value)
    assert "Odoo API Fault (Create Lead)" in caplog.text

@pytest.mark.asyncio
async def test_odoo_client_create_lead_data_load_error_propagation(odoo_client, caplog):
    odoo_client.models.execute_kw.side_effect = xmlrpc.client.Fault(100, "Odoo API Error")

    test_lead_data = Mock()
    test_lead_data.name = "Test Lead"
    test_lead_data.email = "test@example.com"

    with pytest.raises(DataLoadError) as exc_info:
        await odoo_client.create_lead(test_lead_data)

    assert isinstance(exc_info.value, DataLoadError)

@pytest.mark.asyncio
async def test_odoo_client_create_leads_batch_success(odoo_client, caplog):
    mock_lead_ids = [456, 457]
    odoo_client.models.execute_kw.return_value = mock_lead_ids

    test_leads_data_batch = [{}, {}]

    lead_ids = await odoo_client.create_leads_batch(test_leads_data_batch)

    assert lead_ids == mock_lead_ids
    odoo_client.models.execute_kw.assert_called_once()
    assert "Batch of 2 leads submitted to Odoo" in caplog.text

@pytest.mark.asyncio
async def test_odoo_client_create_leads_batch_api_error(odoo_client, caplog):
    odoo_client.models.execute_kw.side_effect = xmlrpc.client.Fault(100, "Odoo Batch API Error")

    test_leads_data_batch = [{}, {}]

    with pytest.raises(OdooAPIError) as exc_info:
        await odoo_client.create_leads_batch(test_leads_data_batch)

    assert "Odoo API Fault" in str(exc_info.value)
    assert "Odoo API Fault (Batch Create Leads)" in caplog.text

@pytest.mark.asyncio
async def test_odoo_client_update_lead_success(odoo_client, caplog):
    odoo_client.models.execute_kw.return_value = True

    test_lead_id = 789
    test_lead_data = Mock()
    test_lead_data.name = "Updated Lead"
    test_lead_data.email = "updated@example.com"

    updated = await odoo_client.update_lead(test_lead_id, test_lead_data)

    assert updated is True
    odoo_client.models.execute_kw.assert_called_once()
    assert "Lead updated in Odoo" in caplog.text

@pytest.mark.asyncio
async def test_odoo_client_update_lead_api_error(odoo_client, caplog):
    odoo_client.models.execute_kw.side_effect = xmlrpc.client.Fault(100, "Odoo Update API Error")

    test_lead_id = 789
    test_lead_data = Mock()
    test_lead_data.name = "Updated Lead"
    test_lead_data.email = "updated@example.com"

    with pytest.raises(OdooAPIError) as exc_info:
        await odoo_client.update_lead(test_lead_id, test_lead_data)

    assert "Odoo API Fault" in str(exc_info.value)
    assert "Odoo API Fault (Update Lead)" in caplog.text
