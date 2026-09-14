from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_utils import require_admin
from app.database import get_db
from app.models import Formation
from app.schemas import FormationCreate, FormationOut, FormationUpdate

router = APIRouter(prefix="/formations", tags=["formations"])


@router.get("", response_model=list[FormationOut])
def list_formations(db: Session = Depends(get_db)):
    return db.query(Formation).order_by(Formation.code).all()


@router.get("/{formation_id}", response_model=FormationOut)
def get_formation(formation_id: int, db: Session = Depends(get_db)):
    f = db.get(Formation, formation_id)
    if not f:
        raise HTTPException(status_code=404, detail="Formation introuvable")
    return f


@router.post("", response_model=FormationOut)
def create_formation(
    data: FormationCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    if db.query(Formation).filter(Formation.code == data.code).first():
        raise HTTPException(status_code=400, detail="Code déjà utilisé")
    f = Formation(**data.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.patch("/{formation_id}", response_model=FormationOut)
def update_formation(
    formation_id: int,
    data: FormationUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    f = db.get(Formation, formation_id)
    if not f:
        raise HTTPException(status_code=404, detail="Formation introuvable")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    return f


@router.delete("/{formation_id}", status_code=204)
def delete_formation(
    formation_id: int, db: Session = Depends(get_db), _: object = Depends(require_admin)
):
    f = db.get(Formation, formation_id)
    if not f:
        raise HTTPException(status_code=404, detail="Formation introuvable")
    db.delete(f)
    db.commit()
    return None
