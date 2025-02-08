# Odoo CRM ETL Pipeline for Real-time Lead Management

## Project Overview

This project implements a robust Extract, Transform, Load (ETL) pipeline designed to integrate lead data from external sources, specifically RapidAPI, into Odoo CRM. The pipeline leverages cloud-based storage on AWS S3 for staging raw data and is built for real-time, asynchronous operation to ensure efficient data processing and seamless lead management within Odoo. Orchestration is handled by Apache Airflow, providing scheduled execution, monitoring, and automated retry mechanisms for a reliable and production-ready solution.

The primary objective is to enhance lead management and analytics within Odoo CRM by automating the ingestion of external lead data, ensuring data quality and timeliness.

## Key Features

*   **Real-time Data Integration:** Near real-time data flow from RapidAPI to Odoo CRM, facilitating timely lead management.
*   **Asynchronous Architecture:** Utilizes Python's `asyncio` framework along with `aiohttp` and `aiobotocore` for optimized I/O operations and non-blocking execution.
*   **Comprehensive Data Validation:** Implements rigorous data validation using Pydantic at each stage of the ETL process to maintain data integrity and accuracy.
*   **Flexible Data Transformation:** Employs customizable transformation logic to map and cleanse lead data from RapidAPI to the Odoo CRM data model.
*   **AWS S3 Data Staging:** Stages raw, unprocessed lead data in AWS S3 for archival, audit trails, and potential data reprocessing.
*   **Odoo CRM Integration:** Loads transformed and validated lead data into Odoo CRM via the XML-RPC API, ensuring compatibility with Odoo 17.0 and later versions.
*   **Apache Airflow Orchestration:** Manages the ETL workflow using Apache Airflow for scheduled execution, task dependency management, automated retries, and centralized monitoring.
*   **Granular Error Handling:** Implements robust error handling with custom exception types and detailed logging to facilitate rapid issue identification and resolution.
*   **Performance Metrics and Monitoring:** Integrates Prometheus client to collect and expose key performance indicators (KPIs) such as pipeline duration, stage-specific timings, lead counts, and error metrics, enabling performance monitoring and optimization.
*   **Configuration-Driven Design:** Utilizes a YAML configuration file and environment variables for flexible customization of API keys, credentials, batch sizes, timeouts, and logging configurations, promoting adaptability across environments.
*   **Extensive Test Suite:** Includes a comprehensive suite of unit and integration tests to ensure code reliability, prevent regressions, and validate the functionality of individual components and the end-to-end pipeline.

## Getting Started

To deploy and run the Odoo CRM ETL Pipeline, follow these steps:

### Prerequisites

*   **Python 3.8 or Higher:** Ensure Python 3.8+ is installed on your system.
*   **AWS Account:** An active AWS account for utilizing AWS S3 storage.
*   **RapidAPI Account:** Access to a RapidAPI service providing lead data (specific API endpoint needs to be configured).
*   **Odoo 17.0+ Instance:** An operational Odoo 17.0 or later instance with the CRM module enabled and API access configured.
*   **Apache Airflow (Optional):** If scheduling and orchestration are required, Apache Airflow should be set up and configured.
*   **Prometheus and Grafana (Optional):** For performance monitoring and visualization, Prometheus and Grafana are recommended.

### Installation and Setup

1.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd odoo_etl_pipeline
    ```

2.  **Create a Virtual Environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration:**

    *   **Environment Variables:** Set the following environment variables in your shell environment or using a `.env` file. **Important:** Never hardcode sensitive credentials directly into the configuration file.

        ```bash
        export RAPIDAPI_API_KEY="YOUR_RAPIDAPI_KEY"
        export AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
        export AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
        export AWS_S3_BUCKET_NAME="your-s3-bucket-name"
        export ODOO_URL="http://your-odoo-instance.com" # or https://...
        export ODOO_DB_NAME="your_odoo_db_name"
        export ODOO_USERNAME="your_odoo_username"
        export ODOO_PASSWORD="your_odoo_password"
        # Optional variables for logging customization:
        # export LOG_LEVEL="INFO" # or DEBUG, WARNING, ERROR, CRITICAL
        # export LOG_FILE="odoo_etl_pipeline.log"
        ```

    *   **`config/config.yaml`:** Review and adjust the `config/config.yaml` file, replacing placeholder values with your specific configurations. Ensure that sensitive credentials remain as environment variable placeholders.

        ```yaml
        [rapidapi]
        api_key: "${RAPIDAPI_API_KEY}"
        base_url: "https://api.example-rapidapi.com"
        endpoint: "/leads"
        timeout: 10

        [aws]
        s3_bucket_name: "${AWS_S3_BUCKET_NAME}"
        region_name: "us-east-1"
        access_key_id: "${AWS_ACCESS_KEY_ID}"
        secret_access_key: "${AWS_SECRET_ACCESS_KEY}"

        [odoo]
        url: "${ODOO_URL}"
        db: "${ODOO_DB_NAME}"
        username: "${ODOO_USERNAME}"
        password: "${ODOO_PASSWORD}"
        lead_model: "crm.lead"
        xmlrpc_path: "/xmlrpc/2"

        [etl]
        transform_batch_size: 100
        odoo_batch_size: 20
        rapidapi_timeout: 10

        [retry]
        max_attempts: 3
        wait_seconds: 2
        ```

### Running Tests

It is highly recommended to execute the test suite before running the ETL pipeline to verify the integrity of the codebase and ensure proper functionality.

```bash
pytest tests/

Running the ETL Pipeline
Local Execution (for Development and Testing):

Execute the main pipeline script directly:

python src/etl/pipeline.py
Bash
Airflow Deployment (for Production Scheduling):

Copy dags/odoo_etl_dag.py to your Airflow DAGs directory.

Enable the odoo_rapidapi_etl DAG within the Airflow UI.

Trigger the DAG manually or wait for the scheduled execution.

Monitor DAG execution and task logs via the Airflow UI.

Performance Monitoring Setup
For comprehensive performance monitoring, integration with Prometheus and Grafana is recommended.

Install and Configure Prometheus: Set up a Prometheus server and configure it to scrape metrics from the ETL pipeline's /metrics endpoint (exposed on http://localhost:8000 when running src/etl/pipeline.py locally).

Install and Configure Grafana: Set up a Grafana instance and add Prometheus as a data source.

Create Grafana Dashboards: Design Grafana dashboards to visualize key metrics such as pipeline duration, stage timings, lead processing counts, and error rates.

Documentation
Refer to the code comments and inline documentation for detailed information on specific modules and functions. A comprehensive documentation set is under development.

Contributing
Contributions to enhance the ETL pipeline are welcome. Please fork the repository, create a feature branch, and submit a pull request with your proposed changes. Ensure that all new code is well-tested and documented.

License
MIT License
Contact: [Michael] - [michael.makram.zm@gmail.com]
