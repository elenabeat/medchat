from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import Engine

from textExtraction import Article
from models import embed_texts
from pydanticModels import EmbeddingRequest
from ormModels import Chunk, Article as ArticleORM, File
from sqlFunctions import insert_data, get_files

logger = logging.getLogger(__name__)
TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=150,
    separators=["\n", ". ", " ", ""],
    keep_separator="end",
)


def generate_chunks(
    article: Article,
    text_splitter: RecursiveCharacterTextSplitter = TEXT_SPLITTER,
) -> List[str]:

    return text_splitter.split_text(article.body)


def idetify_new_files(
    directory: Path,
    existing_files: List[str],
) -> List[Path]:
    """
    Identify new PDF files in a directory that are not in the existing files list.

    Args:
        directory (Path): The path to the directory containing PDF files.
        existing_files (List[str]): A list of existing file names to compare against.

    Returns:
        List[Path]: A list of new file names that are not in the existing files list.
    """
    new_files = []
    for file_path in directory.iterdir():
        if file_path.suffix == ".pdf" and file_path.name not in existing_files:
            new_files.append(
                {
                    "file_path": str(file_path),
                    "filename": file_path.name,
                    "file_type": "pdf",
                    "created_at": datetime.now(),
                    "modified_at": datetime.now(),
                }
            )
    return new_files


def process_files(files: List[File]) -> List[Dict[str, Any]]:
    """
    Process a list of File objects to extract article information.

    Args:
        files (List[File]): A list of File objects representing PDF files.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing extracted article information,
    """

    article_data = []
    for file in files:
        article = Article(file.file_path)
        article_data.append(
            {
                "file_id": file.file_id,
                "start_page": article.start_page,
                "end_page": article.end_page,
                "title": article.title,
                "authors": article.authors,
                "body": article.body,
            }
        )
    return article_data


def process_articles(articles: List[ArticleORM]) -> List[Dict[str, Any]]:
    """
    Process a list of ArticleORM objects to extract article information.

    Args:
        articles (List[ArticleORM]): A list of ArticleORM objects representing articles.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing extracted article information.
    """
    chunk_data = []
    for article in articles:
        chunks = generate_chunks(article)
        for chunk_text in chunks:
            chunk_data.append(
                {
                    "article_id": article.article_id,
                    "text": chunk_text,
                }
            )
    return chunk_data


def process_directory(
    directory: Path,
    engine: Engine,
) -> None:
    """
    Process all unseen PDF files in a directory. Extract article information,
    generate chunks, embed them, and insert into the database.

    Args:
        directory (Path): The path to the directory containing PDF files.
        engine (Engine): SQLAlchemy engine for database operations.
    """
    # Identify unseen files and insert them into the database
    existing_files = [file.filename for file in get_files(engine)]
    file_data = idetify_new_files(directory, existing_files)

    if file_data:
        logger.info(f"Identified {len(file_data)} new files to process.")
        files = insert_data(engine, File, file_data)
        logger.info(f"Inserted new files into the database.")

        # Extract article information from the files and insert into the database
        article_data = process_files(files)
        logger.info(f"Extracted {len(article_data)} articles from files.")
        articles = insert_data(engine, ArticleORM, article_data)
        logger.info(f"Inserted articles into the database.")

        # Generate chunks from the articles
        chunk_data = process_articles(articles)
        logger.info(f"Found {len(chunk_data)} chunks from articles.")

        # Embed the chunks and insert them into the database
        embeddings = embed_texts(
            input_type="article",
            texts=[chunk["text"] for chunk in chunk_data],
        )
        logger.info(f"Generated embeddings for chunks.")

        for chunk, embedding in zip(chunk_data, embeddings):
            chunk["embedding"] = embedding

        insert_data(engine, Chunk, chunk_data)
        logger.info(f"Inserted chunks into the database.")
    else:
        logger.info("No new files to process.")
