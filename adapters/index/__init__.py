"""InMemoryRetrievalIndex：确定性内存检索投影（无 embedding / 向量库依赖）。

search 基于 token 重叠的确定性评分：仅证明 derived projection 可
重建、可检索、可清空，不冒充语义检索（真实 embedding 属未来依赖，
见 BACKLOG）。条目存 (memory_id, content_hash)，支持一致性校验。
"""
