# Text Extraction Pipeline

The first step in processing the input file is extracting its text content. This file contains a basic overview of the process. For more details and actual examples see `notebooks/text_extraction.ipynb`.

## Overview 

One of the main challenges of extracting text from the given file was the multi-column layout. This meant that naive text extraction 

The primary goal is to extract structured text while preserving logical reading order and enabling future semantic analysis.


Key Features

    Uses PyMuPDF for high-fidelity text extraction

    Preserves natural reading flow across multi-column layouts

    Extracts metadata like font size to help identify headings and body text

    Filters out non-essential elements like footers and correspondence notes

Why PyMuPDF?

After evaluating various libraries (e.g., PyPDF2, Camelot), PyMuPDF was selected for its:

    Accurate Layout Handling: Maintains paragraph structure and reading order (top-to-bottom, left-to-right) even in multi-column formats.

    Rich Text Metadata: Captures styling info (e.g., font size), which is useful for distinguishing between headers and body text.

    Performance: Offers fast and efficient extraction—beneficial for scaling.

Process Walkthrough

    Setup

        Import required libraries (pymupdf, re, time, etc.)

        Load the target PDF file, skipping the cover page if needed.

    Initial Extraction

        Use PyMuPDF’s .get_text("text") to extract plain text.

        Review the output to understand line breaks and non-content noise.

    Structured Extraction

        Switch to .get_text("dict") to extract words along with positional and styling information.

        Filter and sort content using bounding box coordinates and font size.

    Cleaning and Organization

        Remove footer text (e.g., journal info, author correspondence).

        Group lines into paragraphs using their vertical position and indentation heuristics.

        Identify headers based on relative font sizes.

    Result Preview

        Print or preview the cleaned and structured paragraphs.

    Discussion

        Pros: Clean extraction, respects layout, useful metadata.

        Cons: Some false positives, no semantic tagging yet.

        Future Work: Use additional metadata (e.g., bold, italic), implement section labeling, and integrate NLP for better content segmentation.