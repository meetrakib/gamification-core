from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quests.models import Quest
from app.modules.quests.schemas import QuestCreate, QuestUpdate


class QuestService:
    """Public interface for quests module. Other modules must use this only."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, quest_id: int) -> Quest | None:
        result = await self._db.execute(select(Quest).where(Quest.id == quest_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Quest | None:
        result = await self._db.execute(select(Quest).where(Quest.slug == slug))
        return result.scalar_one_or_none()

    async def list_active(
        self,
        quest_type: str | None = None,
        at_time: datetime | None = None,
    ) -> list[Quest]:
        q = select(Quest).where(Quest.is_active == True)
        if quest_type:
            q = q.where(Quest.quest_type == quest_type)
        if at_time is not None:
            if Quest.schedule_start is not None:
                q = q.where(Quest.schedule_start <= at_time)
            if Quest.schedule_end is not None:
                q = q.where(Quest.schedule_end >= at_time)
        q = q.order_by(Quest.id)
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def create(self, data: QuestCreate) -> Quest:
        quest = Quest(
            slug=data.slug,
            name=data.name,
            description=data.description,
            quest_type=data.quest_type,
            rules=data.rules,
            reward=data.reward,
            schedule_start=data.schedule_start,
            schedule_end=data.schedule_end,
            is_active=data.is_active,
        )
        self._db.add(quest)
        await self._db.flush()
        await self._db.refresh(quest)
        return quest

    async def update(self, quest: Quest, data: QuestUpdate) -> Quest:
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(quest, k, v)
        await self._db.flush()
        await self._db.refresh(quest)
        return quest
