# Text Extraction Pipeline

This file contains a basic overview of the text extraction process. For more details and actual examples see `notebooks/text_extraction.ipynb`. Note that while the code in the `src` may differ slightly from that in the notebook (to integrate with the broader application structure) the code in the notebook is functionally the same as what is powering the app.

## Initial Extraction with PyMuPDF

There are several Python libraries that can extract text from a pdf including PyMuPDF, PyPDF2, Camelot, and more. After evaluating a few options and testing them on the provided document, I selected PyMuPDF for the following reasons:

1. **Accurate Layout Preservation**

    PyMuPDF’s maintains paragraph structure and follows a natural reading order (top-down, left-to-right). This is especially important for multi-column documents like ours, since some of the other libraries I tested either scramble the text order or require hardcoded column settings, thus reducing flexibility and generalizability.

2. **Rich Text Metadata**

    PyMuPDF provides detailed styling information for each line of text, including font family, font size, and formatting (bold, italic, etc.). Currently, the pipeline only uses font size to distinguish different parts of the article (e.g. headers vs. body text), but the additional formatting info opens the door for more advanced  processing in future iterations.

3. **Performance**

    PyMuPDF is known for its fast text extraction, which, while not a critical factor at this prototyping stage, would be important in a production environment where efficiency and scalability matter. See: https://pymupdf.readthedocs.io/en/latest/about.html#performance

## Parsing and Cleaning

After using PyMuPDF to extract the text blocks and their styling we perform the following steps:

1. Compute the average font size of each block of text (roughly equivalent to a paragraph) rounded to the nearest 2.5. We perform this rounding because the OCR process that produced the document led to some small variation in font size (e.g., text in the same sentence with sizes 10.1, 10.05. 10.25, etc.).
2. Iterate through the blocks until you encounter a block of font size 20 (indicating the start of the article). Save this block as the article's title.
3. After the start is found, continue iterating and:
    - Add first block of size 15 to the authors
    - Add any blocks of size 10 to the body
    - Skip any blocks of font size <= 7.5
    - Skip any "vertical" blocks (height > 5 * width) as these contain some margin comments.
    - Add any blocks of different size to a list of irregular blocks
4. Stop when the end of the document is reached OR when you encounter another block of size 20 (indicating the start of a new article)
5. Clean up the body text by removing line breaks that interrupt sentences, which are the result of a sentence stretching across columns

## Discussion

Overall, I am satisfied with the text extraction pipeline given the limitations in time and scope. The current process performs very well on the given file and should generalize well to other files with consistent styling.

### Benefits

- **Clean Text**: PyMuPDF extracts text cleanly, with minimal missing/misidentified characters.
- **Accurrate Layout**: PyMuPDF extracts text in the correct reading order (top-down, left-right) without the user hardcoding the documents format (e.g., number of columns or rows).
- **Classify Text from Styling**: use the text styling (font size and orientation) to classify data as article, author, body, or extraneous. 
- **Performant**: article processing time takes approximately 0.03 seconds which is about 0.005 seconds per page.
- **Interpretable & Customizable**: unlike black-box 3rd party services, we can control each step of the process

### Limitations

- **Format Fragility**: This approach assumes consistent formatting across articles. While articles in the same issue of a journal likely have the same styling, different journals may use different styles or journals may change their styling over time.
- **Brittle Text Classification**: we only use font size to classify each block of text, ignoring any semantic understanding. This may lead to issues if the formatting is not consistent within the article, for instance if a Figure label is also Size 10.

### Potential Future Improvements 
- **Autodetect Font-Sizes to Adapt to Different Styles**: dynamically determine the different font size cutoffs for body, authors, or titles
- **Incorporate Semantic Understanding to Text Classification**: for example, author block should not only be of the right size but must contain one or more person names, validated using NER techniques.
- **Track Section Headers or other Structure**: for long articles with mutliple sections (Background, Methods, etc.) capture the sections so we can better contextualize chunks in down stream processes.
- **Parellelization**: the intial processing of each page individually could be parallelized once speed/scalability becomes a concern.