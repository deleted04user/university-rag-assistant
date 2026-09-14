from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth_utils import get_current_user
from app.database import get_db
from app.models import ChatMessage, User
from app.schemas import ChatAsk, ChatReply
from app.services.chat_pipeline import answer_hybrid

router = APIRouter(prefix="/chat", tags=["chatbot"])


@router.post("/ask", response_model=ChatReply)
def ask(
    body: ChatAsk,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    answer, intent, recs, sources = answer_hybrid(db, body.message)
    db.add(
        ChatMessage(
            user_id=user.id,
            role="user",
            content=body.message,
            intent=intent,
        )
    )
    db.add(
        ChatMessage(
            user_id=user.id,
            role="assistant",
            content=answer,
            intent=intent,
        )
    )
    db.commit()
    return ChatReply(
        answer=answer,
        intent=intent,
        recommendations=recs,
        sources=sources,
    )
