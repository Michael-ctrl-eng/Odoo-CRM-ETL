import asyncio
import xmlrpc.client
from src.utils.logger import logger
from src import config
from typing import List
from src.data_models.transformed_lead import TransformedLead
from src.exceptions import OdooAPIError, DataLoadError

class OdooClient:
    def __init__(self):
        self.url = str(config.odoo.url)
        self.db = config.odoo.db
        self.username = config.odoo.username
        self.password = config.odoo.password
        self.lead_model = config.odoo.lead_model
        self.xmlrpc_path = config.odoo.xmlrpc_path

        common = xmlrpc.client.ServerProxy('{}{}/common'.format(self.url, self.xmlrpc_path))
        try:
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            if self.uid:
                logger.info(f"Successfully authenticated to Odoo as user ID: {self.uid}")
            else:
                logger.error("Odoo Authentication failed: Invalid credentials.")
                raise OdooAPIError("Odoo Authentication failed: Invalid credentials.")
            self.models = xmlrpc.client.ServerProxy('{}{}/object'.format(self.url, self.xmlrpc_path))
        except Exception as e:
            logger.error(f"Error connecting to Odoo XML-RPC API: {e}")
            raise OdooAPIError(f"Error connecting to Odoo XML-RPC API: {e}")

        self.transform_batch_size = config.etl.transform_batch_size
        self.odoo_batch_size = config.etl.odoo_batch_size


    async def create_lead(self, lead_data: TransformedLead):
        """Creates a lead in Odoo CRM (using asyncio.to_thread for sync XML-RPC call)."""
        logger.info(f"Creating lead in Odoo (threaded): {lead_data.name}, Email: {lead_data.email}")
        odoo_data = {
            'name': lead_data.name,
            'email_from': lead_data.email,
            'phone': lead_data.phone,
            'partner_name': lead_data.partner_name,
            'description': lead_data.description,
            # ... map other fields to Odoo fields ...
        }
        try:
            loop = asyncio.get_running_loop()
            lead_id = await loop.run_in_executor(
                None,
                lambda: self.models.execute_kw(self.db, self.uid, self.password, self.lead_model, 'create', [odoo_data])
            )
            logger.info(f"Lead created in Odoo with ID: {lead_id}")
            return lead_id
        except xmlrpc.client.Fault as e:
            logger.error(f"Odoo API Fault (Create Lead): {e.faultCode} - {e.faultString}")
            raise OdooAPIError(e.faultString) from e
        except Exception as e:
            logger.error(f"Error creating lead in Odoo (threaded): {e}. Data: {lead_data}. Error: {e}")
            raise OdooAPIError(f"Error creating lead in Odoo: {e}")

    async def create_leads_batch(self, leads_data_batch: List[dict]) -> List[int]:
        """Creates a batch of leads in Odoo CRM (threaded XML-RPC batch)."""
        try:
            loop = asyncio.get_running_loop()
            lead_ids = await loop.run_in_executor(
                None,
                lambda: self.models.execute_kw(self.db, self.uid, self.password, self.lead_model, 'create', [leads_data_batch])
            )
            logger.info(f"Batch of {len(leads_data_batch)} leads submitted to Odoo for creation (threaded).")
            return lead_ids if isinstance(lead_ids, list) else []
        except xmlrpc.client.Fault as e:
            logger.error(f"Odoo API Fault (Batch Create Leads): {e.faultCode} - {e.faultString}")
            raise OdooAPIError(e.faultString) from e
        except Exception as e:
            logger.error(f"Error creating batch of leads in Odoo (threaded): {e}")
            raise OdooAPIError(f"Error creating batch of leads in Odoo: {e}")

    async def update_lead(self, lead_id: int, lead_data: TransformedLead):
        """Updates an existing lead in Odoo CRM (example)."""
        logger.info(f"Updating lead in Odoo ID: {lead_id} with data: {lead_data.name}, Email: {lead_data.email}")
        try:
            odoo_data = {
                'name': lead_data.name,
                'email_from': lead_data.email,
                # ... fields to update ...
            }
            loop = asyncio.get_running_loop()
            updated = await loop.run_in_executor(
                None,
                lambda: self.models.execute_kw(self.db, self.uid, self.password, self.lead_model, 'write', [[lead_id], odoo_data])
            )
            if updated:
                logger.info(f"Lead updated in Odoo with ID: {lead_id}")
            else:
                logger.warning(f"Failed to update lead in Odoo with ID: {lead_id}. Lead might not exist or no changes applied.")
            return updated
        except xmlrpc.client.Fault as e:
            logger.error(f"Odoo API Fault (Update Lead): {e.faultCode} - {e.faultString}")
            raise OdooAPIError(e.faultString) from e
        except Exception as e:
            logger.error(f"Error updating lead in Odoo: {e}")
            raise OdooAPIError(f"Error updating lead in Odoo: {e}")
