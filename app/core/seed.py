from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.modules.quests.models import Quest
from app.modules.quests.schemas import QuestCreate
from app.modules.quests.service import QuestService


async def seed_if_empty() -> None:
    """Create a sample quest if no quests exist (dev only)."""
    async with async_session_maker() as db:
        result = await db.execute(select(Quest).limit(1))
        if result.scalar_one_or_none() is not None:
            return
        service = QuestService(db)
        await service.create(
            QuestCreate(
                slug="first-5-trades",
                name="Complete 5 Trades",
                description="Make 5 trades to complete this quest.",
                quest_type="repeated",
                rules={"type": "trade_count", "target": 5},
                reward={"type": "points", "amount": 100},
                is_active=True,
            )
        )
        await db.commit()
