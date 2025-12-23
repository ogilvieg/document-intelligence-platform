"""Demo script to visualize chunking behavior."""

import sys
sys.path.append('/Users/gawaineogilvie/GitRepos/document-intelligence-platform/backend')

from uuid import uuid4
from app.services.chunking import ChunkingService

def print_separator():
    print("\n" + "="*80 + "\n")

# Initialize chunking service
service = ChunkingService(chunk_size=150, chunk_overlap=30)

# Sample text
text = """
The Document Intelligence Platform is an advanced system for analyzing documents.
It uses state-of-the-art AI models to extract insights from PDF, Markdown, and HTML files.

The system works in three phases. First, documents are ingested and parsed.
Second, they are chunked into manageable segments. Third, each chunk is analyzed.

Chunking is critical for processing large documents. By breaking text into smaller pieces,
we can maintain context while staying within model token limits. The overlap between
chunks ensures that no information is lost at boundaries.

This intelligent chunking strategy balances efficiency with quality. Sentence-aware
breaking produces more coherent chunks. The system can handle various document formats
and sizes, making it versatile for different use cases.
""".strip()

print("🔍 CHUNKING DEMONSTRATION")
print_separator()
print(f"📄 Original Text Length: {len(text)} characters")
print(f"⚙️  Chunk Size: {service.chunk_size} chars")
print(f"🔗 Overlap: {service.chunk_overlap} chars")
print_separator()

# Chunk the text
document_id = uuid4()
result = service.chunk_document(text, document_id)

print(f"📊 Chunking Results:")
print(f"   Total Chunks: {result['total_chunks']}")
print(f"   Average Size: {result['average_chunk_size']:.1f} chars")
print_separator()

# Display each chunk
for i, chunk in enumerate(result['chunks'], 1):
    print(f"📦 CHUNK {i} (Index: {chunk['chunk_index']})")
    print(f"   Position: {chunk['start_char']}-{chunk['end_char']}")
    print(f"   Length: {len(chunk['text'])} chars")
    print(f"\n   Text:\n   {chunk['text'][:200]}...")
    
    # Show overlap with next chunk
    if i < len(result['chunks']):
        next_chunk = result['chunks'][i]
        overlap_text = chunk['text'][-30:]
        if overlap_text in next_chunk['text']:
            print(f"\n   ✓ Overlap detected with next chunk")
            print(f"   Overlapping text: '...{overlap_text}...'")
    
    print_separator()

# Validation
validation = service.validate_chunks(result['chunks'])
print("✅ VALIDATION REPORT")
print(f"   Valid: {validation['valid']}")
print(f"   Warnings: {len(validation['warnings'])}")
if validation['warnings']:
    for warning in validation['warnings']:
        print(f"   ⚠️  {warning}")

print(f"\n📈 Statistics:")
for key, value in validation['statistics'].items():
    if isinstance(value, float):
        print(f"   {key}: {value:.1f}")
    else:
        print(f"   {key}: {value}")

print_separator()
print("✨ Demo complete!")
