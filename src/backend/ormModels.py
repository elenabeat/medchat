from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, ForeignKey, DateTime, Text, Integer, Float
from sqlalchemy.orm import mapped_column, Mapped, relationship, DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for SQL orm classes.
    """

class ClinCode(Base):
    