from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth_utils import require_admin
from app.database import get_db
from app.models import UniversityInfo
from app.schemas import UniversityInfoCreate, UniversityInfoOut, UniversityInfoUpdate

router = APIRouter(prefix="/infos", tags=["university_infos"])


@router.get("", response_model=list[UniversityInfoOut])
def list_infos(
    db: Session = Depends(get_db),
    category: str | None = Query(None),
):
    q = db.query(UniversityInfo)
    if category:
        q = q.filter(UniversityInfo.category == category)
    return q.order_by(UniversityInfo.category, UniversityInfo.title).all()


@router.get("/{info_id}", response_model=UniversityInfoOut)
def get_info(info_id: int, db: Session = Depends(get_db)):
    row = db.get(UniversityInfo, info_id)
    if not row:
        raise HTTPException(status_code=404, detail="Information introuvable")
    return row


@router.post("", response_model=UniversityInfoOut)
def create_info(
    data: UniversityInfoCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    row = UniversityInfo(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{info_id}", response_model=UniversityInfoOut)
def update_info(
    info_id: int,
    data: UniversityInfoUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    row = db.get(UniversityInfo, info_id)
    if not row:
        raise HTTPException(status_code=404, detail="Information introuvable")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{info_id}", status_code=204)
def delete_info(
    info_id: int, db: Session = Depends(get_db), _: object = Depends(require_admin)
):
    row = db.get(UniversityInfo, info_id)
    if not row:
        raise HTTPException(status_code=404, detail="Information introuvable")
    db.delete(row)
    db.commit()
    return None
