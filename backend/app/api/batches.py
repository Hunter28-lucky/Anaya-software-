from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import ImportBatch
from app.schemas.api_models import BatchOut
from app.services.batch_runner import BatchExecutionRunner

router = APIRouter()


@router.get("", response_model=List[BatchOut])
async def list_batches(project_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(ImportBatch).order_by(ImportBatch.created_at.desc())
    if project_id:
        stmt = stmt.where(ImportBatch.project_id == project_id)
    res = await db.execute(stmt)
    batches = res.scalars().all()
    return [BatchOut.model_validate(b) for b in batches]


@router.get("/{batch_id}", response_model=BatchOut)
async def get_batch(batch_id: str, db: AsyncSession = Depends(get_db)):
    batch = await db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchOut.model_validate(batch)


@router.post("/{batch_id}/pause", response_model=BatchOut)
async def pause_batch(batch_id: str, db: AsyncSession = Depends(get_db)):
    batch = await db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status == "PROCESSING":
        batch.status = "PAUSED"
        await db.commit()
        await db.refresh(batch)
    return BatchOut.model_validate(batch)


@router.post("/{batch_id}/resume", response_model=BatchOut)
async def resume_batch(
    batch_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    batch = await db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status in ("PAUSED", "QUEUED"):
        batch.status = "PROCESSING"
        await db.commit()
        await db.refresh(batch)
        background_tasks.add_task(BatchExecutionRunner.process_batch, batch.id)
    return BatchOut.model_validate(batch)


@router.post("/{batch_id}/cancel", response_model=BatchOut)
async def cancel_batch(batch_id: str, db: AsyncSession = Depends(get_db)):
    batch = await db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    batch.status = "CANCELLED"
    await db.commit()
    await db.refresh(batch)
    return BatchOut.model_validate(batch)
