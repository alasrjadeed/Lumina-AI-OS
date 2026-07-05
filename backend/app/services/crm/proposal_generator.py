import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class ProposalGenerator:
    def __init__(self, ai: AIEngine):
        self.ai = ai

    async def generate(self, client_name: str, scope: str, pricing: str, timeline: str) -> Dict[str, Any]:
        prompt = f"""Create a professional business proposal.

Client: {client_name}
Scope of Work: {scope}
Pricing: {pricing}
Timeline: {timeline}

Include: executive summary, scope, deliverables, pricing table, timeline, terms & conditions."""
        content = await self.ai.generate(prompt=prompt, system="You are a professional proposal writer. Generate a complete, polished business proposal.")
        return {
            "client": client_name,
            "content": content,
            "scope": scope,
            "pricing": pricing,
            "timeline": timeline,
        }

    async def generate_quotation(self, client_name: str, items: List[Dict], tax: float = 0.0, discount: float = 0.0) -> Dict[str, Any]:
        lines = []
        subtotal = 0
        for item in items:
            qty = item.get("qty", 1)
            price = item.get("price", 0)
            total = qty * price
            subtotal += total
            lines.append(f"{item.get('description', 'Item')} x{qty} @ ${price:.2f} = ${total:.2f}")
        tax_amount = subtotal * tax
        discount_amount = subtotal * discount
        grand_total = subtotal + tax_amount - discount_amount
        content = f"""QUOTATION for {client_name}

{'─' * 40}
{chr(10).join(lines)}
{'─' * 40}
Subtotal: ${subtotal:.2f}
Tax ({(tax*100):.0f}%): ${tax_amount:.2f}
Discount ({(discount*100):.0f}%): -${discount_amount:.2f}
{'─' * 40}
TOTAL: ${grand_total:.2f}
{'─' * 40}

Terms: Payment due within 30 days.
Validity: This quotation is valid for 14 days."""
        return {
            "client": client_name,
            "content": content,
            "items": items,
            "subtotal": subtotal,
            "tax": tax_amount,
            "discount": discount_amount,
            "grand_total": grand_total,
        }
