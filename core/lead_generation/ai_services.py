from __future__ import annotations

import re
from typing import Any

from core.log import log
from core.provider import engine as ai_engine

from .models import LeadRecord


class LeadScoringService:
    def __init__(self, cloudflare_account_id: str = "", cloudflare_api_token: str = ""):
        self._cf_account_id = cloudflare_account_id
        self._cf_api_token = cloudflare_api_token

    async def score_lead(self, lead: LeadRecord) -> int:
        scoring_input = self._build_scoring_input(lead)
        try:
            prompt = f"""You are a B2B lead scoring AI. Score this lead 0-100 based on:
- Data completeness (0-30): does it have email, phone, website, social links?
- Engagement signals (0-25): followers count, reviews count, activity level
- Business relevance (0-25): how likely is this business to need services?
- Recency (0-20): is the data fresh?

Lead data:
{scoring_input}

Return ONLY the integer score (0-100). No explanation."""
            result = await ai_engine.chat([
                {"role": "system", "content": "You are a lead scoring AI. Output only a number from 0 to 100."},
                {"role": "user", "content": prompt},
            ])
            content = result.get("message", {}).get("content", "0")
            score = int(re.search(r"\d+", content).group(0)) if re.search(r"\d+", content) else 0
            return max(0, min(100, score))
        except Exception as e:
            log.warning("AI scoring failed: %s, using heuristic fallback", e)
            return self._heuristic_score(lead)

    async def batch_score(self, leads: list[LeadRecord]) -> dict[str, Any]:
        scored = 0
        failed = 0
        for lead in leads:
            try:
                lead.lead_score = await self.score_lead(lead)
                scored += 1
            except Exception:
                failed += 1
        return {"scored": scored, "failed": failed}

    def _build_scoring_input(self, lead: LeadRecord) -> str:
        parts = [f"Business: {lead.business_name}"]
        if lead.email:
            parts.append(f"Email: {lead.email}")
        if lead.phone:
            parts.append(f"Phone: {lead.phone}")
        if lead.website:
            parts.append(f"Website: {lead.website}")
        if lead.source:
            parts.append(f"Source: {lead.source}")
        if lead.category:
            parts.append(f"Category: {lead.category}")
        if lead.description:
            parts.append(f"Description: {lead.description[:200]}")
        if lead.followers_count:
            parts.append(f"Followers: {lead.followers_count}")
        if lead.reviews_count:
            parts.append(f"Reviews: {lead.reviews_count}")
        if lead.rating:
            parts.append(f"Rating: {lead.rating}")
        if lead.social_links:
            parts.append(f"Social: {', '.join(lead.social_links.keys())}")
        return "\n".join(parts)

    def _heuristic_score(self, lead: LeadRecord) -> int:
        score = 0
        if lead.email:
            score += 20
        if lead.phone:
            score += 15
        if lead.website:
            score += 25
        if lead.social_links:
            score += 10
        if lead.followers_count and lead.followers_count > 100:
            score += 10
        if lead.reviews_count and lead.reviews_count > 5:
            score += 10
        if lead.rating and lead.rating >= 4.0:
            score += 10
        return min(score, 100)


class OutreachService:
    def __init__(self):
        pass

    async def generate_email(self, lead: LeadRecord, language: str = "en") -> str:
        try:
            prompt_lang = "Arabic" if language == "ar" else "English"
            prompt = f"""Write a professional {prompt_lang} cold outreach email for this business:

Business Name: {lead.business_name}
Industry: {lead.category}
Location: {lead.country}, {lead.city}
Website: {lead.website or 'N/A'}
Description: {lead.description or 'N/A'}

The email should:
- Be personalized with the business name
- Introduce our AI automation services (Lumina AI OS)
- Mention specific value for their industry
- Include a clear call to action
- Be 3-4 short paragraphs
- Sound professional but warm

For Arabic emails, use formal Arabic and include common Arabic business greetings."""
            result = await ai_engine.chat([
                {"role": "system", "content": "You are a B2B sales copywriter. Write compelling outreach emails."},
                {"role": "user", "content": prompt},
            ])
            return result.get("message", {}).get("content", "")
        except Exception as e:
            log.warning("AI email generation failed: %s", e)
            return self._fallback_email(lead)

    async def generate_whatsapp(self, lead: LeadRecord, language: str = "en") -> str:
        try:
            prompt_lang = "Arabic" if language == "ar" else "English"
            prompt = f"""Write a short, friendly WhatsApp outreach message in {prompt_lang} for:

Business: {lead.business_name}
Industry: {lead.category}
Contact: {lead.contact_person or lead.business_name}

Requirements:
- Keep it under 3 sentences
- Sound personal and conversational (not corporate)
- Mention a specific value proposition
- Include a friendly call to action
- Use emojis naturally (1-2 max)

For Arabic messages, use Levantine/Gulf dialect style."""
            result = await ai_engine.chat([
                {"role": "system", "content": "You write engaging WhatsApp business messages. Keep them short and personal."},
                {"role": "user", "content": prompt},
            ])
            return result.get("message", {}).get("content", "")
        except Exception as e:
            log.warning("AI WhatsApp generation failed: %s", e)
            return self._fallback_whatsapp(lead)

    @staticmethod
    def _fallback_email(lead: LeadRecord) -> str:
        return f"""Subject: Streamlining {lead.business_name}'s Growth with AI Automation

Dear {lead.contact_person or 'Team at ' + lead.business_name},

I hope this message finds you well. I came across {lead.business_name} and was impressed by your presence in the {lead.country} market.

At Lumina AI, we help businesses like yours automate lead generation, customer outreach, and marketing workflows using AI — saving hours of manual work while increasing conversion rates.

Would you be open to a brief 15-minute call this week to explore how we might support your growth?

Looking forward to hearing from you.

Best regards,
Lumina AI Team"""

    @staticmethod
    def _fallback_whatsapp(lead: LeadRecord) -> str:
        return f"Hi {lead.contact_person or 'there'}! 👋 I noticed {lead.business_name} online and thought you might be interested in our AI automation tools that help businesses like yours find more leads and streamline outreach. Would love to chat if you're interested! 🚀"
