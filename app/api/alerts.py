from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud.alerts import (
    get_alerts, get_alert, create_alert, update_alert, delete_alert, get_alert_matches,
)
from app.schemas.alert import AlertCreate, AlertRead, AlertMatchRead

router = APIRouter()


@router.get("", response_model=list[AlertRead])
def list_alerts(db: Session = Depends(get_db)):
    return get_alerts(db)


@router.post("", response_model=AlertRead)
def create_new_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    return create_alert(db, alert)


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert_detail(alert_id: int, db: Session = Depends(get_db)):
    alert = get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/{alert_id}", response_model=AlertRead)
def update_existing_alert(alert_id: int, updates: dict, db: Session = Depends(get_db)):
    alert = update_alert(db, alert_id, updates)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.delete("/{alert_id}")
def delete_existing_alert(alert_id: int, db: Session = Depends(get_db)):
    if not delete_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"ok": True}


@router.get("/{alert_id}/matches", response_model=list[AlertMatchRead])
def list_alert_matches(alert_id: int, db: Session = Depends(get_db)):
    alert = get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return get_alert_matches(db, alert_id)
