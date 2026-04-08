from neo4j import GraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sonar_local")

class Neo4jConnection:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def close(self):
        self._driver.close()

    def session(self):
        return self._driver.session()

    def verify(self):
        self._driver.verify_connectivity()
        print("Neo4j connection verified.")

db = Neo4jConnection()