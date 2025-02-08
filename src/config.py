from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, HttpUrl, validator, conint

class RapidAPISettings(BaseSettings):
    api_key: str = Field(..., description="RapidAPI API Key")
    base_url: HttpUrl = Field(..., description="RapidAPI Base URL")
    endpoint: str = Field("/leads", description="RapidAPI Endpoint")
    timeout: conint(ge=1, default=10, description="RapidAPI Request Timeout (seconds)")

    model_config = SettingsConfigDict(section="rapidapi", case_sensitive=False)

    @validator("base_url")
    def validate_base_url_protocol(cls, url):
        """Ensure base URL starts with https:// or http://"""
        if not str(url).startswith(('http://', 'https://')):
            raise ValueError("RapidAPI base URL must start with 'http://' or 'https://'")
        return url


class AWSSettings(BaseSettings):
    s3_bucket_name: str = Field(..., description="AWS S3 Bucket Name")
    region_name: str = Field(..., description="AWS Region Name")
    access_key_id: str = Field(..., description="AWS Access Key ID")
    secret_access_key: str = Field(..., description="AWS Secret Access Key")

    model_config = SettingsConfigDict(section="aws", case_sensitive=False)

    @validator("region_name")
    def validate_aws_region(cls, value):
        """Validate AWS region against a list of valid regions."""
        valid_regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-2", "ap-northeast-1"]
        if value not in valid_regions:
            raise ValueError(f"Invalid AWS region '{value}'. Valid regions are: {valid_regions}")
        return value


class OdooSettings(BaseSettings):
    url: HttpUrl = Field(..., description="Odoo Instance URL")
    db: str = Field(..., description="Odoo Database Name")
    username: str = Field(..., description="Odoo Username")
    password: str = Field(..., description="Odoo Password")
    lead_model: str = Field("crm.lead", description="Odoo Lead Model")
    xmlrpc_path: str = Field("/xmlrpc/2", description="Odoo XML-RPC Path")

    model_config = SettingsConfigDict(section="odoo", case_sensitive=False)

    @validator("url")
    def validate_odoo_url_protocol(cls, url):
        """Ensure Odoo URL starts with https:// or http://"""
        if not str(url).startswith(('http://', 'https://')):
            raise ValueError("Odoo URL must start with 'http://' or 'https://'")
        return url

    class ETLSettings(BaseSettings):
        transform_batch_size: conint(ge=1, default=100, description="Batch size for data transformation")
        odoo_batch_size: conint(ge=1, default=20, description="Batch size for Odoo load operations")

        model_config = SettingsConfigDict(section="etl", case_sensitive=False)

    class RetrySettings(BaseSettings):
        max_attempts: conint(ge=1, default=3, description="Maximum retry attempts for API requests")
        wait_seconds: conint(ge=1, default=2, description="Wait time in seconds between retry attempts")

        model_config = SettingsConfigDict(section="retry", case_sensitive=False)


    class Settings(BaseSettings):
        rapidapi: RapidAPISettings
        aws: AWSSettings
        odoo: OdooSettings
        etl: ETLSettings
        retry: RetrySettings

        model_config = SettingsConfigDict(config_path='config/config.yaml', case_sensitive=False)


    settings = Settings()
