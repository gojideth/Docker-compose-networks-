from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase
from typing import List
import os
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Person(BaseModel):
    name: str
    age: int

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://172.17.0.3:7687")  # Default bridge network IP
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

logger.info(f"Attempting to connect to Neo4j at: {NEO4J_URI}")

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    # Test the connection
    with driver.session() as session:
        session.run("RETURN 1")
    logger.info("Successfully connected to Neo4j")
except Exception as e:
    logger.error(f"Failed to connect to Neo4j: {e}")
    driver = None

# List of random names for generating persons
RANDOM_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah",
    "Isaac", "Julia", "Kevin", "Laura", "Michael", "Nina", "Oscar", "Penny",
    "Quinn", "Rachel", "Samuel", "Tina", "Ulysses", "Victoria", "William", "Xara",
    "Yasmin", "Zachary"
]

app = FastAPI()

@app.post("/persons", response_model=Person)
def create_person():
    if driver is None:
        raise HTTPException(status_code=503, detail="Database connection not available. Check network configuration.")

    # Generate random name and age
    random_name = random.choice(RANDOM_NAMES)
    random_age = random.randint(18, 80)

    try:
        with driver.session() as session:
            result = session.run(
                "CREATE (p:Person {name: $name, age: $age}) RETURN p.name AS name, p.age AS age",
                name=random_name,
                age=random_age
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create person")
            return Person(name=record["name"], age=record["age"])
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.get("/persons", response_model=List[Person])
def list_persons():
    if driver is None:
        raise HTTPException(status_code=503, detail="Database connection not available. Check network configuration.")

    try:
        with driver.session() as session:
            result = session.run("MATCH (p:Person) RETURN p.name AS name, p.age AS age")
            persons = [Person(name=record["name"], age=record["age"]) for record in result]
            return persons
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.get("/health")
def health_check():
    if driver is None:
        return {"status": "unhealthy", "database": "disconnected", "message": "Cannot connect to Neo4j database"}

    try:
        with driver.session() as session:
            session.run("RETURN 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
