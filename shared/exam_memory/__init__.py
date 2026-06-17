"""exam-memory V2 - exam experience MCP Server.

Exports:
    from exam_memory.embedding import encode, is_available, get_embedder
    from exam_memory.vector_store import NumpyVectorStore
    from exam_memory.fts_store import FTSStore
    from exam_memory.hybrid_search import hybrid_search, FUSION_WEIGHTS
    from exam_memory.chunking import chunk_text, EXPERIENCE_CHUNK_CHARS

Usage:
    python -m exam_memory.server          # start MCP server
    python -m exam_memory.rebuild_index   # rebuild all indexes
"""

__version__ = "2.0.0"
