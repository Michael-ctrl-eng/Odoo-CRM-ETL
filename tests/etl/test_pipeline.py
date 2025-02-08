import pytest
from src.etl.pipeline import ETLPipeline
from unittest.mock import AsyncMock, patch, Mock
from src.exceptions import DataExtractionError, DataTransformationError, DataLoadError
import asyncio

@pytest.fixture
def etl_pipeline():
    pipeline = ETLPipeline()
    pipeline.rapidapi_client = Mock()
    pipeline.s3_client = Mock()
    pipeline.odoo_client = Mock()
    return pipeline

@pytest.mark.asyncio
async def test_etl_pipeline_run_etl_success(etl_pipeline, caplog):
    etl_pipeline.rapidapi_client.fetch_leads = AsyncMock(return_value=[Mock()])
    etl_pipeline.transform_data = AsyncMock(return_value=[Mock()])
    etl_pipeline.s3_client.upload_to_s3 = AsyncMock(return_value=None)
    etl_pipeline.odoo_client.create_leads_batch = AsyncMock(return_value=[1])

    await etl_pipeline.run_etl()

    etl_pipeline.rapidapi_client.fetch_leads.assert_called_once()
    etl_pipeline.s3_client.upload_to_s3.assert_called_once()
    etl_pipeline.odoo_client.create_leads_batch.assert_called_once()
    assert "ETL Pipeline run completed successfully" in caplog.text

@pytest.mark.asyncio
async def test_etl_pipeline_run_etl_extraction_error(etl_pipeline, caplog):
    etl_pipeline.rapidapi_client.fetch_leads = AsyncMock(side_effect=DataExtractionError("Extraction Failed"))

    with pytest.raises(DataExtractionError) as exc_info:
        await etl_pipeline.run_etl()

    assert "ETL Pipeline failed during data extraction" in caplog.text
    assert "Extraction Failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_etl_pipeline_run_etl_transformation_error(etl_pipeline, caplog):
    etl_pipeline.rapidapi_client.fetch_leads = AsyncMock(return_value=[Mock()])
    etl_pipeline.transform_data = AsyncMock(side_effect=DataTransformationError("Transformation Failed"))

    with pytest.raises(DataTransformationError) as exc_info:
        await etl_pipeline.run_etl()

    assert "ETL Pipeline failed during data transformation" in caplog.text
    assert "Transformation Failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_etl_pipeline_run_etl_load_error(etl_pipeline, caplog):
    etl_pipeline.rapidapi_client.fetch_leads = AsyncMock(return_value=[Mock()])
    etl_pipeline.transform_data = AsyncMock(return_value=[Mock()])
    etl_pipeline.odoo_client.create_leads_batch = AsyncMock(side_effect=DataLoadError("Odoo Load Failed"))

    with pytest.raises(DataLoadError) as exc_info:
        await etl_pipeline.run_etl()

    assert "ETL Pipeline failed during data load" in caplog.text
    assert "Odoo Load Failed" in str(exc_info.value)
