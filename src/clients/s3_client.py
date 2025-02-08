import aiobotocore.session
import asyncio
import json
from src.utils.logger import logger
from src import config
from src.exceptions import S3StorageError, DataLoadError

class S3Client:
    def __init__(self):
        self.bucket_name = config.aws.s3_bucket_name
        self.region_name = config.aws.region_name
        self.access_key_id = config.aws.access_key_id
        self.secret_access_key = config.aws.secret_access_key
        self.session = aiobotocore.session.get_session()

    async def upload_to_s3(self, data: list, key: str):
        """Uploads data to S3 as JSON asynchronously."""
        logger.info(f"Uploading data to S3 bucket: {self.bucket_name}, key: {key}")
        try:
            async with self.session.create_client('s3', region_name=self.region_name,
                                                  aws_access_key_id=self.access_key_id,
                                                  aws_secret_access_key=self.secret_access_key) as client:
                json_data = json.dumps(data, indent=2).encode('utf-8')
                await client.put_object(Bucket=self.bucket_name, Key=key, Body=json_data)
                logger.info(f"Data successfully uploaded to S3 bucket: {self.bucket_name}, key: {key}")
        except Exception as e:
            logger.error(f"Error uploading data to S3: {e}")
            raise S3StorageError(f"Error uploading data to S3 bucket '{self.bucket_name}', key '{key}': {e}")
