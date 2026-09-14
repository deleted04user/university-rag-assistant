from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth_utils import require_admin
from app.database import get_db
from app.models import Horaire
from app.schemas import HoraireCreate, HoraireOut, HoraireUpdate

router = APIRouter(prefix="/horaires", tags=["horaires"])


@router.get("", response_model=list[HoraireOut])
def list_horaires(
    db: Session = Depends(get_db),
    formation_id: int | None = Query(None),
    q: str | None = Query(None, description="Filtre module code/nom"),
):
    query = db.query(Horaire)
    if formation_id is not None:
        query = query.filter(Horaire.formation_id == formation_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Horaire.module_name.ilike(like)) | (Horaire.module_code.ilike(like))
        )
    return query.order_by(Horaire.day_of_week, Horaire.start_time).all()


@router.get("/{horaire_id}", response_model=HoraireOut)
def get_horaire(horaire_id: int, db: Session = Depends(get_db)):
    h = db.get(Horaire, horaire_id)
    if not h:
        raise HTTPException(status_code=404, detail="Créneau introuvable")
    return h


@router.post("", response_model=HoraireOut)
def create_horaire(
    data: HoraireCreate, db: Session = Depends(get_db), _: object = Depends(require_admin)
):
    h = Horaire(**data.model_dump())
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


@router.patch("/{horaire_id}", response_model=HoraireOut)
def update_horaire(
    horaire_id: int,
    data: HoraireUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    h = db.get(Horaire, horaire_id)
    if not h:
        raise HTTPException(status_code=404, detail="Créneau introuvable")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(h, k, v)
    db.commit()
    db.refresh(h)
    return h


@router.delete("/{horaire_id}", status_code=204)
def delete_horaire(
    horaire_id: int, db: Session = Depends(get_db), _: object = Depends(require_admin)
):
    h = db.get(Horaire, horaire_id)
    if not h:
        raise HTTPException(status_code=404, detail="Créneau introuvable")
    db.delete(h)
    db.commit()
    return None
