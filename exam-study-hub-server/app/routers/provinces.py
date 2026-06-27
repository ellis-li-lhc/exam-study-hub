# 报考省份接口（只读）。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import province as crud_province
from app.schemas.province import ProvinceRead

router = APIRouter(prefix="/api/provinces", tags=["provinces"])


@router.get("", response_model=list[ProvinceRead])
def read_provinces(db: Session = Depends(get_db)):
    return crud_province.list_provinces(db)
