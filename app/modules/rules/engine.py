from typing import Any

from app.modules.rules.types import RuleResult, RuleType


class RuleEngine:
    """Pure domain: evaluate rule + current progress + event -> new progress and completed flag."""

    @staticmethod
    def evaluate(
        rule_type: str,
        rule_params: dict[str, Any],
        current_progress: dict[str, Any],
        event_type: str,
        event_payload: dict[str, Any],
    ) -> RuleResult:
        if rule_type == RuleType.TRADE_COUNT:
            return RuleEngine._eval_trade_count(rule_params, current_progress, event_type, event_payload)
        if rule_type == RuleType.VOLUME:
            return RuleEngine._eval_volume(rule_params, current_progress, event_type, event_payload)
        if rule_type == RuleType.SIGNUP:
            return RuleEngine._eval_signup(rule_params, current_progress, event_type, event_payload)
        return RuleResult(new_progress=dict(current_progress), completed=False)

    @staticmethod
    def _eval_trade_count(
        params: dict[str, Any],
        current: dict[str, Any],
        event_type: str,
        payload: dict[str, Any],
    ) -> RuleResult:
        target = params.get("target", 0)
        count = current.get("trade_count", 0)
        if event_type == "trade":
            count += 1
        new_progress = {**current, "trade_count": count}
        return RuleResult(new_progress=new_progress, completed=count >= target)

    @staticmethod
    def _eval_volume(
        params: dict[str, Any],
        current: dict[str, Any],
        event_type: str,
        payload: dict[str, Any],
    ) -> RuleResult:
        target = params.get("target_usd", 0) or params.get("target", 0)
        volume = current.get("volume_usd", 0)
        if event_type == "trade" and "volume_usd" in payload:
            volume += float(payload["volume_usd"])
        elif event_type == "trade" and "amount" in payload:
            volume += float(payload.get("amount", 0))
        new_progress = {**current, "volume_usd": volume}
        return RuleResult(new_progress=new_progress, completed=volume >= target)

    @staticmethod
    def _eval_signup(
        params: dict[str, Any],
        current: dict[str, Any],
        event_type: str,
        payload: dict[str, Any],
    ) -> RuleResult:
        if event_type == "signup":
            return RuleResult(new_progress={**current, "signed_up": True}, completed=True)
        return RuleResult(new_progress=dict(current), completed=False)
