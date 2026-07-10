"""AI Content Writer — generates all types of content using the AI provider."""

from __future__ import annotations

from core.log import log
from core.provider import engine
from core.vault.store import vault

CONTENT_TYPES = {
    "blog": {
        "label": "Blog Post",
        "prompt": (
            "Write a professional blog post about {topic}. Include an engaging title,"
            " introduction, 3-5 main points with subheadings, and a conclusion"
            " with call-to-action. Tone: {tone}. Word count: ~500 words."
        ),
        "icon": "📝",
    },
    "product_description": {
        "label": "Product Description",
        "prompt": (
            "Write a compelling product description for: {topic}. Include features,"
            " benefits, specifications, and why customers should buy."
            " Tone: {tone}. Keep it concise but persuasive."
        ),
        "icon": "🏷️",
    },
    "meta_title": {
        "label": "Meta Title",
        "prompt": (
            "Generate 5 SEO-optimized meta titles (max 60 chars each) for: {topic}."
            " Include primary keyword naturally. Make them click-worthy."
        ),
        "icon": "🔖",
    },
    "meta_description": {
        "label": "Meta Description",
        "prompt": (
            "Generate 3 SEO meta descriptions (max 160 chars each) for: {topic}."
            " Include keywords, benefits, and a call-to-action."
        ),
        "icon": "📋",
    },
    "faq": {
        "label": "FAQ Section",
        "prompt": (
            "Create an FAQ section with 5-8 questions and answers about: {topic}."
            " Cover the most common questions customers ask. Tone: {tone}."
        ),
        "icon": "❓",
    },
    "landing_page": {
        "label": "Landing Page",
        "prompt": (
            "Write a complete landing page for: {topic}. Include: hero headline,"
            " subheadline, key benefits (3), features, social proof, pricing"
            " mention, and CTA. Tone: {tone}."
        ),
        "icon": "🖥️",
    },
    "email": {
        "label": "Email",
        "prompt": (
            "Write a professional email about: {topic}. Include subject line,"
            " greeting, body, and signature. Tone: {tone}. Keep it concise and actionable."
        ),
        "icon": "✉️",
    },
    "social_post": {
        "label": "Social Media Post",
        "prompt": (
            "Write a social media post about: {topic} for {platform}."
            " Include hashtags. Tone: {tone}. Keep it engaging and shareable."
        ),
        "icon": "📱",
    },
    "reply": {
        "label": "Reply",
        "prompt": "Write a reply to: {topic}. Tone: {tone}. Be helpful and professional.",
        "icon": "💬",
    },
    "whatsapp": {
        "label": "WhatsApp Message",
        "prompt": (
            "Write a WhatsApp business message about: {topic}. Keep it concise,"
            " friendly, and professional. Include a clear call-to-action if"
            " applicable. Tone: {tone}."
        ),
        "icon": "💬",
    },
    "quote": {
        "label": "Client Quote / Proposal",
        "prompt": (
            "Create a professional quote/proposal for a client about: {topic}."
            " Include: client greeting, project overview, pricing breakdown"
            " (itemize 3-5 services with prices), total amount, payment terms,"
            " validity period, and closing. Format professionally with clear sections."
            " Tone: {tone}."
        ),
        "icon": "💰",
    },
    "invoice": {
        "label": "Invoice",
        "prompt": (
            "Generate a professional invoice for: {topic}. Include: invoice number"
            " (INV-2024-001), date, client details, itemized services with rates"
            " and amounts, subtotal, tax (if applicable), total due, payment terms,"
            " and bank details placeholder. Tone: professional."
        ),
        "icon": "🧾",
    },
}


class ContentWriter:
    """AI-powered content writer for all content types."""

    def list_types(self) -> list[dict]:
        return [
            {"key": k, "label": v["label"], "icon": v["icon"]} for k, v in CONTENT_TYPES.items()
        ]

    def get_prompt(self, content_type: str) -> str | None:
        ct = CONTENT_TYPES.get(content_type)
        return ct["prompt"] if ct else None

    async def generate(
        self,
        content_type: str,
        topic: str,
        tone: str = "professional",
        platform: str = "Facebook",
        language: str = "English",
        use_vault: bool = True,
    ) -> dict:
        """Generate content using the AI provider chain."""
        ct = CONTENT_TYPES.get(content_type)
        if not ct:
            return {"error": f"Unknown content type: {content_type}"}

        prompt = ct["prompt"].format(topic=topic, tone=tone, platform=platform)

        if use_vault:
            vault_data = vault.to_context_prompt()
            if vault_data:
                prompt += f"\n\nUse this available information where relevant:\n{vault_data}"

        prompt += f"\n\nWrite in: {language}"

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an expert {content_type.replace('_', ' ')} writer."
                    " Generate high-quality, original content."
                    " Format with proper structure."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        try:
            resp = await engine.chat(messages)
            text = resp.get("message", {}).get("content", "")
            return {"content": text, "type": content_type, "topic": topic, "tone": tone}
        except Exception as e:
            log.error("ContentWriter: Generation failed: %s", e)
            return {"error": str(e)}

    async def generate_blog(self, topic: str, tone: str = "professional") -> dict:
        return await self.generate("blog", topic, tone)

    async def generate_product_desc(self, topic: str, tone: str = "professional") -> dict:
        return await self.generate("product_description", topic, tone)

    async def generate_meta_title(self, topic: str) -> dict:
        return await self.generate("meta_title", topic, "professional")

    async def generate_meta_desc(self, topic: str) -> dict:
        return await self.generate("meta_description", topic, "professional")

    async def generate_faq(self, topic: str, tone: str = "helpful") -> dict:
        return await self.generate("faq", topic, tone)

    async def generate_landing_page(self, topic: str, tone: str = "persuasive") -> dict:
        return await self.generate("landing_page", topic, tone)

    async def generate_email(self, topic: str, tone: str = "professional") -> dict:
        return await self.generate("email", topic, tone)

    async def generate_social_post(
        self, topic: str, platform: str = "Facebook", tone: str = "engaging"
    ) -> dict:
        return await self.generate("social_post", topic, tone, platform=platform)

    async def generate_reply(self, topic: str, tone: str = "helpful") -> dict:
        return await self.generate("reply", topic, tone)

    async def generate_whatsapp(self, topic: str, tone: str = "friendly") -> dict:
        return await self.generate("whatsapp", topic, tone)

    async def generate_quote(self, topic: str, tone: str = "professional") -> dict:
        return await self.generate("quote", topic, tone)

    async def generate_invoice(self, topic: str) -> dict:
        return await self.generate("invoice", topic, "professional")


writer = ContentWriter()
