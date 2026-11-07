from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Project, User
from app.schemas import ProjectCreateRequest, ProjectPublic, ProjectUpdateRequest

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectPublic])
def list_projects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.user_id == user.id)
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .limit(100)
        .all()
    )


@router.post("", response_model=ProjectPublic)
def create_project(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Project:
    project = Project(
        user_id=user.id,
        name=payload.name.strip(),
        description=(payload.description or "").strip(),
        project_type=(payload.project_type or "general").strip() or "general",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectPublic)
def update_project(
    project_id: int,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if payload.name is not None:
        project.name = payload.name.strip()
    if payload.description is not None:
        project.description = payload.description.strip()
    if payload.project_type is not None:
        project.project_type = (payload.project_type or "general").strip() or "general"

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    db.delete(project)
    db.commit()
