"""SQLAlchemy ORM models for scan jobs and analytics snapshots."""
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.postgres import Base


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    files_scanned: Mapped[int] = mapped_column(Integer, default=0)
    nodes_created: Mapped[int] = mapped_column(Integer, default=0)
    edges_created: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    repository: Mapped["Repository"] = relationship("Repository", back_populates="scan_jobs")  # noqa
    analytics_snapshot: Mapped["AnalyticsSnapshot | None"] = relationship("AnalyticsSnapshot", back_populates="scan_job", uselist=False)

    def __repr__(self) -> str:
        return f"<ScanJob id={self.id} status={self.status}>"


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    scan_job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    architecture_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_modules: Mapped[int] = mapped_column(Integer, default=0)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_dependencies: Mapped[int] = mapped_column(Integer, default=0)
    circular_deps: Mapped[int] = mapped_column(Integer, default=0)
    dead_modules: Mapped[int] = mapped_column(Integer, default=0)
    highly_coupled: Mapped[int] = mapped_column(Integer, default=0)
    missing_docs: Mapped[int] = mapped_column(Integer, default=0)
    metrics_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Graph stored in Postgres so it works without Neo4j
    graph_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scan_job: Mapped["ScanJob"] = relationship("ScanJob", back_populates="analytics_snapshot")

    def __repr__(self) -> str:
        return f"<AnalyticsSnapshot repo={self.repository_id} score={self.architecture_score}>"
