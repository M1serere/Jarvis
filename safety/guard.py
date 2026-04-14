from __future__ import annotations

from core.models import AssistantDecision


class SafetyGuard:
    def approve(self, decision: AssistantDecision) -> bool:
        return True