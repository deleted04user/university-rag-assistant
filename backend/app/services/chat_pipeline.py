"""Orchestration chat : RAG local (Phase A) en priorité, puis logique mots-clés + SQL."""

from sqlalchemy.orm import Session

from app.config import settings
from app.services.nlp_chatbot import (
    answer_question,
    detect_intent_and_entities,
    recommendations_for_intent,
    _lang,
)
from app.services import rag_service


def answer_hybrid(db: Session, message: str) -> tuple[str, str, list[str], list[str]]:
    """
    Retourne (answer, intent, recommendations, sources).
    sources = libellés RAG si réponse RAG, sinon [].
    """
    lang = _lang(message)
    if settings.rag_enabled:
        rag = rag_service.try_rag_answer(message, lang)
        if rag is not None:
            text, labels = rag
            ir = detect_intent_and_entities(message)
            recs = recommendations_for_intent(ir.intent, lang)
            hint = (
                "Réponse issue de la recherche locale dans la base (RAG TF‑IDF, sans API payante)."
                if lang == "fr"
                else "Answer from local indexed search (TF‑IDF RAG, no paid API)."
            )
            merged = [hint] + recs[:3]
            return text, "rag", merged, labels

    ans, intent, recs = answer_question(db, message)
    return ans, intent, recs, []
