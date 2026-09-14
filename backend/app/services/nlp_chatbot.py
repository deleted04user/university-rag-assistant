"""
Pipeline NLP léger : détection d'intention par mots-clés (FR/EN) + interrogation BDD.
Extensible vers spaCy / Rasa / LLM via la même interface.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models import Formation, Horaire, UniversityInfo


def _norm(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


@dataclass
class IntentResult:
    intent: str
    entities: dict[str, Any]


# (intent, keywords_fr_en)
KEYWORDS: list[tuple[str, tuple[list[str], list[str]]]] = [
    (
        "schedules",
        (
            [
                "horaire",
                "horaires",
                "emploi du temps",
                "cours",
                "quand",
                "seance",
                "salle",
            ],
            ["schedule", "timetable", "class time", "when", "room"],
        ),
    ),
    (
        "programs",
        (
            ["formation", "formations", "programme", "diplome", "filiere", "parcours"],
            ["program", "degree", "course list", "major"],
        ),
    ),
    (
        "admission",
        (
            [
                "inscription",
                "admission",
                "candidat",
                "candidature",
                "s inscrire",
                "inscrire",
            ],
            ["enroll", "registration", "apply", "admission", "candidate"],
        ),
    ),
    (
        "services",
        (
            [
                "bibliotheque",
                "restaurant",
                "crous",
                "sport",
                "service",
                "contact",
                "secretariat",
            ],
            ["library", "cafeteria", "sports", "service", "contact", "office"],
        ),
    ),
    (
        "general",
        (
            ["universite", "campus", "adresse", "qui", "quoi", "information"],
            ["university", "campus", "address", "about", "info"],
        ),
    ),
]


def detect_intent_and_entities(message: str) -> IntentResult:
    n = _norm(message)
    scores: dict[str, float] = {intent: 0.0 for intent, _ in KEYWORDS}
    for intent, (fr, en) in KEYWORDS:
        for kw in fr + en:
            if _norm(kw) in n:
                scores[intent] += 1.0
    # quoted or capitalized token as possible module hint
    module_guess = None
    m = re.search(r"['\"]([^'\"]{2,40})['\"]", message)
    if m:
        module_guess = m.group(1).strip()
    else:
        # "module X" / "cours X"
        m2 = re.search(
            r"(?:module|cours|course|class)\s+([a-zA-Z0-9_.+\-]{2,40})", message, re.I
        )
        if m2:
            module_guess = m2.group(1).strip()

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        best = "general"
    return IntentResult(intent=best, entities={"module_hint": module_guess})


def _format_horaires(rows: list[Horaire], lang: str) -> str:
    if not rows:
        return (
            "Je ne dispose pas de cette information pour le moment."
            if lang == "fr"
            else "I do not have this information at the moment."
        )
    lines = []
    for h in rows:
        lines.append(
            f"- {h.day_of_week} : {h.start_time.strftime('%H:%M')}–{h.end_time.strftime('%H:%M')} "
            f"— {h.module_name} ({h.module_code})"
            + (f", {h.room}" if h.room else "")
        )
    header = "Horaires trouvés :" if lang == "fr" else "Schedules found:"
    return header + "\n" + "\n".join(lines)


def _format_formations(rows: list[Formation], lang: str) -> str:
    if not rows:
        return (
            "Je ne dispose pas de cette information pour le moment."
            if lang == "fr"
            else "I do not have this information at the moment."
        )
    lines = [f"- {f.code} — {f.title} ({f.duration_semesters} sem.)" for f in rows]
    h = "Formations disponibles :" if lang == "fr" else "Available programs:"
    return h + "\n" + "\n".join(lines)


def _format_infos(rows: list[UniversityInfo], lang: str) -> str:
    if not rows:
        return (
            "Je ne dispose pas de cette information pour le moment."
            if lang == "fr"
            else "I do not have this information at the moment."
        )
    parts = []
    for r in rows:
        parts.append(f"**{r.title}**\n{r.content}")
    return "\n\n".join(parts)


def _lang(message: str) -> str:
    n = _norm(message)
    en_hits = sum(1 for _, (_, en) in KEYWORDS for kw in en if _norm(kw) in n)
    fr_hits = sum(1 for _, (fr, _) in KEYWORDS for kw in fr if _norm(kw) in n)
    # simple heuristic
    if re.search(r"\b(the|what|when|how|where|schedule|program)\b", n):
        en_hits += 1
    return "en" if en_hits > fr_hits else "fr"


def recommendations_for_intent(intent: str, lang: str) -> list[str]:
    if lang == "en":
        base = {
            "schedules": [
                "Browse the full schedule page",
                "Ask for a specific module code",
            ],
            "programs": ["Compare program duration", "Ask about admission"],
            "admission": ["See registration steps in University info"],
            "services": ["Contact secretary", "Library hours"],
            "general": ["Programs", "Schedules", "Admission"],
        }
    else:
        base = {
            "schedules": [
                "Consulter la page Horaires complète",
                "Préciser le code ou le nom du module",
            ],
            "programs": [
                "Comparer la durée des parcours",
                "Demander les conditions d'admission",
            ],
            "admission": ["Voir la rubrique Inscription dans Infos université"],
            "services": ["Contacter le secrétariat", "Horaires bibliothèque"],
            "general": ["Formations", "Horaires", "Admission"],
        }
    return base.get(intent, base["general"])


def answer_question(db: Session, message: str) -> tuple[str, str, list[str]]:
    lang = _lang(message)
    ir = detect_intent_and_entities(message)
    intent = ir.intent
    hint = ir.entities.get("module_hint")
    hint_n = _norm(hint) if hint else None

    answer = ""
    if intent == "schedules":
        q = db.query(Horaire)
        if hint_n:
            q = q.filter(
                (Horaire.module_name.ilike(f"%{hint}%"))
                | (Horaire.module_code.ilike(f"%{hint}%"))
            )
        rows = q.order_by(Horaire.day_of_week, Horaire.start_time).limit(25).all()
        answer = _format_horaires(rows, lang)
    elif intent == "programs":
        rows = db.query(Formation).order_by(Formation.code).all()
        answer = _format_formations(rows, lang)
    elif intent == "admission":
        rows = (
            db.query(UniversityInfo)
            .filter(UniversityInfo.category == "admission")
            .all()
        )
        answer = _format_infos(rows, lang)
    elif intent == "services":
        rows = (
            db.query(UniversityInfo)
            .filter(UniversityInfo.category == "services")
            .all()
        )
        answer = _format_infos(rows, lang)
    else:
        rows = (
            db.query(UniversityInfo).filter(UniversityInfo.category == "general").all()
        )
        if not rows:
            rows = db.query(UniversityInfo).limit(5).all()
        answer = _format_infos(rows, lang)

    recs = recommendations_for_intent(intent, lang)
    return answer, intent, recs
