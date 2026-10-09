from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.entities import Project, ProjectRule, Profile, ProjectRecord, ImportBatch
from app.schemas.api_models import ProjectCreate, ProjectUpdate, ProjectOut, ProjectRuleCreate, ProjectRuleOut

router = APIRouter()


async def get_or_create_default_tenant(db: AsyncSession) -> Profile:
    stmt = select(Profile).limit(1)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        profile = Profile(email="analyst@leadqualify.ai", full_name="Lead Analyst", role="admin")
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.get("", response_model=List[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    stmt = select(Project).options(selectinload(Project.rules)).order_by(Project.created_at.desc())
    res = await db.execute(stmt)
    projects = res.scalars().all()

    out = []
    for p in projects:
        # Count records
        rec_count = await db.scalar(select(func.count(ProjectRecord.id)).where(ProjectRecord.project_id == p.id)) or 0
        batch_count = await db.scalar(select(func.count(ImportBatch.id)).where(ImportBatch.project_id == p.id)) or 0
        p_dict = ProjectOut(
            id=p.id,
            tenant_id=p.tenant_id,
            name=p.name,
            target_industry=p.target_industry,
            description=p.description,
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at,
            rules=ProjectRuleOut.model_validate(p.rules) if p.rules else None,
            total_records=rec_count,
            total_batches=batch_count,
        )
        out.append(p_dict)
    return out


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    tenant = await get_or_create_default_tenant(db)

    project = Project(
        tenant_id=tenant.id,
        name=payload.name,
        target_industry=payload.target_industry,
        description=payload.description,
    )
    db.add(project)
    await db.flush()

    # Create rules
    rule_data = payload.rules
    if not rule_data:
        # Default Medical Tourism rules
        rule_data = ProjectRuleCreate(
            industry_definition="Medical tourism facilitators, international patient coordinators, and cross-border healthcare travel agencies.",
            inclusion_criteria=[
                "Arranges cross-border medical treatments or healthcare travel",
                "Facilitates international patient intake, hospital coordination, and travel logistics",
                "Offers bundled medical packages with accredited overseas hospitals"
            ],
            exclusion_criteria=[
                "General travel agencies with no healthcare services",
                "Hospitals without dedicated international patient programs",
                "Websites that only mention medical tourism in blog articles or news"
            ],
            positive_examples=[
                {"company": "Global Medical Care", "reason": "Full international patient coordination and surgery packages"},
                {"company": "HealthTravel Connect", "reason": "Accredited dental and orthopedic travel facilitator"}
            ],
            negative_examples=[
                {"company": "Wanderlust Holidays", "reason": "General leisure vacation booking agency with no medical partnerships"},
                {"company": "Health News Weekly", "reason": "Editorial publisher that wrote an article about overseas clinics"}
            ],
            confidence_threshold=0.70
        )

    rule = ProjectRule(
        project_id=project.id,
        industry_definition=rule_data.industry_definition,
        inclusion_criteria=rule_data.inclusion_criteria,
        exclusion_criteria=rule_data.exclusion_criteria,
        positive_examples=rule_data.positive_examples,
        negative_examples=rule_data.negative_examples,
        confidence_threshold=rule_data.confidence_threshold,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(project)
    await db.refresh(rule)

    return ProjectOut(
        id=project.id,
        tenant_id=project.tenant_id,
        name=project.name,
        target_industry=project.target_industry,
        description=project.description,
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at,
        rules=ProjectRuleOut.model_validate(rule),
        total_records=0,
        total_batches=0,
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Project)
        .options(selectinload(Project.rules))
        .where(Project.id == project_id)
    )
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rec_count = await db.scalar(select(func.count(ProjectRecord.id)).where(ProjectRecord.project_id == project.id)) or 0
    batch_count = await db.scalar(select(func.count(ImportBatch.id)).where(ImportBatch.project_id == project.id)) or 0

    return ProjectOut(
        id=project.id,
        tenant_id=project.tenant_id,
        name=project.name,
        target_industry=project.target_industry,
        description=project.description,
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at,
        rules=ProjectRuleOut.model_validate(project.rules) if project.rules else None,
        total_records=rec_count,
        total_batches=batch_count,
    )


@router.put("/{project_id}/rules", response_model=ProjectRuleOut)
async def update_project_rules(
    project_id: str,
    payload: ProjectRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ProjectRule).where(ProjectRule.project_id == project_id)
    res = await db.execute(stmt)
    rule = res.scalar_one_or_none()
    if not rule:
        rule = ProjectRule(project_id=project_id, **payload.model_dump())
        db.add(rule)
    else:
        rule.industry_definition = payload.industry_definition
        rule.inclusion_criteria = payload.inclusion_criteria
        rule.exclusion_criteria = payload.exclusion_criteria
        rule.positive_examples = payload.positive_examples
        rule.negative_examples = payload.negative_examples
        rule.confidence_threshold = payload.confidence_threshold

    await db.commit()
    await db.refresh(rule)
    return ProjectRuleOut.model_validate(rule)


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted successfully"}
