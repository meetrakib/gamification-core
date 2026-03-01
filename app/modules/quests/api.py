from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.quests.schemas import QuestCreate, QuestRead, QuestUpdate
from app.modules.quests.service import QuestService

router = APIRouter(prefix="/quests", tags=["quests"])


@router.get("", response_model=list[QuestRead])
async def list_quests(
    quest_type: str | None = Query(None, description="Filter by quest_type"),
    db: AsyncSession = Depends(get_db),
) -> list[QuestRead]:
    service = QuestService(db)
    quests = await service.list_active(quest_type=quest_type)
    return [QuestRead.model_validate(q) for q in quests]


@router.get("/{quest_id}", response_model=QuestRead)
async def get_quest(
    quest_id: int,
    db: AsyncSession = Depends(get_db),
) -> QuestRead:
    service = QuestService(db)
    quest = await service.get_by_id(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    return QuestRead.model_validate(quest)


@router.post("", response_model=QuestRead, status_code=201)
async def create_quest(
    data: QuestCreate,
    db: AsyncSession = Depends(get_db),
) -> QuestRead:
    service = QuestService(db)
    existing = await service.get_by_slug(data.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Quest slug already exists")
    quest = await service.create(data)
    return QuestRead.model_validate(quest)


@router.patch("/{quest_id}", response_model=QuestRead)
async def update_quest(
    quest_id: int,
    data: QuestUpdate,
    db: AsyncSession = Depends(get_db),
) -> QuestRead:
    service = QuestService(db)
    quest = await service.get_by_id(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    quest = await service.update(quest, data)
    return QuestRead.model_validate(quest)
