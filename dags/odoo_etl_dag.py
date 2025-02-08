from airflow import DAG
from airflow.decorators import task
from datetime import datetime, timedelta
from src.etl.pipeline import ETLPipeline
import asyncio
from src.utils.logger import logger
from airflow.exceptions import AirflowException

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
}

dag = DAG(
    'odoo_rapidapi_etl',
    default_args=default_args,
    description='ETL Pipeline for RapidAPI Leads to Odoo CRM',
    schedule_interval=timedelta(minutes=30),
    catchup=False,
    tags=['odoo', 'etl', 'rapidapi', 's3', 'crm']
)

pipeline = ETLPipeline()

@task(retries=3, retry_delay=timedelta(minutes=5), task_id='extract_data_task')
def extract():
    logger.info("Starting extract task in Airflow.")
    try:
        return asyncio.run(pipeline.extract_data())
    except Exception as e:
        logger.error(f"Extract task failed: {e}")
        raise AirflowException(f"Data extraction failed. Check logs for details: {e}") from e

@task(retries=3, retry_delay=timedelta(minutes=5), task_id='transform_data_task')
def transform(extracted_data):
    logger.info("Starting transform task in Airflow.")
    try:
        return asyncio.run(pipeline.transform_data(extracted_data))
    except Exception as e:
        logger.error(f"Transform task failed: {e}")
        raise AirflowException(f"Data transformation failed. Check logs for details: {e}") from e

@task(retries=3, retry_delay=timedelta(minutes=5), task_id='load_s3_task')
def load_s3(extracted_data):
    logger.info("Starting load to S3 task in Airflow.")
    try:
        return asyncio.run(pipeline.load_to_s3(extracted_data))
    except Exception as e:
        logger.error(f"Load to S3 task failed: {e}")
        raise AirflowException(f"Load to S3 failed. Check logs for details: {e}") from e

@task(retries=3, retry_delay=timedelta(minutes=5), task_id='load_odoo_task')
def load_odoo(transformed_data):
    logger.info("Starting load to Odoo task in Airflow.")
    try:
        return asyncio.run(pipeline.load_to_odoo(transformed_data))
    except Exception as e:
        logger.error(f"Load to Odoo task failed: {e}")
        raise AirflowException(f"Load to Odoo failed. Check logs for details: {e}") from e

verify_odoo_data = PythonOperator( # Using PythonOperator for verify task as decorator might not be best for placeholder
    task_id='verify_odoo_data_task',
    python_callable=lambda: asyncio.run(pipeline.verify_odoo_data(None)), # Pass None as transformed_leads for placeholder
    retries=1, # Less retries for verification - adjust as needed
    retry_delay=timedelta(minutes=5),
)

extract_task = extract()
transform_task = transform(extract_task)
load_s3_task = load_s3(extracted_data=extract_task)
load_odoo_task = load_odoo(transformed_data=transform_task)

extract_task >> [transform_task, load_s3_task] >> load_odoo_task >> verify_odoo_data # Added verify_odoo_data to DAG flow
