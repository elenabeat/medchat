from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, ForeignKey, DateTime, Text, Integer, Float, Index
from sqlalchemy.orm import mapped_column, Mapped, relationship, DeclarativeBase
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """
    Base class for SQL orm classes.
    """


# class ClinCode(Base):
#     __tablename__ = "clin_codes"

#     cc_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
#     description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
#     embedding: Mapped[Optional[List[float]]] = mapped_column(
#         Vector(768), nullable=True
#     )  # Store as JSON string

#     def __repr__(self) -> str:
#         return f"<ClinCode(id={self.cc_id}, code={self.code}, description={self.description})>"


class File(Base):
    __tablename__ = "files"

    file_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    modified_at: Mapped[datetime] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"<File(id={self.file_id}, filename={self.filename}, created_at={self.created_at})>"


class Article(Base):
    __tablename__ = "articles"

    article_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    file_id: Mapped[int] = mapped_column(ForeignKey("files.file_id"), nullable=False)
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    authors: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<Article(id={self.article_id}, title={self.title}, authors={self.authors})>"


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.article_id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(768), nullable=True
    )  # Store as JSON string

    __table_args__ = (
        Index(
            "idx_chunk_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l2_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<Chunk(id={self.chunk_id}, text={self.text[:50]})>"


class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime)
    response_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # Nullable for messages that may not have response due to errors or timeouts
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.chunk_id"), nullable=False)
    # chunk: Mapped["Chunk"] = relationship("Chunk", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.message_id}, text={self.text[:50]}, created_at={self.created_at})>"
