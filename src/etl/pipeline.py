import asyncio
import time
from src.clients.rapidapi_client import RapidAPIClient
from src.clients.s3_client import S3Client
from src.clients.odoo_client import OdooClient
from src.data_models.rapidapi_lead import RapidAPILead
from src.data_models.transformed_lead import TransformedLead
from src.utils.logger import logger
from typing import List
import datetime
from prometheus_client import Summary, Counter, Histogram, start_http_server
from src.exceptions import DataExtractionError, DataTransformationError, DataLoadError
from src import config

ETL_PIPELINE_DURATION = Summary('etl_pipeline_duration_seconds', 'Total time spent in ETL pipeline run')
ETL_EXTRACT_DURATION = Summary('etl_extract_duration_seconds', 'Time spent in data extraction stage')
ETL_TRANSFORM_DURATION = Summary('etl_transform_duration_seconds', 'Time spent in data transformation stage')
ETL_LOAD_ODOO_DURATION = Summary('etl_load_odoo_duration_seconds', 'Time spent loading data to Odoo')
ETL_LOAD_S3_DURATION = Summary('etl_load_s3_duration_seconds', 'Time spent loading data to S3')

LEADS_EXTRACTED_COUNTER = Counter('etl_leads_extracted_total', 'Total leads extracted from RapidAPI')
LEADS_TRANSFORMED_COUNTER = Counter('etl_leads_transformed_total', 'Total leads transformed')
LEADS_LOADED_ODOO_COUNTER = Counter('etl_leads_loaded_odoo_total', 'Total leads loaded to Odoo')
LEADS_LOADED_S3_COUNTER = Counter('etl_leads_loaded_s3_total', 'Total raw leads loaded to S3')

EXTRACTION_ERRORS_COUNTER = Counter('etl_extraction_errors_total', 'Total data extraction errors')
TRANSFORMATION_ERRORS_COUNTER = Counter('etl_transformation_errors_total', 'Total data transformation errors')
LOAD_ODOO_ERRORS_COUNTER = Counter('etl_load_odoo_errors_total', 'Total errors during Odoo load')
LOAD_S3_ERRORS_COUNTER = Counter('etl_load_s3_errors_total', 'Total errors during S3 load')


class ETLPipeline:
    def __init__(self):
        self.rapidapi_client = RapidAPIClient()
        self.s3_client = S3Client()
        self.odoo_client = OdooClient()

        self.transform_batch_size = config.etl.transform_batch_size
        self.odoo_batch_size = config.etl.odoo_batch_size


    async def extract_data(self) -> List[RapidAPILead]:
        """Extracts data from RapidAPI."""
        logger.info("Starting data extraction from RapidAPI...")
        try:
            extract_start_time = time.monotonic()
            leads = await self.rapidapi_client.fetch_leads()
            ETL_EXTRACT_DURATION.observe(time.monotonic() - extract_start_time)
            LEADS_EXTRACTED_COUNTER.inc(len(leads))
            logger.info("Data extraction from RapidAPI completed.")
            return leads
        except RapidAPIRequestError as e:
            logger.error(f"Data extraction from RapidAPI failed due to request error: {e}")
            EXTRACTION_ERRORS_COUNTER.inc()
            raise DataExtractionError(f"RapidAPI request failed: {e}") from e
        except DataExtractionError as e:
            logger.error(f"Data extraction from RapidAPI failed: {e}")
            EXTRACTION_ERRORS_COUNTER.inc()
            raise
        except Exception as e:
            logger.error(f"Unexpected error during data extraction from RapidAPI: {e}")
            EXTRACTION_ERRORS_COUNTER.inc()
            raise DataExtractionError(f"Unexpected extraction error: {e}") from e

    async def transform_data(self, rapidapi_leads: List[RapidAPILead]) -> List[TransformedLead]:
        """Transforms RapidAPI lead data in concurrent batches."""
        logger.info("Starting batched data transformation...")
        transformed_leads = []
        transform_start_time = time.monotonic()
        total_transformed_in_run = 0
        batch_size = self.transform_batch_size
        for i in range(0, len(rapidapi_leads), batch_size):
            batch = rapidapi_leads[i:i + batch_size]
            tasks = [self._transform_single_lead(lead) for lead in batch]
            batch_transformed = await asyncio.gather(*tasks, return_exceptions=True)
            for result in batch_transformed:
                if isinstance(result, Exception):
                    TRANSFORMATION_ERRORS_COUNTER.inc()
                    logger.error(f"Transformation error in concurrent batch: {result}")
                else:
                    transformed_leads.append(result)
            total_transformed_in_run += len(batch_transformed)
        ETL_TRANSFORM_DURATION.observe(time.monotonic() - transform_start_time)
        LEADS_TRANSFORMED_COUNTER.inc(total_transformed_in_run)
        logger.info(f"Batched data transformation completed. Transformed {len(transformed_leads)} leads.")
        return transformed_leads


    async def _transform_single_lead(self, lead: RapidAPILead) -> TransformedLead:
        """Transforms a single RapidAPI lead to TransformedLead."""
        try:
            transformed_lead = TransformedLead(
                name=f"{lead.first_name} {lead.last_name}".strip(),
                email=lead.email,
                phone=lead.phone,
                partner_name=lead.company,
                description=f"Source: RapidAPI - {lead.source}, Lead ID: {lead.lead_id}"
            )
            return transformed_lead
        except Exception as e:
            lead_identifier = lead.lead_id if hasattr(lead, 'lead_id') else "Unknown Lead ID"
            logger.error(f"Error transforming lead {lead_identifier} in concurrent batch: {e}")
            raise DataTransformationError(f"Error transforming lead ID '{lead_identifier}': {e}") from e

    async def load_to_s3(self, data: list):
        """Loads raw data to AWS S3 for staging/archival."""
        logger.info("Starting data load to S3...")
        s3_load_start_time = time.monotonic()
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        s3_key = f"rapidapi-leads/raw-leads-{timestamp}.json"
        try:
            await self.s3_client.upload_to_s3(data, s3_key)
            ETL_LOAD_S3_DURATION.observe(time.monotonic() - s3_load_start_time)
            LEADS_LOADED_S3_COUNTER.inc(len(data))
            logger.info(f"Data loaded to S3 successfully. Key: {s3_key}")
        except S3StorageError as e:
            logger.error(f"Data load to S3 failed: {e}")
            LOAD_S3_ERRORS_COUNTER.inc()
            raise DataLoadError(f"S3 load failed: {e}") from e
        except DataLoadError as e:
            logger.error(f"Data load to S3 failed: {e}")
            LOAD_S3_ERRORS_COUNTER.inc()
            raise
        except Exception as e:
            logger.error(f"Unexpected error during data load to S3: {e}")
            LOAD_S3_ERRORS_COUNTER.inc()
            raise DataLoadError(f"Unexpected S3 load error: {e}") from e


    async def load_to_odoo(self, transformed_leads: List[TransformedLead]):
        """Loads transformed lead data into Odoo CRM in batches."""
        logger.info("Starting batched data load to Odoo CRM...")
        odoo_load_start_time = time.monotonic()
        total_created_in_run = 0
        created_count = 0
        updated_count = 0
        batch_size = self.odoo_batch_size
        for i in range(0, len(transformed_leads), batch_size):
            lead_batch = transformed_leads[i:i + batch_size]
            odoo_create_data_batch = []
            for lead in lead_batch:
                odoo_data = {
                    'name': lead.name,
                    'email_from': lead.email,
                    'phone': lead.phone,
                    'partner_name': lead.partner_name,
                    'description': lead.description,
                }
                odoo_create_data_batch.append(odoo_data)

            try:
                lead_ids = await self.odoo_client.create_leads_batch(odoo_create_data_batch)
                created_count += len(lead_ids) if lead_ids else 0
                total_created_in_run += len(lead_ids) if lead_ids else 0
                logger.info(f"Batch of {len(lead_ids) if lead_ids else 0} leads created in Odoo.")
            except OdooAPIError as e:
                LOAD_ODOO_ERRORS_COUNTER.inc()
                logger.error(f"Data load to Odoo failed due to API error: {e}")
                raise DataLoadError(f"Odoo API error during load: {e}") from e
            except DataLoadError as e:
                LOAD_ODOO_ERRORS_COUNTER.inc()
                logger.error(f"Data load to Odoo failed: {e}")
                raise
            except Exception as e:
                LOAD_ODOO_ERRORS_COUNTER.inc()
                logger.error(f"Unexpected error during data load to Odoo: {e}")
                raise DataLoadError(f"Unexpected Odoo load error: {e}") from e


        ETL_LOAD_ODOO_DURATION.observe(time.monotonic() - odoo_load_start_time)
        LEADS_LOADED_ODOO_COUNTER.inc(total_created_in_run)
        logger.info(f"Batched data load to Odoo CRM completed. Created {total_created_in_run} leads in this run.")

    async def verify_odoo_data(self, transformed_leads: List[TransformedLead]):
        """Placeholder for verifying created leads exist in Odoo (To be implemented)."""
        logger.info("Starting post-load data verification in Odoo (Placeholder - Not Implemented).")
        pass

    @ETL_PIPELINE_DURATION.time()
    async def run_etl(self):
        """Runs the complete ETL pipeline."""
        logger.info("Starting ETL Pipeline run...")
        start_time = datetime.datetime.now()
        pipeline_start_time = time.monotonic()
        try:
            rapidapi_data = await self.extract_data()
            await self.load_to_s3(rapidapi_data)
            transformed_data = await self.transform_data(rapidapi_data)
            await self.load_to_odoo(transformed_data)
            await self.verify_odoo_data(transformed_data)
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            logger.info(f"ETL Pipeline run completed successfully in {duration}.")
        except DataExtractionError as e:
            logger.error(f"ETL Pipeline failed during data extraction: {e}")
            raise
        except DataTransformationError as e:
            logger.error(f"ETL Pipeline failed during data transformation: {e}")
            raise
        except DataLoadError as e:
            logger.error(f"ETL Pipeline failed during data load: {e}")
            raise
        except Exception as e:
            logger.error(f"ETL Pipeline run failed due to an unexpected error: {e}")
            logger.exception(e)
            raise


async def main():
    pipeline = ETLPipeline()
    await pipeline.run_etl()

if __name__ == "__main__":
    start_http_server(8000)
    asyncio.run(main())
