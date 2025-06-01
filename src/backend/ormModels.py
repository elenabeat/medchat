from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, ForeignKey, DateTime, Text, Integer, Index
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """
    Base class for SQL orm classes.
    """


class File(Base):
    __tablename__ = "files"

    # Primary key
    file_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Columns
    file_path: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    modified_at: Mapped[datetime] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"File(id={self.file_id}, filename={self.filename}, created_at={self.created_at})"


class Article(Base):
    __tablename__ = "articles"

    # Primary key
    article_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    # Foreign key
    file_id: Mapped[int] = mapped_column(ForeignKey("files.file_id"), nullable=False)

    # Columns
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    authors: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    file = relationship("File", backref="articles")

    def __repr__(self) -> str:
        return (
            f"Article(id={self.article_id}, title={self.title}, authors={self.authors})"
        )


class Chunk(Base):
    __tablename__ = "chunks"

    # Primary key
    chunk_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.article_id"), nullable=False
    )

    # Columns
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)

    # Relationships
    article: Mapped[Article] = relationship("Article", backref="chunks")
    # messages: Mapped[List["Message"]] = relationship(
    #     "Message", secondary="message_context", back_populates="message_chunks"
    # )

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
        return f"Chunk(id={self.chunk_id}, text={self.text[:50]})"


class Session(Base):
    __tablename__ = "sessions"

    # Primary key
    session_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    # Columns
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    messages: Mapped[List["Message"]] = relationship("Message", backref="session")

    def __repr__(self) -> str:
        return f"Session(id={self.session_id}, user_id={self.user_id}, created_at={self.created_at})"


class Message(Base):
    __tablename__ = "messages"

    # Primary key
    message_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    # Foreign key
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.session_id"), nullable=False
    )

    # Columns
    query: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime)
    search_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_retreived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    response_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    chunks: Mapped[List[Chunk]] = relationship("Chunk", secondary="message_context")

    def __repr__(self) -> str:
        return f"Message(id={self.message_id}, text={self.text[:50]}, received_at={self.received_at})"


class MessageContext(Base):
    __tablename__ = "message_context"

    # Primary keys
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.message_id"), primary_key=True
    )
    chunk_id: Mapped[int] = mapped_column(
        ForeignKey("chunks.chunk_id"), primary_key=True
    )

    def __repr__(self) -> str:
        return f"MessageContext(id={self.message_context_id}, message_id={self.message_id}, chunk_id={self.chunk_id})"
