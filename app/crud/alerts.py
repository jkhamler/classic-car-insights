from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.alert import Alert, AlertMatch
from app.schemas.alert import AlertCreate


def get_alerts(db: Session, user_id: str | None = None) -> list[Alert]:
    q = db.query(Alert)
    if user_id:
        q = q.filter(Alert.user_id == user_id)
    return q.order_by(desc(Alert.created_at)).all()


def get_alert(db: Session, alert_id: int) -> Alert | None:
    return db.query(Alert).filter(Alert.id == alert_id).first()


def create_alert(db: Session, alert: AlertCreate, user_id: str | None = None) -> Alert:
    db_alert = Alert(
        **alert.model_dump(exclude={"criteria_json"}),
        criteria_json=alert.criteria_json.model_dump(),
        user_id=user_id,
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def update_alert(db: Session, alert_id: int, updates: dict) -> Alert | None:
    alert = get_alert(db, alert_id)
    if not alert:
        return None
    for key, value in updates.items():
        setattr(alert, key, value)
    db.commit()
    db.refresh(alert)
    return alert


def delete_alert(db: Session, alert_id: int) -> bool:
    alert = get_alert(db, alert_id)
    if not alert:
        return False
    db.delete(alert)
    db.commit()
    return True


def count_active_alerts(db: Session) -> int:
    return db.query(Alert).filter(Alert.is_active.is_(True)).count()


def get_alert_matches(db: Session, alert_id: int, limit: int = 50) -> list[AlertMatch]:
    return (
        db.query(AlertMatch)
        .filter(AlertMatch.alert_id == alert_id)
        .order_by(desc(AlertMatch.triggered_at))
        .limit(limit)
        .all()
    )


def create_alert_match(db: Session, alert_id: int, listing_id: int) -> AlertMatch:
    match = AlertMatch(alert_id=alert_id, listing_id=listing_id)
    db.add(match)
    db.commit()
    db.refresh(match)
    return match
