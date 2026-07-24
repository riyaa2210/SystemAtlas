"""SQLAlchemy ORM model for repositories."""
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.postgres import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False)
    github_url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    languages: Mapped[dict] = mapped_column(JSONB, default=list)
    frameworks: Mapped[dict] = mapped_column(JSONB, default=list)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    star_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="repositories")  # noqa: F821
    scan_jobs: Mapped[list["ScanJob"]] = relationship(  # noqa: F821
        "ScanJob", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository id={self.id} full_name={self.full_name}>"
