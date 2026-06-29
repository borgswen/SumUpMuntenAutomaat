from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

Base = declarative_base()


class PaymentRecord(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(64), nullable=False)
    transaction_id = Column(String(128), nullable=True)
    raw_payload = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False)


class Database:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def add_payment(
        self,
        amount: int,
        price: float,
        status: str,
        transaction_id: str | None = None,
        raw_payload: Any | None = None,
    ) -> PaymentRecord:
        session: Session = self.SessionLocal()
        record = PaymentRecord(
            amount=amount,
            price=price,
            status=status,
            transaction_id=transaction_id,
            raw_payload=str(raw_payload) if raw_payload is not None else None,
            timestamp=datetime.utcnow(),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        session.close()
        return record

    def list_payments(self) -> list[PaymentRecord]:
        session: Session = self.SessionLocal()
        records = session.query(PaymentRecord).order_by(PaymentRecord.timestamp.desc()).all()
        session.close()
        return records
