from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quests.service import QuestService
from app.modules.progress.models import UserProgress
from app.modules.rules.engine import RuleEngine


class ProgressService:
    """Public interface for progress module. record_event delegates to RuleEngine."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._quest_svc = QuestService(db)

    async def get_or_create(self, user_id: str, quest_id: int) -> UserProgress:
        result = await self._db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.quest_id == quest_id,
            )
        )
        progress = result.scalar_one_or_none()
        if progress:
            return progress
        progress = UserProgress(user_id=user_id, quest_id=quest_id, state="not_started")
        self._db.add(progress)
        await self._db.flush()
        await self._db.refresh(progress)
        return progress

    async def get_for_user(self, user_id: str) -> list[UserProgress]:
        result = await self._db.execute(
            select(UserProgress).where(UserProgress.user_id == user_id).order_by(UserProgress.id)
        )
        return list(result.scalars().all())

    async def get_by_user_and_quest(self, user_id: str, quest_id: int) -> UserProgress | None:
        result = await self._db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.quest_id == quest_id,
            )
        )
        return result.scalar_one_or_none()

    async def record_event(
        self,
        user_id: str,
        event_type: str,
        event_payload: dict,
    ) -> list[UserProgress]:
        """Process event for user: load active quests, evaluate rules, update progress. Returns updated progress list."""
        now = datetime.now(timezone.utc)
        quests = await self._quest_svc.list_active(at_time=now)
        updated: list[UserProgress] = []
        for quest in quests:
            rules = quest.rules or {}
            if not isinstance(rules, dict):
                continue
            rule_type = rules.get("type")
            rule_params = {k: v for k, v in rules.items() if k != "type"}
            if not rule_type:
                continue
            progress = await self.get_or_create(user_id, quest.id)
            if progress.state in ("completed", "reward_claimed"):
                continue
            result = RuleEngine.evaluate(
                rule_type=rule_type,
                rule_params=rule_params if isinstance(rule_params, dict) else {},
                current_progress=progress.progress_payload or {},
                event_type=event_type,
                event_payload=event_payload or {},
            )
            progress.progress_payload = result.new_progress
            if result.completed:
                progress.state = "completed"
                progress.completed_at = now
            else:
                progress.state = "in_progress"
            await self._db.flush()
            updated.append(progress)
        return updated

    async def claim_reward(self, user_id: str, quest_id: int) -> UserProgress | None:
        progress = await self.get_by_user_and_quest(user_id, quest_id)
        if not progress or progress.state != "completed":
            return None
        progress.state = "reward_claimed"
        progress.reward_claimed_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(progress)
        return progress
