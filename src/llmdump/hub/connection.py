"""Neo4j connection management."""

from typing import Optional
from neo4j import GraphDatabase, Driver
import os
import logging

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Manages Neo4j database connections."""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j URI (defaults to NEO4J_URI env var)
            user: Neo4j username (defaults to NEO4J_USER env var)
            password: Neo4j password (defaults to NEO4J_PASSWORD env var)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        
        self.driver: Optional[Driver] = None
    
    def connect(self) -> Driver:
        """Establish connection to Neo4j."""
        if self.driver is None:
            logger.info(f"Connecting to Neo4j at {self.uri}")
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
        return self.driver
    
    def close(self):
        """Close connection."""
        if self.driver:
            logger.info("Closing Neo4j connection")
            self.driver.close()
            self.driver = None
    
    def verify_connectivity(self) -> bool:
        """Verify connection to Neo4j."""
        try:
            driver = self.connect()
            driver.verify_connectivity()
            logger.info("Neo4j connection verified")
            return True
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


__all__ = ['Neo4jConnection']
