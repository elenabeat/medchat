from typing import List, Dict, Any, Type
import os
import logging

from sqlalchemy import create_engine, Engine, select, insert, text
from sqlalchemy.orm import Session
from sqlalchemy.engine import URL
from sqlalchemy_utils import database_exists, create_database, drop_database
import toml

from ormModels import Base, File

CONFIG = toml.load("config.toml")
logger = logging.getLogger(__name__)


def create_connection() -> Engine:
    """
    Opens a connection to the PostgreSQL database specified in the configuration file.
    Also creates the database and tables if they do not exist.

    Returns:
        Engine: SQLAlchemy engine connected to the PostgreSQL database.
    """

    db_url = URL.create(
        drivername=CONFIG["DRIVER"],
        username=CONFIG["USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=CONFIG["HOST"],
        port=CONFIG["PORT"],
        database=CONFIG["DATABASE"],
    )

    if CONFIG["FORCE_REBUILD"] and database_exists(db_url):
        logger.info("Dropping existing database...")
        drop_database(db_url)

    if not database_exists(db_url):
        create_database(db_url)
        logger.info(f"Database {CONFIG['DATABASE']} created successfully.")

    engine = create_engine(db_url, echo=False)
    engine.connect()

    with Session(engine) as session:
        with session.begin():
            session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    Base.metadata.create_all(engine)

    return engine


def insert_data(
    engine: Engine, table: Type[Base], data: List[Dict[str, Any]]
) -> List[Base]:
    """
    Inserts data into the specified table in the database.

    Args:
        engine (Engine): SQLAlchemy engine for database operations.
        table (Type[Base]): The ORM model class representing the table to insert data into.
        data (List[Dict[str, Any]]): A list of dictionaries containing the data to be inserted.

    Returns:
        List[Base]: A list of ORM objects representing the inserted rows.
    """

    with Session(engine) as session:
        outputs = session.scalars(insert(table).returning(table), data)
        session.commit()
        return outputs.all()


def get_files(engine: Engine) -> List[File]:
    """
    Retrieves all files from the database.

    Args:
        engine (Engine): SQLAlchemy engine for database operations.

    Returns:
        List[File]: A list of File ORM objects.
    """

    with Session(engine) as session:
        stmt = select(File)
        return session.scalars(stmt).all()
