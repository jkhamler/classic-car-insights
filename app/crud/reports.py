from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.ai_report import AIReport


def get_latest_report(db: Session, report_type: str) -> AIReport | None:
    return (
        db.query(AIReport)
        .filter(AIReport.report_type == report_type)
        .order_by(desc(AIReport.generated_at))
        .first()
    )


def get_report_for_listing(db: Session, listing_id: int) -> AIReport | None:
    return (
        db.query(AIReport)
        .filter(AIReport.listing_id == listing_id, AIReport.report_type == "opportunity_analysis")
        .order_by(desc(AIReport.generated_at))
        .first()
    )


def get_report_for_vehicle(db: Session, vehicle_id: int) -> AIReport | None:
    return (
        db.query(AIReport)
        .filter(AIReport.vehicle_id == vehicle_id, AIReport.report_type == "investment_thesis")
        .order_by(desc(AIReport.generated_at))
        .first()
    )


def create_report(
    db: Session,
    report_type: str,
    content: str,
    title: str | None = None,
    vehicle_id: int | None = None,
    listing_id: int | None = None,
    metadata_json: dict | None = None,
) -> AIReport:
    report = AIReport(
        report_type=report_type,
        title=title,
        content=content,
        vehicle_id=vehicle_id,
        listing_id=listing_id,
        metadata_json=metadata_json,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
