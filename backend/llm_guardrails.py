"""
OWASP LLM Top 10 aligned guardrails for this chatbot.

This module focuses on practical runtime controls for a banking assistant:
- Block high-risk prompt injection and system prompt extraction attempts
- Block requests that imply unsupported autonomous actions
- Detect unbounded-consumption style abuse patterns
"""

from dataclasses import dataclass
from typing import List, Pattern, Tuple
import re


@dataclass
class GuardrailDecision:
    """Decision returned by the guardrail engine."""

    allowed: bool
    risks: List[str]
    reason: str = ""


class LLMGuardrails:
    """Simple deterministic checks mapped to OWASP LLM Top 10 categories."""

    MAX_SAFE_MESSAGE_LENGTH = 1200

    _PROMPT_INJECTION_PATTERNS: Tuple[Pattern[str], ...] = tuple(
        re.compile(pattern, flags=re.IGNORECASE)
        for pattern in (
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"override\s+(your\s+)?instructions",
            r"jailbreak",
            r"developer\s+mode",
            r"do\s+anything\s+now",
            r"pretend\s+to\s+be",
            r"act\s+as\s+(a\s+)?system"
        )
    )

    _PROMPT_LEAKAGE_PATTERNS: Tuple[Pattern[str], ...] = tuple(
        re.compile(pattern, flags=re.IGNORECASE)
        for pattern in (
            r"reveal\s+(the\s+)?system\s+prompt",
            r"show\s+(me\s+)?(your\s+)?hidden\s+instructions",
            r"print\s+your\s+prompt",
            r"what\s+are\s+your\s+internal\s+rules"
        )
    )

    _EXCESSIVE_AGENCY_PATTERNS: Tuple[Pattern[str], ...] = tuple(
        re.compile(pattern, flags=re.IGNORECASE)
        for pattern in (
            r"transfer\s+money",
            r"wire\s+funds",
            r"execute\s+(a\s+)?transaction",
            r"change\s+my\s+password",
            r"delete\s+my\s+account",
            r"run\s+(a\s+)?command",
            r"call\s+(an\s+)?api"
        )
    )

    _UNBOUNDED_CONSUMPTION_PATTERNS: Tuple[Pattern[str], ...] = tuple(
        re.compile(pattern, flags=re.IGNORECASE)
        for pattern in (
            r"repeat\s+forever",
            r"infinite\s+loop",
            r"generate\s+\d{4,}\s+",
            r"output\s+\d{4,}\s+"
        )
    )

    @staticmethod
    def _matches_any(text: str, patterns: Tuple[Pattern[str], ...]) -> bool:
        return any(pattern.search(text) for pattern in patterns)

    def evaluate_user_message(self, message: str) -> GuardrailDecision:
        """Evaluate incoming user text against OWASP LLM Top 10 risks."""
        normalized = (message or "").strip()

        if not normalized:
            return GuardrailDecision(allowed=False, risks=["LLM10:2025"], reason="Empty message")

        risks: List[str] = []

        if len(normalized) > self.MAX_SAFE_MESSAGE_LENGTH:
            risks.append("LLM10:2025")

        if self._matches_any(normalized, self._PROMPT_INJECTION_PATTERNS):
            risks.append("LLM01:2025")

        if self._matches_any(normalized, self._PROMPT_LEAKAGE_PATTERNS):
            risks.append("LLM07:2025")

        if self._matches_any(normalized, self._EXCESSIVE_AGENCY_PATTERNS):
            risks.append("LLM06:2025")

        if self._matches_any(normalized, self._UNBOUNDED_CONSUMPTION_PATTERNS):
            risks.append("LLM10:2025")

        if risks:
            unique_risks = sorted(set(risks))
            return GuardrailDecision(
                allowed=False,
                risks=unique_risks,
                reason="Input matched blocked LLM risk patterns"
            )

        return GuardrailDecision(allowed=True, risks=[])
