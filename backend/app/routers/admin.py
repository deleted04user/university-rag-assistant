from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth_utils import require_admin
from app.database import get_db
from app.models import ChatMessage, User
from app.schemas import AdminUserUpdate, StatsSummary, UserOut
from app.services import rag_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.id).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id and data.is_active is False:
        raise HTTPException(status_code=400, detail="Impossible de se désactiver soi-même")
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return u


@router.get("/stats/chat", response_model=StatsSummary)
def chat_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    total = db.query(func.count(ChatMessage.id)).scalar() or 0
    rows = (
        db.query(ChatMessage.intent, func.count(ChatMessage.id))
        .filter(ChatMessage.role == "assistant")
        .group_by(ChatMessage.intent)
        .all()
    )
    by_intent = {r[0] or "unknown": r[1] for r in rows}
    since = datetime.utcnow() - timedelta(days=7)
    last7 = (
        db.query(func.count(ChatMessage.id))
        .filter(ChatMessage.created_at >= since)
        .scalar()
        or 0
    )
    return StatsSummary(
        total_messages=total, by_intent=by_intent, last_7_days=last7
    )


@router.post("/rag/reindex")
def rag_reindex(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Reconstruit l'index sémantique après modification des formations / horaires / infos."""
    try:
        n = rag_service.rebuild_index(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec réindexation RAG : {e}") from e
    return {"indexed_chunks": n, "message": "Index RAG reconstruit."}
