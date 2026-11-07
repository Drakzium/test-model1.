from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import MemoryEntry, User
from app.schemas import MemoryEntryCreateRequest, MemoryEntryPublic, MemoryEntryUpdateRequest

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("", response_model=list[MemoryEntryPublic])
def list_memory_entries(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[MemoryEntry]:
    return (
        db.query(MemoryEntry)
        .filter(MemoryEntry.user_id == user.id)
        .order_by(MemoryEntry.updated_at.desc(), MemoryEntry.id.desc())
        .limit(200)
        .all()
    )


@router.post("", response_model=MemoryEntryPublic)
def create_memory_entry(
    payload: MemoryEntryCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MemoryEntry:
    memory = MemoryEntry(
        user_id=user.id,
        title=payload.title.strip(),
        content=(payload.content or "").strip(),
        category=(payload.category or "general").strip() or "general",
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


@router.patch("/{memory_id}", response_model=MemoryEntryPublic)
def update_memory_entry(
    memory_id: int,
    payload: MemoryEntryUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MemoryEntry:
    memory = (
        db.query(MemoryEntry)
        .filter(MemoryEntry.id == memory_id, MemoryEntry.user_id == user.id)
        .first()
    )
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")

    if payload.title is not None:
        memory.title = payload.title.strip()
    if payload.content is not None:
        memory.content = payload.content.strip()
    if payload.category is not None:
        memory.category = (payload.category or "general").strip() or "general"

    db.commit()
    db.refresh(memory)
    return memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory_entry(
    memory_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    memory = (
        db.query(MemoryEntry)
        .filter(MemoryEntry.id == memory_id, MemoryEntry.user_id == user.id)
        .first()
    )
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
    db.delete(memory)
    db.commit()
