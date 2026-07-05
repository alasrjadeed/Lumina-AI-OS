from backend.app.services.crm.lead_manager import LeadManager
from backend.app.services.crm.sales_pipeline import SalesPipeline
from backend.app.services.crm.proposal_generator import ProposalGenerator
from backend.app.services.crm.quotation_generator import QuotationGenerator
from backend.app.services.crm.followup_manager import FollowUpManager
from backend.app.services.crm.calendar_service import CalendarService
from backend.app.services.crm.client_workspace import ClientWorkspace

__all__ = ["LeadManager", "SalesPipeline", "ProposalGenerator", "QuotationGenerator", "FollowUpManager", "CalendarService", "ClientWorkspace"]
