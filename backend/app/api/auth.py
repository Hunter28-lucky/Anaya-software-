from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import Profile
from app.schemas.api_models import ProfileCreate, ProfileOut

router = APIRouter()


@router.get("/me", response_model=ProfileOut)
async def get_current_user(db: AsyncSession = Depends(get_db)):
    """
    Returns default tenant/profile for session.
    Automatically provisions demo/admin user if none exists.
    """
    stmt = select(Profile).limit(1)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        profile = Profile(
            email="analyst@leadqualify.ai",
            full_name="Lead Analyst",
            role="admin"
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile
