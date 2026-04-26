import uuid
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType

COLLECTION_NAME = "aegis_policies"
EMBEDDING_DIM = 3072

def create_payload_indexes(qdrant: QdrantClient):
    qdrant.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="policy_category",
        field_schema=PayloadSchemaType.KEYWORD
    )
    qdrant.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="effective_date",
        field_schema=PayloadSchemaType.KEYWORD
    )
    qdrant.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="document_id",
        field_schema=PayloadSchemaType.KEYWORD
    )
    print("Payload indexes created ✅")

def get_embedding(text: str, client: OpenAI) -> list:
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return response.data[0].embedding

def get_embeddings_batch(texts: list, client: OpenAI) -> list:
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=texts
    )
    return [item.embedding for item in response.data]

def setup_qdrant_collection(qdrant: QdrantClient):
    existing = [c.name for c in qdrant.get_collections().collections]

    if COLLECTION_NAME in existing:
        qdrant.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")

    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE
        )
    )
    print(f"Created collection: {COLLECTION_NAME}")

def upsert_chunks_batch(tagged_chunks: list, openai_client: OpenAI, qdrant: QdrantClient):
    points = []
    embed_batch_size = 50   # OpenAI — 50 texts per API call
    upsert_batch_size = 25  # Qdrant Cloud — 25 points per API call

    # Embedding loop
    for i in range(0, len(tagged_chunks), embed_batch_size):
        batch_chunks = tagged_chunks[i : i + embed_batch_size]
        texts = [chunk["content"] for chunk in batch_chunks]
        vectors = get_embeddings_batch(texts, openai_client)

        for chunk, vector in zip(batch_chunks, vectors):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "chunk_text": chunk["content"],
                    **chunk["metadata"]
                }
            )
            points.append(point)

        print(f"Embedded batch {i//embed_batch_size + 1}: {len(batch_chunks)} chunks")

    # Upsert loop
    for i in range(0, len(points), upsert_batch_size):
        batch = points[i : i + upsert_batch_size]
        qdrant.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(f"Upserted batch {i//upsert_batch_size + 1}: {len(batch)} chunks")

    print(f"Total upserted: {len(points)} chunks")