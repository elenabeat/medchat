from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, ForeignKey, DateTime, Text, Integer, Float
from sqlalchemy.orm import mapped_column, Mapped, relationship, DeclarativeBase
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """
    Base class for SQL orm classes.
    """


class ClinCode(Base):
    __tablename__ = "clin_codes"

    cc_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(768), nullable=True
    )  # Store as JSON string

    def __repr__(self) -> str:
        return f"<ClinCode(id={self.cc_id}, code={self.code}, description={self.description})>"


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(768), nullable=True
    )  # Store as JSON string

    def __repr__(self) -> str:
        return f"<Chunk(id={self.chunk_id}, text={self.text[:50]}, created_at={self.created_at})>"


class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(datetime.timezone.utc)
    )
    latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.chunk_id"), nullable=False)
    chunk: Mapped["Chunk"] = relationship("Chunk", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.message_id}, text={self.text[:50]}, created_at={self.created_at})>"
