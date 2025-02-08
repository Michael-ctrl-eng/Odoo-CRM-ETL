import aiohttp
import asyncio
from src.utils.logger import logger
from src import config
from src.data_models.rapidapi_lead import RapidAPILead
from typing import List
from tenacity import retry, wait_fixed, stop_after_attempt, before_log, after_log, retry_if_exception_type
import logging, sys
from src.exceptions import RapidAPIRequestError, DataExtractionError

retry_logger = logging.getLogger("tenacity_logger")
retry_logger.setLevel(logging.WARNING)
retry_handler = logging.StreamHandler(sys.stdout)
retry_logger.addHandler(retry_handler)

def sensitive_data_filter(record):
    message = record["message"]
    record["message"] = message.replace(config.rapidapi.api_key, "[API_KEY_MASKED]")
    return True
logger.add_filter(sensitive_data_filter)


class RapidAPIClient:
    def __init__(self):
        self.api_key = config.rapidapi.api_key
        self.base_url = str(config.rapidapi.base_url)
        self.endpoint = config.rapidapi.endpoint
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": config.rapidapi.base_url.host
        }
        self.request_timeout = config.etl.rapidapi_timeout

    @retry(wait=wait_fixed(config.retry.wait_seconds),
           stop=stop_after_attempt(config.retry.max_attempts),
           retry=retry_if_exception_type(aiohttp.ClientError),
           before_log=before_log(retry_logger, logging.INFO),
           after_log=after_log(retry_logger, logging.WARNING)
           )
    async def fetch_leads(self) -> List[RapidAPILead]:
        """Fetches leads from RapidAPI asynchronously with retries and timeout."""
        url = f"{self.base_url}{self.endpoint}"
        logger.info(f"Fetching leads from RapidAPI endpoint: {url}")
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
                async with session.get(url, headers=self.headers) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if not isinstance(data, list):
                        logger.warning(f"Unexpected RapidAPI response format: Not a list. Response: {data}")
                        return []

                    leads = []
                    for lead_data in data:
                        try:
                            lead = RapidAPILead(**lead_data)
                            leads.append(lead)
                        except Exception as validation_error:
                            logger.error(f"Pydantic validation error for RapidAPI lead data: {validation_error}. Data: {lead_data}")
                    logger.info(f"Successfully fetched and validated {len(leads)} leads from RapidAPI.")
                    return leads
        except aiohttp.ClientError as e:
            logger.error(f"AIOHTTP Client Error fetching data from RapidAPI: {e}")
            raise RapidAPIRequestError(f"Error fetching data from RapidAPI: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during RapidAPI data fetching: {e}")
            raise DataExtractionError(f"Unexpected error fetching from RapidAPI: {e}")
