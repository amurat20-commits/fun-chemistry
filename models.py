from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    original_name = Column(String(512), nullable=False)
    stored_name = Column(String(512), nullable=False, unique=True)
    size = Column(BigInteger, nullable=False)
    extension = Column(String(32), nullable=False)
    mime_type = Column(String(255), nullable=True)
    storage_path = Column(String(1024), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False,
                         default=lambda: datetime.now(timezone.utc))
