"""Elasticsearch index configurations for file upload module."""


def get_pdf_index_mappings(embedding_dimension: int = 1536) -> dict:
    """
    Get Elasticsearch mappings for PDF document chunks index.
    
    Args:
        embedding_dimension: Dimension of the embedding vectors (default: 1536 for OpenAI)
        
    Returns:
        Dictionary containing index mappings configuration
    """
    return {
        "properties": {
            "file_id": {"type": "keyword"},
            "filename": {"type": "text"},
            "cdn_url": {"type": "keyword"},
            "file_type": {"type": "keyword"},
            "sub_folder": {"type": "keyword"},
            "page_number": {"type": "integer"},
            "text_content": {
                "type": "text",
                "analyzer": "standard"
            },
            "embeddings": {
                "type": "dense_vector",
                "dims": embedding_dimension,
                "index": True,
                "similarity": "cosine"
            },
            "char_count": {"type": "integer"},
            "total_pages": {"type": "integer"},
            "pdf_metadata": {
                "properties": {
                    "title": {"type": "text"},
                    "author": {"type": "text"},
                    "subject": {"type": "text"},
                    "creator": {"type": "text"},
                    "producer": {"type": "text"},
                    "creation_date": {"type": "keyword"},
                    "modification_date": {"type": "keyword"}
                }
            },
            "custom_metadata": {"type": "object", "enabled": True},
            "chunk_type": {"type": "keyword"},
            "indexed_at": {"type": "date"},
            # Additional fields for similarity search filters
            "category": {"type": "keyword"},
            "year": {"type": "keyword"},
            "season": {"type": "keyword"}
        }
    }


def get_pdf_index_settings() -> dict:
    """
    Get Elasticsearch settings for PDF document chunks index.
    
    Returns:
        Dictionary containing index settings configuration
    """
    return {
        "number_of_shards": 1,
        "number_of_replicas": 1
    }
