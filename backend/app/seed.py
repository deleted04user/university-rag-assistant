from datetime import time

from sqlalchemy.orm import Session

from app.auth_utils import hash_password
from app.models import Formation, Horaire, UniversityInfo, User, UserRole


def seed_if_empty(db: Session) -> None:
    if db.query(User).first():
        return

    admin = User(
        email="admin@univ-demo.fr",
        hashed_password=hash_password("admin123"),
        full_name="Administrateur",
        role=UserRole.admin,
    )
    stud = User(
        email="student@univ-demo.fr",
        hashed_password=hash_password("student123"),
        full_name="Étudiant Démo",
        role=UserRole.student,
    )
    db.add_all([admin, stud])

    info = Formation(
        code="L3-INFO",
        title="Licence Informatique",
        description="Parcours développement logiciel et systèmes.",
        duration_semesters=6,
    )
    data = Formation(
        code="M-DATA",
        title="Master Data Engineering",
        description="Big data, pipelines et analyse.",
        duration_semesters=4,
    )
    db.add_all([info, data])
    db.flush()

    db.add_all(
        [
            Horaire(
                module_code="INF301",
                module_name="Programmation Java",
                day_of_week="Lundi",
                start_time=time(10, 0),
                end_time=time(12, 0),
                room="A-102",
                teacher="Dr. Martin",
                formation_id=info.id,
            ),
            Horaire(
                module_code="INF301",
                module_name="Programmation Java",
                day_of_week="Mercredi",
                start_time=time(14, 0),
                end_time=time(16, 0),
                room="Lab-3",
                teacher="Dr. Martin",
                formation_id=info.id,
            ),
            Horaire(
                module_code="DATA501",
                module_name="Bases de données avancées",
                day_of_week="Mardi",
                start_time=time(9, 0),
                end_time=time(11, 0),
                room="C-201",
                teacher="Pr. Benali",
                formation_id=data.id,
            ),
        ]
    )

    db.add_all(
        [
            UniversityInfo(
                category="admission",
                title="Inscription",
                content=(
                    "1. Créez un compte sur la plateforme.\n"
                    "2. Remplissez le dossier en ligne.\n"
                    "3. Validez votre email et joignez les pièces demandées.\n"
                    "4. Suivez l'état dans votre espace candidat."
                ),
            ),
            UniversityInfo(
                category="services",
                title="Bibliothèque",
                content="Ouverture : lundi–vendredi 8h30–19h. Week-end 9h–13h.",
            ),
            UniversityInfo(
                category="services",
                title="Secrétariat pédagogique",
                content="Email : scolarite@univ-demo.fr — Accueil : bâtiment A, rez-de-chaussée.",
            ),
            UniversityInfo(
                category="general",
                title="Présentation",
                content=(
                    "Notre université propose des formations en informatique et data. "
                    "Campus principal : ville-centre, accès transports en commun."
                ),
            ),
        ]
    )
    db.commit()
