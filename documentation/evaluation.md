# Evaluation Process

This document outlines the methodology used to evaluate the performance of the RAG (Retrieval-Augmented Generation) system. Our approach is composed into two complementary arms: (1) User Interaction metrics, and (2) Controlled Testing Metrics.

## 1. User Interaction Metrics

In this arm, we collect and analyze metrics generated during actual user interactions with the chatbot. This helps us understand how the system performs under real usage conditions and identifies areas for improvement based on authentic user behavior. These metrics will computed from the message logs in the sql database (for details on the database design see `documentation/database.md`)

### Key Performance Indicators

See the notebook `notebooks/user_interaction_metrics.ipynb` to see these queries running.

| KPI                              | Description                                                            | SQL Query                                                                                          |
| -------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Good Feedback Rate**           | % of messages with good feedback, among all messages with feedback.                       | `SELECT AVG(CASE WHEN is_good THEN 1 ELSE 0 END) FROM messages`                                       |
| **Feedback Rate**                | % of messages with any user feedback (`is_good` is not null).    | `SELECT COUNT(*) FILTER (WHERE is_good IS NOT NULL) * 1.0 / COUNT(*) FROM messages`                   |
| **Response Time (Latency)**      | Avg time from query received to response return | `SELECT AVG(response_at - received_at) FROM messages`                                                 |
| **Context Retrieval Time**       | Avg time between query received and context found.                              | `SELECT AVG(context_retreived_at - received_at) FROM messages WHERE context_retreived_at IS NOT NULL;` |
| **Response Generation Time**       | Avg time between context found and response generated.                  | `SELECT AVG(response_at - context_retreived_at) FROM messages WHERE response_at IS NOT NULL;` |
| **Query Volume Over Time**       | Total messages grouped by day/week/etc.                                | `"SELECT DATE(received_at), COUNT(*) FROM messages GROUP BY DATE(received_at) ORDER BY DATE(received_at);"`                                         |
| **Chunks Retrieved per Message** | Avg number of chunks retrieved as context per message.              | `SELECT AVG(chunk_count) FROM (SELECT COUNT(*) AS chunk_count FROM message_context GROUP BY message_id);` |
| **Context Coverage**             | % of messages with at least one chunk.                  | `SELECT COUNT(DISTINCT message_id) FROM message_context`                                                     |
| **Average Messages per Session** | Avg number of messages exchanged in each session.                     | `SELECT AVG(msg_count) FROM (SELECT COUNT(*) AS msg_count FROM messages GROUP BY session_id);`     |
| **Average Sessions per User**          | Avg number of sessions per `user_id`.                             | `SELECT AVG(session_count) FROM (SELECT COUNT(DISTINCT session_id) AS session_count FROM sessions GROUP BY user_id);`                         |                                    |

## 2. Controlled Testing Metrics

To complement real-world data, we also conduct controlled experiments using fixed test inputs across different versions of the chatbot. This allows for direct comparison of changes in the retrieval pipeline, generation model, or prompt design. Controlled evaluations provide:

- Consistent and reproducible test conditions
- A/B comparisons between system variants
- Ground-truth based accuracy assessments
- Qualitative analysis of response helpfulness and completeness

This controlled setting is especially useful for isolating the impact of specific changes and for benchmarking improvements over time.

See the notebook `notebooks/controlled_testing_metrics.ipynb` so see how we implement each of the KPIs below.

### Test Set + Response Generation

For this prototype I manually generated 10 test queries, each consisting of a question, sample answer, and list of relevant chunk ids. These questions are designed to cover a wide range of topics from all parts of the documents. Additionally, some questions require information from multiple chunks to answer, thereby increasing the difficulty level and testing the ability to synthesize information from different chunks.

I acknowledge this testing set is still rather small, so all results should be taken lightly. However, the purpose of this set is not to give a definitive score for the app's performance, but rather serve as an example of the overall testing framework.

Once the test set is ready, I spin up the backend container and directly hit the `chat_response` api with each of the inputs and collect the results from the system.

### Key Performance Indicators

The KPIs fall into two main categories: Context Retrieval Metrics and Response Quality Metrics.

#### Context Retrieval Metrics

These metrics evaluate how well the app is identifying the relevant context from the source documents. The main context retrieval metrics are the precision and recall of the returned chunks for each query. 

As a reminder,

**Recall** measures what fraction of the true (relevant) chunks were actually retrieved.
- For example, if there are 3 relevant chunks in test and the system retrieves 2 of them, recall is 2/3 = 66%.
- High recall ensures the system doesn’t miss important context.

**Precision** measures what fraction of the retrieved chunks are actually relevant.
- For example, if the system retrieves 2 chunks and only 1 are truly relevant, precision is 1/2 = 50%.
- High precision ensures it doesn’t include irrelevant or distracting content.

We will also measure the **F1-score** of the returned chunks, which is the harmonic mean of precision and recall. This is a good way to distill the recall and precision to a single number.


#### Response Quality Metrics

These metrics measure the quality of the model's response in comparisson to the given response. These metrics are particularly important for
- Hallucination detection
- Prompt/Model Testing
- Identifying redundancy in chunks (maybe the app didn't find the target chunk but it found another chunk with overlapping information)

##### Traditional NLP Metrics

We first compare the responses and answers using two traditional NLP metrics: BLEU Score and ROUGE Score.

As a reminder, both metrics can be used to compare a refernce text to a candidate text by measuring the co-occurrences of n-grams. BLEU was originally developed to assess to natural language translation task and ROUGE was developed to evaluate summaries.

Neither metric is particularly well suited for this task, since they only consider n-grams and not more nuanced semantic similarity. However, they are a useful baseline if nothing else.

##### Vector Similarity

Another approach is to take the similarity between the embeddings of the given answer and the response. This should hopefully capture some of the richer semantic meaning that is missing in the BLEU and ROUGE scores.

To generate the embeddings I will be using a new model, `BAAI/bge-m3`. This is a general purpose embedding model that scores well on most evaluation sets (see [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)).

I am deliberately using a new family of models to avoid data leakage in our evaluations. In more detail:
- Using an embedding model from the Qwen family could skew similarity scores upward, as both the generator (Qwen3) and the embedder may have been trained on overlapping data. This could make the responses appear more semantically similar than they actually are.
- Recall the MedCPT models were used to retrieve context that was served as input to the Qwen model during generation. Reusing MEDCPT for evaluation would effectively mean asking the same model to assess the quality of an output that it indirectly influenced. This creates a feedback loop where any semantic alignment introduced during retrieval could artificially inflate the similarity scores. It also risks conflating retrieval performance with response quality, undermining the independence of the evaluation.

An additional benefit of BGE-M3 is that is that it can simultaneously perform the three common retrieval functionalities of embedding model: dense retrieval, multi-vector retrieval, and sparse retrieval. Hence, it's basically 3 vector similarity scores in one, helping us get a more reliable overall similarity.

##### LLM Graded Metrics

In addition to the metrics above, one can also use LLM-graded scores to assess the quality of responses. This involves prompting a large language model to rate or compare responses based on criteria such as correctness, relevance, completeness, or helpfulness.

These methods provide several benefits, namely that:
- LLM's can consider nuance in ways traditional scores cannot, for example sarcasm or negation
- By changing the rubric in the prompts you can emphasize or de-emphasize specific criteria (e.g., don't say anything not fully supported by the context)

However, the inherent randomness of LLM's gives me pause. Before implementing them, I would want to do a study comparing the LLM's scores to human reviewers and measuring their consistency across runs.

For the purposes of this prototype, I also chose to leave them out because I don't have faith in the small models I can run on my hardware to act as reliable reviewers.

