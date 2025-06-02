# Text Processing Pipeline

After extracting the text data from the file, the next step is to process it by chunking the text into manageable pieces and generating embeddings. For more details and actual examples see `notebooks/text_processing.ipynb`. Note that while the code in the `src` may differ slightly from that in the notebook (to integrate with the broader application structure) the code in the notebook is functionally the same as what is powering the app.

## Chunk Article Body

### Why chunk the text?

#### 1. Context limit

LLM's have a context limit, i.e., a maximum number of tokens they can process during inference. While recent advances have brought about commercial and open-source models with context limits in the 10's or 100's of thousands, many smaller models may not be able to fit the entire article in context. Breaking the article into chunks allows us to use smaller models which only need to read the relevant portions of the document at inference time.

In order to serve the model the right portion of the document for a given query, we will implement a retrieval pipeline which will use an embedding model. Similar to LLM's, these embedding models have their own context windows.

#### 2. Latency

When generating a response, the LLM will need to process each input token before generating its first output token. Even if a model could fit the entire article in context, it would take much longer to respond if we asked it to read the entire article instead of just a relevant snippet.


### Chunking Strategy

We will be using a fairly standard Recursive Character Text Splitting algorithm, outlined below.

The goal is to split text into chunks with:
- A maximum chunk size (e.g., 1000 characters)
- A minimum amount of overlap between chunks (e.g., 200 characters)
- Preserving natural language structure, like paragraphs or sentences, wherever possible

You initialize the text splitter with:
- `separators`: Ordered list of characters to try splitting on, ordered in descending priority

- `chunk_size`: Maximum size of a chunk.

- `chunk_overlap`: Number of characters that overlap between adjacent chunks.

Algorithm:
1. Split the text using the first separator.
2. Check the size of each split. For each candidate chunk:
    - If it's smaller than or equal to chunk_size, accept it.
    - If it's larger than chunk_size, recursively split it using the next separator in the list.
3. Repeat Step 2 recursively until all candidate chunks are of an acceptable size. This usually leads to over-splitting.
4. Iteratively merge candidate chunks to get as close to the `chunk_size` as possible (without going over) and meet the minimum chunk overlap requirements.

#### How to set parameters?

**Chunk Size**

Downstream, I want to generate embeddings for each chunk using the [MedCPT-Article-Encoder](https://huggingface.co/ncbi/MedCPT-Article-Encoder), an embedding model that was trained on abstracts from PubMed (more on this in `documentation/language_models.md`). Because this model was trained on abstracts, I want to make each chunk roughly the same length as an abstract, which are usually between 150-250 words. Taking an average of 5 characters per word this give us between 750-1250 characters on average. This agrees with [this article](https://urds.uoregon.edu/symposium/abstracts) I found from the University of Oregon which gives a typical upper bound of 1500 characters for abstracts. 

Hence, I will use 1500 maximum chunk size.

**Separators**

I used the standard list of separators for this library, except I added `". "` to try to force more splits at the end of sentences. The goal being to make sure each chunk is interpretable on its own, since the llm won't be able to look back/ahead to get more context.

**Chunk Overlap**

I set this to 150 characters which roughly equals a sentence or two of overlap. Again, the goal being to make each chunk interpretable on its own.

## Generate Chunk Embeddings

As I mentioned above, I generate embeddings for each chunk using the [MedCPT-Article-Encoder](https://huggingface.co/ncbi/MedCPT-Article-Encoder). For more details and justification for this choice see `documentation/language_models.md`.

## Bonus: Extract Keywords

## Keyword Extraction

>**NOTE**: 
>I originally intended to use this code in the app but did not have time to integrate it. My plan was to (1) use it to perform hybrid search (keyword matching +  vector similarity) in the rag pipeline, and (2) compare the keywords to the set of clinical code descriptions described in the [Clinical Knowledge Graph](https://github.com/mims-harvard/Clinical-knowledge-embeddings) article. I would then use a 0-shot classifier to tag each chunk with its relevant clinical codes.
>
> You can still find the code to do the keyword extraction in the notebook.

We compute the keywords using the TextRank algorithm. At a high level, this algorithm works by creating a graph where "words" (after some pre-processing) are nodes and their connections are based on co-occurrence. The algorithm then applies PageRank to rank the nodes, identifying the most important words. These words can be aggreated into phrases or sentences in a post processing step. This is one of the main benefits of this algorithm over other common approaches (such as KeyBERT, RAKE, YAKE) which only return single words. For example, in our use-case we would want to identify "breast cancer" as a keyword, not just "breast" or "cancer".

In this implementation we will use spacy's `en_core_web_sm` model and the `PyTextRank` library's implementation of the TextRank algorithm.

Let's test it below on the first chunk, which happens to be exactly the abstract of the article.