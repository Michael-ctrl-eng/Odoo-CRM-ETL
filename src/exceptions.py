class ETLError(Exception):
    """Base class for ETL pipeline exceptions."""
    pass

class DataExtractionError(ETLError):
    """Exception raised during data extraction from RapidAPI."""
    pass

class DataTransformationError(ETLError):
    """Exception raised during data transformation."""
    pass

class DataLoadError(ETLError):
    """Exception raised during data load to Odoo or S3."""
    pass

class OdooAPIError(DataLoadError):
    """Exception specific to Odoo API interactions."""
    pass

class S3StorageError(DataLoadError):
    """Exception specific to S3 storage operations."""
    pass

class RapidAPIRequestError(DataExtractionError):
    """Exception specific to RapidAPI request failures."""
    pass
