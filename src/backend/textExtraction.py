from typing import List, Dict
import os
import re

import pymupdf


class Article:
    """
    Class to extract and process text from a PDF article.
    """

    def __init__(
        self,
        path: os.PathLike,
        title_size: int = 20,
        author_size: int = 15,
        body_size: int = 10,
        note_size: int = 7.5,
    ):

        # Init attributes
        self.path = path
        self.title_size = title_size
        self.author_size = author_size
        self.body_size = body_size
        self.note_size = note_size

        # Init data attributes to None
        self.title = None
        self.authors = None
        self.start_page = None
        self.end_page = None
        self.body = None
        self.irregular_blocks = None

        # Open the PDF document
        self.doc = pymupdf.open(path)
        self.num_pages = len(self.doc)

        # Process the PDF file to extract title, authors, and body text
        self._process_file()

    def _read_page_blocks(self, page_number: int) -> List[Dict]:
        """
        Extract the rich text from a specific page of the document.

        Args:
            page_number (int): The page number to read (0-indexed).

        Returns:
            List[Dict]: A list of dictionaries representing text blocks on the page.
        """

        page = self.doc[page_number]
        blocks = page.get_text(option="dict", flags=11)["blocks"]
        return blocks

    def _parse_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """
        Parse the text blocks to extract text and average font size.

        Args:
            blocks (List[Dict]): The list of text blocks, each containing lines and spans.

        Returns:
            List[Dict]: A list of dictionaries with block text and average font size.
        """
        parsed_blocks = []
        for b in blocks:

            # Skip vertical blocks (height > 5x width)
            x0, y0, x1, y1 = b["bbox"]
            width = x1 - x0
            height = y1 - y0

            if height > 5 * width:
                continue

            font_sizes = []
            for l in b["lines"]:
                for s in l["spans"]:
                    font_sizes.append(s["size"])
            if font_sizes:
                block_text = " ".join(s["text"] for l in b["lines"] for s in l["spans"])
                avg_font_size = round(sum(font_sizes) / len(font_sizes) / 2.5) * 2.5
                parsed_blocks.append({"text": block_text, "size": avg_font_size})
        return parsed_blocks

    def _parse_doc(self) -> Dict[int, List[Dict]]:
        """
        Parse the entire document to extract text blocks and their average font sizes.

        Returns:
            List[Dict]: A list of dictionaries with block text and average font size for each page.
        """
        all_blocks = {}
        for page_number in range(self.num_pages):
            blocks = self._read_page_blocks(page_number)
            parsed_blocks = self._parse_blocks(blocks)
            all_blocks[page_number] = parsed_blocks
        return all_blocks

    def _process_file(self) -> None:
        """
        Process the PDF file to extract title, authors, and body text.
        Ignore any text before the first headline
        or after the second headline (if applicable).
        """
        page_blocks = self._parse_doc()
        start = False
        self.body = ""
        self.irregular_blocks = []
        for page, blocks in page_blocks.items():
            for block in blocks:
                # If no title has been found yet, check for the title
                if not start and block["size"] < self.title_size:
                    continue
                if not start and block["size"] >= self.title_size:
                    start = True
                    self.start_page = page
                    self.title = block["text"]
                    continue

                # If the title has been found, check next title to break
                if block["size"] == self.title_size:
                    self.end_page = page
                    break

                # If block is too small, skip it
                if block["size"] <= self.note_size:
                    continue

                # Add block to appropriate attribute
                if block["size"] == self.author_size and not self.authors:
                    self.authors = block["text"]
                elif block["size"] == self.body_size:
                    self.body += block["text"] + "\n"
                else:
                    self.irregular_blocks.append(block)

        # Remove line breaks unless they are followed by a capital letter, indicating a new sentence
        self.body = re.sub(r"\n(?=[^A-Z])", "", self.body.strip())
