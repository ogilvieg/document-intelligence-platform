"""Synthetic, precomputed analysis shown by the zero-risk demo path."""

SAMPLE_ANALYSIS = {
    "sample": {
        "synthetic": True,
        "fixture_version": "contract-review-v1",
        "title": "Synthetic Services Agreement",
        "description": "Precomputed example using fictional contract text.",
        "metrics_are_representative": True,
    },
    "analysis": {
        "analysis_id": "sample-analysis-contract-v1",
        "query": "Identify material commercial and termination risks.",
        "output": {
            "overall_fit": "The agreement is workable, but its termination and liability terms need revision before signature.",
            "strengths": [
                "Service levels and reporting duties are defined.",
                "Fees and renewal timing are stated clearly.",
            ],
            "gaps": [
                "The agreement lacks a cure period before termination.",
                "Data-return timing is not specified.",
            ],
            "risk_factors": [
                "Liability is uncapped for the customer but capped for the provider.",
                "The provider may terminate for convenience on short notice.",
            ],
            "confidence": 0.88,
            "recommended_focus": [
                "Add a mutual liability cap.",
                "Negotiate a 30-day cure period and data-return deadline.",
            ],
        },
        "citations": [
            {
                "chunk_id": "sample-chunk-termination",
                "document_id": "synthetic-sample-document",
                "document_title": "Synthetic Services Agreement (Sample)",
                "chunk_text": "Provider may terminate this Agreement for convenience upon ten days' written notice.",
                "relevance_score": 0.94,
            },
            {
                "chunk_id": "sample-chunk-liability",
                "document_id": "synthetic-sample-document",
                "document_title": "Synthetic Services Agreement (Sample)",
                "chunk_text": "Provider's aggregate liability will not exceed fees paid in the prior three months.",
                "relevance_score": 0.91,
            },
        ],
        "retrieved_chunks": [
            {
                "chunk_id": "sample-chunk-termination",
                "document_id": "synthetic-sample-document",
                "document_title": "Synthetic Services Agreement (Sample)",
                "doc_type": "pdf",
                "chunk_index": 7,
                "text": "Provider may terminate this Agreement for convenience upon ten days' written notice. Customer may terminate only for an uncured material breach.",
                "similarity_score": 0.94,
                "metadata": {"page": 6, "section": "Termination"},
            },
            {
                "chunk_id": "sample-chunk-liability",
                "document_id": "synthetic-sample-document",
                "document_title": "Synthetic Services Agreement (Sample)",
                "doc_type": "pdf",
                "chunk_index": 11,
                "text": "Provider's aggregate liability will not exceed fees paid in the prior three months. Customer obligations are not similarly limited.",
                "similarity_score": 0.91,
                "metadata": {"page": 9, "section": "Limitation of Liability"},
            },
        ],
        "retrieval_metadata": {
            "chunks_retrieved": 2,
            "query_embedding_model": "text-embedding-3-small",
            "retrieval_timestamp": "2026-08-20T12:00:00Z",
            "filters_applied": {"document_ids": ["synthetic-sample-document"]},
        },
        "llm_metadata": {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.0,
            "latency_ms": 1180,
            "prompt_tokens": 812,
            "completion_tokens": 238,
            "total_tokens": 1050,
            "cost_usd": 0.0153,
        },
        "cost": 0.0153,
        "created_at": "2026-08-20T12:00:02Z",
    },
}
