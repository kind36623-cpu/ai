from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
import logging
import uuid
import time

logger = logging.getLogger(__name__)

class MemoryGraph:
    def __init__(self):
        self.is_enabled = bool(settings.pinecone_api_key)
        self.index = None
        self._encoder = None  # Lazy-loaded on first use
        self.pc = None

        if self.is_enabled:
            try:
                self.pc = Pinecone(api_key=settings.pinecone_api_key)
                self.index_name = settings.pinecone_index_name

                # Check if index exists, create if not
                existing = [i["name"] for i in self.pc.list_indexes()]
                if self.index_name not in existing:
                    logger.info(f"Creating new Pinecone index: {self.index_name}")
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=384,
                        metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1")
                    )
                    while not self.pc.describe_index(self.index_name).status["ready"]:
                        time.sleep(1)

                self.index = self.pc.Index(self.index_name)
                logger.info("Memory Graph (Pinecone) connected. Encoder will load on first use.")

            except Exception as e:
                logger.error(f"Failed to initialize Pinecone: {e}")
                self.is_enabled = False

    def _get_encoder(self):
        """Lazy-load the embedding model only when first needed."""
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model ready.")
        return self._encoder

    def store_memory(self, text: str, source: str = "conversation", trust_score: int = 80):
        """Layer 5.1: Node Creation"""
        if not self.is_enabled:
            return
        try:
            encoder = self._get_encoder()
            vector = encoder.encode(text).tolist()
            node_id = f"node_{uuid.uuid4()}"
            metadata = {
                "content": text,
                "source": source,
                "trust_score": trust_score,
                "timestamp": time.time(),
                "access_count": 0
            }
            self.index.upsert(vectors=[(node_id, vector, metadata)])
            logger.info(f"Stored memory node: {node_id}")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")

    def retrieve_memories(self, query: str, top_k: int = 5) -> str:
        """Layer 5.4: Memory Retrieval"""
        if not self.is_enabled:
            return ""
        try:
            encoder = self._get_encoder()
            query_vector = encoder.encode(query).tolist()
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )
            if not results.matches:
                return ""
            memory_strings = []
            for match in results.matches:
                content = match.metadata.get("content", "")
                score = match.score
                if score > 0.3:
                    memory_strings.append(f"- {content} (Relevance: {score:.2f})")
            return "\n".join(memory_strings) if memory_strings else ""
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return ""

# Global Instance
memory_graph = MemoryGraph()
