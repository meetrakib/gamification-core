from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.progress.schemas import UserProgressRead
from app.modules.progress.service import ProgressService

router = APIRouter(prefix="/users/{user_id}/progress", tags=["progress"])


@router.get("", response_model=list[UserProgressRead])
async def get_user_progress(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[UserProgressRead]:
    service = ProgressService(db)
    items = await service.get_for_user(user_id)
    return [UserProgressRead.model_validate(p) for p in items]


@router.post("/{quest_id}/claim", response_model=UserProgressRead)
async def claim_reward(
    user_id: str,
    quest_id: int,
    db: AsyncSession = Depends(get_db),
) -> UserProgressRead:
    service = ProgressService(db)
    progress = await service.claim_reward(user_id, quest_id)
    if not progress:
        raise HTTPException(
            status_code=400,
            detail="Progress not found or quest not completed (cannot claim)",
        )
    return UserProgressRead.model_validate(progress)
