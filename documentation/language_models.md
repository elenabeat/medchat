
# Language Models

## Retrieval: MedCPT

To generate embeddings for user queries and article chunks, we use the `MedCPT` family of models developed by NCBI.

`MedCPT` includes three models:

* **[MedCPT-Query-Encoder](https://huggingface.co/ncbi/MedCPT-Query-Encoder)**: generates embeddings from user queries.
* **[MedCPT-Article-Encoder](https://huggingface.co/ncbi/MedCPT-Article-Encoder)**: generates embeddings for article chunks.
* **[MedCPT-Cross-Encoder](https://huggingface.co/ncbi/MedCPT-Cross-Encoder)**: a cross-encoder model that ranks  chunks based on relevance to the query.

These models are trained over 23 million PubMed abstracts and over 255 million query-article relevance pairs derived from real-world search logs, making them highly specialized for medical text retrieval.

### Benefits

1. **Optimized for medical language**

    General-purpose embedding models often perform poorly on biomedical text because of the amount of domain-specific jargon. MedCPT is trained specifically on clinical and scientific abstracts, making it far more effective in identifying semantically relevant information in our domain.
2. **Reranking with cross-encoder**

    Many [studies]((https://ieeexplore.ieee.org/abstract/document/10711642)) and [guides](https://weaviate.io/blog/cross-encoders-as-reranker?utm_source=chatgpt.com) show that using cross-encoders to rerank top results significantly improves retrieval accuracy in RAG pipelines. I have personally seen the benefits of this approach in my prior experience.
3. **Small model size**

    At just 109M parameters each, the MedCPT models are efficient and lightweight. This is particularly important for this prototype as we possess limited GPU RAM, most of which will be consumed by the text generation model. For comparison, most of the top models on the [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard) exceed 7B parameters. 

Learn more about MedCPT in their [paper](https://arxiv.org/abs/2307.00589).


## Text-Generation: Qwen3-4b (AWQ)

We use [**Qwen3-4b-AWQ**](https://huggingface.co/Qwen/Qwen3-4B-AWQ) as our main text generation model for two key stages of the RAG pipeline: query rewriting and final response generation

Qwen3-4b is a compact, high-performance chat model developed by Alibaba Cloud, trained on diverse multilingual and multi-domain data. We use an **AWQ quantized** version of the model, which quantizes the model weights to 4-bit precision.

### Benefits

1. **Strong performance at small scale**

    Despite being only 4B parameters, Qwen3 consistently outperforms many larger models on reasoning and dialogue tasks. 

    See, for example: [Qwen Paper](https://arxiv.org/abs/2505.09388), [Qwen Blog Post](https://qwenlm.github.io/blog/qwen3/) and the [LM Arena Leaderboard](https://lmarena.ai/leaderboard/text/instruction-following) (only compares Qwen3-3b, but general principal stands).

2. **Quantized for efficiency**

    The AWQ (Activation-aware Weight Quantization) format enables us to run the model within tight GPU memory constraints and with reducing latency without a noticeable loss in generation quality.

3. **Optional Reasoning**

    Qwen3-4b uniquely supports switching between "thinking mode" (for complex logical reasoning) and "non-thinking mode" (for general-purpose dialogue). When enabled, thinking mode generates intermediate reasoning steps ("thinking tokens") before producing a final answer, improving performance on complicated tasks.
    
    In our pipeline, we *disable thinking mode for query generation* to minimize latency, and *enable thinking mode for final response generation* to enhance response quality.

We’ve found Qwen3-4b-AWQ strikes an excellent balance between capability and resource usage, making it ideal for use alongside lightweight retrievers in GPU-limited environments.


