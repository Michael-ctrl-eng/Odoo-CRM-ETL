import pytest
import aiobotocore.session
from src.clients.s3_client import S3Client
from unittest.mock import AsyncMock, patch, Mock
from src.exceptions import S3StorageError, DataLoadError
import asyncio
import json

@pytest.mark.asyncio
async def test_upload_to_s3_success(mocker, caplog):
    mock_s3_client = AsyncMock()
    mock_session = mocker.patch('aiobotocore.session.get_session')
    mock_session_instance = Mock()
    mock_session_instance.create_client = Mock(return_value=mock_s3_client)
    mock_session.return_value = mock_session_instance

    client = S3Client()
    test_data = [{"key": "value"}]
    test_key = "test-key.json"
    await client.upload_to_s3(test_data, test_key)

    mock_s3_client.put_object.assert_called_once()
    call_kwargs = mock_s3_client.put_object.call_args.kwargs
    assert call_kwargs['Bucket'] == client.bucket_name
    assert call_kwargs['Key'] == test_key
    assert json.loads(call_kwargs['Body'].decode('utf-8')) == test_data
    assert "Data successfully uploaded to S3" in caplog.text

@pytest.mark.asyncio
async def test_upload_to_s3_error(mocker, caplog):
    mock_s3_client = AsyncMock()
    mock_s3_client.put_object.side_effect = Exception("S3 Upload Failed")
    mock_session = mocker.patch('aiobotocore.session.get_session')
    mock_session_instance = Mock()
    mock_session_instance.create_client = Mock(return_value=mock_s3_client)
    mock_session.return_value = mock_session_instance

    client = S3Client()
    test_data = [{"key": "value"}]
    test_key = "test-key.json"

    with pytest.raises(S3StorageError) as exc_info:
        await client.upload_to_s3(test_data, test_key)

    assert "Error uploading data to S3" in str(exc_info.value)
    assert "Error uploading data to S3" in caplog.text

@pytest.mark.asyncio
async def test_upload_to_s3_data_load_error_propagation(mocker, caplog):
    mock_s3_client = AsyncMock()
    mock_s3_client.put_object.side_effect = Exception("S3 Upload Failed")
    mock_session = mocker.patch('aiobotocore.session.get_session')
    mock_session_instance = Mock()
    mock_session_instance.create_client = Mock(return_value=mock_s3_client)
    mock_session.return_value = mock_session_instance

    client = S3Client()
    test_data = [{"key": "value"}]
    test_key = "test-key.json"

    with pytest.raises(DataLoadError) as exc_info:
        await client.upload_to_s3(test_data, test_key)

    assert isinstance(exc_info.value, DataLoadError)
