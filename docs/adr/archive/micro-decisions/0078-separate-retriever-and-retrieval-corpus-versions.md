# Separate Retriever and Retrieval Corpus Versions

V1 will version retriever behavior separately from the retrieval corpus. Retriever versions describe search algorithms and configuration such as keyword, embedding, hybrid, top-k, and reranking behavior, while retrieval corpus versions describe the project knowledge and repository evidence snapshot being indexed; separating them makes retrieval quality changes attributable to strategy changes or corpus changes rather than an ambiguous combined version.
