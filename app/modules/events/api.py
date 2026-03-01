from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.events.schemas import EventIn, EventOut
from app.modules.progress.service import ProgressService

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut)
async def post_event(
    data: EventIn,
    db: AsyncSession = Depends(get_db),
) -> EventOut:
    service = ProgressService(db)
    updated = await service.record_event(
        user_id=data.user_id,
        event_type=data.event_type,
        event_payload=data.payload,
    )
    return EventOut(accepted=True, updated_progress_count=len(updated))
