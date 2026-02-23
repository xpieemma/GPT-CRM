from groq import AsyncGroq
from typing import Optional, Dict
import json

from app.models import ConversationContext, AgentResponse
from app.config import settings
from app.utils.logging import agent_logger
from app.services.prompt_store import prompt_store
from app.services.audit import audit
from app.services.metrics import metrics


class OutreachAgent:
    """AI Outreach Agent powered by Groq (free, fast, Llama 3)"""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def generate_response(
        self,
        context: ConversationContext,
        user_message: Optional[str] = None,
        tenant_id: str = "default"
    ) -> AgentResponse:
        """Generate response with budget enforcement and audit trail"""

        # 1. Enforce budget before API call
        audit.enforce_budget(tenant_id)

        # 2. Get tenant prompt
        prompt_data = prompt_store.get_active_prompt(tenant_id)
        system_prompt = prompt_data['content'] if prompt_data else self._get_default_prompt()

        # 3. Build messages
        # Groq uses the same OpenAI-compatible chat completions interface.
        # JSON mode is supported on Llama 3 models via response_format.
        messages = [
            {"role": "system", "content": system_prompt + "\n\nAlways respond with valid JSON only."},
            {"role": "user", "content": self._prepare_context(context)}
        ]
        if user_message:
            messages.append({"role": "user", "content": user_message})

        try:
            # 4. Call Groq
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            # 5. Parse response
            raw_content = response.choices[0].message.content
            try:
                result = json.loads(raw_content)
                agent_response = AgentResponse(**result)
            except (json.JSONDecodeError, Exception) as e:
                agent_logger.error(f"Parse failed: {e}")
                agent_response = self._get_fallback_response()

            # 6. Track token usage
            # Groq is free but we still track tokens for observability
            token_count = response.usage.total_tokens if response.usage else 0
            metrics.put_metric("TokensUsed", token_count, tenant_id)
            metrics.put_metric("TokenCost", 0.0, tenant_id)  # Free!

            # 7. Audit trail
            audit.log_interaction(
                tenant_id=tenant_id,
                lead_id=context.lead.id,
                prompt_version=prompt_data['version'] if prompt_data else "default",
                model=self.model,
                context=context.dict(),
                response=agent_response.dict(),
                cost=0.0
            )

            return agent_response

        except Exception as e:
            agent_logger.error(f"Generation failed: {e}")
            metrics.increment("GenerationFailures", tenant_id)
            raise

    def _prepare_context(self, context: ConversationContext) -> str:
        """Prepare lead context for prompt"""
        lead = context.lead
        return (
            f"Lead: {lead.first_name} {lead.last_name}\n"
            f"Company: {lead.company}\n"
            f"Position: {lead.position}\n"
            f"Status: {lead.status}\n"
            f"Stage: {context.current_stage}\n"
        )

    def _get_default_prompt(self) -> str:
        """Default system prompt"""
        return (
            "You are a CRM outreach agent. Generate professional, personalised responses.\n"
            "Return JSON with these exact keys: message, suggested_action, confidence_score, requires_human"
        )

    def _get_fallback_response(self) -> AgentResponse:
        """Safe fallback when JSON parsing fails"""
        return AgentResponse(
            message="I'll need to have a team member follow up.",
            suggested_action="escalate",
            confidence_score=0.0,
            requires_human=True,
            metadata={"error": "parse_failed"}
        )


# Singleton
outreach_agent = OutreachAgent()
