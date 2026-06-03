from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from app.core.config import settings
import logging
import uuid
import time

logger = logging.getLogger(__name__)

class MemoryGraph:
    def __init__(self):
        self.is_enabled = bool(settings.pinecone_api_key)
        self.index = None
        self.encoder = None

        if self.is_enabled:
            try:
                # Initialize Pinecone
                self.pc = Pinecone(api_key=settings.pinecone_api_key)
                self.index_name = settings.pinecone_index_name
                
                # Check if index exists, create if it doesn't
                # Using 384 dimensions because we are using all-MiniLM-L6-v2 for free local embeddings
                if self.index_name not in [index_info["name"] for index_info in self.pc.list_indexes()]:
                    logger.info(f"Creating new Pinecone index: {self.index_name}")
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=384,
                        metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1")
                    )
                    # Wait for index to be ready
                    while not self.pc.describe_index(self.index_name).status['ready']:
                        time.sleep(1)

                self.index = self.pc.Index(self.index_name)
                
                # Initialize Local Embedding Model
                logger.info("Loading local embedding model (all-MiniLM-L6-v2)...")
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Memory Graph (Pinecone) initialized successfully.")
                
            except Exception as e:
                logger.error(f"Failed to initialize Pinecone: {e}")
                self.is_enabled = False

    def store_memory(self, text: str, source: str = "conversation", trust_score: int = 80):
        """Layer 5.1: Node Creation Function"""
        if not self.is_enabled:
            return

        try:
            # 1. Generate Vector Embedding
            vector = self.encoder.encode(text).tolist()
            
            # 2. Generate unique Node ID
            node_id = f"node_{uuid.uuid4()}"
            
            # 3. Store in Pinecone with metadata
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
        """Layer 5.4: Memory Retrieval Function"""
        if not self.is_enabled:
            return ""

        try:
            # 1. Generate Vector for Query
            query_vector = self.encoder.encode(query).tolist()
            
            # 2. Search Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )
            
            if not results.matches:
                return ""
                
            # 3. Format memories for Context Builder
            memory_strings = []
            for match in results.matches:
                content = match.metadata.get("content", "")
                score = match.score
                if score > 0.3:  # Only include relevant memories
                    memory_strings.append(f"- {content} (Relevance: {score:.2f})")
                    
            if memory_strings:
                return "\n".join(memory_strings)
            return ""
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return ""

# Global Instance
memory_graph = MemoryGraph()
