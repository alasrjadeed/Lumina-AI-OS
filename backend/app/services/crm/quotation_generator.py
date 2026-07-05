import logging
from typing import Any, Dict, List
from backend.app.services.crm.proposal_generator import ProposalGenerator
from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class QuotationGenerator:
    def __init__(self, ai: AIEngine):
        self.proposal_gen = ProposalGenerator(ai)

    async def create_quotation(self, client: str, items: List[Dict], tax: float = 0.0, discount: float = 0.0) -> Dict[str, Any]:
        return await self.proposal_gen.generate_quotation(client, items, tax, discount)
