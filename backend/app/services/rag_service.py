"""
Phase A — RAG 100 % local : TF-IDF (scikit-learn) + similarité cosinus.
Aucune API payante, pas de compilation C++, fonctionne sous Windows + Python 3.13.
Pour aller plus loin (sémantique neurale) : ajouter des embeddings plus tard (GPU / build tools).
"""

from __future__ import annotations

import logging
import os
import re
from typing import TYPE_CHECKING, Optional

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_cache: dict | None = None


def _one_line(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def _index_path() -> str:
    return settings.rag_index_path


def rebuild_index(db: "Session") -> int:
    """Construit la matrice TF-IDF et la sauvegarde + cache mémoire."""
    global _cache
    from app.models import Formation, Horaire, UniversityInfo

    index_texts: list[str] = []
    display_texts: list[str] = []
    labels: list[str] = []

    for f in db.query(Formation).order_by(Formation.id).all():
        readable = (
            f"Formation {f.code} — {f.title}. "
            f"Durée : {f.duration_semesters} semestres. {f.description or ''}"
        )
        boost = " programme diplôme parcours cursus licence master"
        display_texts.append(_one_line(readable))
        index_texts.append(_one_line(readable + boost))
        labels.append(f"{f.code} — {f.title}")

    for h in db.query(Horaire).order_by(Horaire.id).all():
        st = h.start_time.strftime("%H:%M")
        et = h.end_time.strftime("%H:%M")
        room = h.room or "non précisée"
        teacher = h.teacher or "non précisé"
        readable = (
            f"Cours « {h.module_name} » (code {h.module_code}). "
            f"Jour : {h.day_of_week}, de {st} à {et}. Salle : {room}. Enseignant : {teacher}."
        )
        boost = " horaire emploi du temps cours schedule timetable class"
        display_texts.append(_one_line(readable))
        index_texts.append(_one_line(readable + boost))
        labels.append(f"{h.module_code} — {h.module_name}")

    for i in db.query(UniversityInfo).order_by(UniversityInfo.id).all():
        readable = f"[{i.category}] {i.title}. {i.content}"
        boost = " inscription admission contact service université"
        display_texts.append(_one_line(readable))
        index_texts.append(_one_line(readable + boost))
        labels.append(f"{i.category}: {i.title}")

    if not index_texts:
        logger.warning("RAG: aucun document à indexer.")
        _cache = None
        p = _index_path()
        if os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass
        return 0

    vectorizer = TfidfVectorizer(
        max_features=8192,
        ngram_range=(1, 2),
        min_df=1,
        strip_accents="unicode",
        lowercase=True,
    )
    matrix = vectorizer.fit_transform(index_texts)

    path = _index_path()
    joblib.dump(
        {
            "vectorizer": vectorizer,
            "matrix": matrix,
            "display_texts": display_texts,
            "labels": labels,
        },
        path,
    )

    _cache = {
        "vectorizer": vectorizer,
        "matrix": matrix,
        "display_texts": display_texts,
        "labels": labels,
    }
    logger.info("RAG: %s passages indexés (TF-IDF, %s).", len(index_texts), path)
    return len(index_texts)


def _load_cache() -> bool:
    global _cache
    if _cache is not None:
        return True
    path = _index_path()
    if not os.path.isfile(path):
        return False
    try:
        data = joblib.load(path)
        _cache = {
            "vectorizer": data["vectorizer"],
            "matrix": data["matrix"],
            "display_texts": data["display_texts"],
            "labels": data["labels"],
        }
        return True
    except Exception as e:
        logger.warning("Impossible de charger l'index RAG : %s", e)
        return False


def try_rag_answer(question: str, lang: str) -> Optional[tuple[str, list[str]]]:
    if not settings.rag_enabled:
        return None

    q = question.strip()
    if not q:
        return None

    if not _load_cache():
        return None

    vectorizer: TfidfVectorizer = _cache["vectorizer"]
    matrix = _cache["matrix"]
    display_texts: list[str] = _cache["display_texts"]
    labels: list[str] = _cache["labels"]

    if matrix.shape[0] == 0:
        return None

    qv = vectorizer.transform([_one_line(q)])
    sims = cosine_similarity(qv, matrix)[0]
    k = min(settings.rag_top_k, len(sims))
    top_idx = np.argsort(-sims)[:k]

    best = float(sims[top_idx[0]])
    if best < settings.rag_min_similarity:
        return None

    bullets: list[str] = []
    src_labels: list[str] = []
    seen: set[str] = set()

    for i in top_idx:
        s = float(sims[i])
        if s < settings.rag_min_similarity:
            continue
        raw = display_texts[int(i)]
        if len(raw) > 420:
            raw = raw[:417] + "…"
        bullets.append(raw)
        lab = labels[int(i)]
        if lab not in seen:
            seen.add(lab)
            src_labels.append(lab)

    if not bullets:
        return None

    if lang == "en":
        header = "Here are the most relevant excerpts from the university knowledge base:\n\n"
        src = "Sources"
    else:
        header = "Voici les passages les plus pertinents de la base documentaire :\n\n"
        src = "Sources"

    body = "\n".join(f"• {b}" for b in bullets)
    footer = f"\n\n{src} : " + " · ".join(src_labels[:6])
    return header + body + footer, src_labels
