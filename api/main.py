from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from neo4j import GraphDatabase
import os, random

class Person(BaseModel):
    name: str
    age: int

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

RANDOM_NAMES = ["Alice","Bob","Charlie","Diana","Edward","Fiona","George","Hannah",
                "Isaac","Julia","Kevin","Laura","Michael","Nina","Oscar","Penny",
                "Quinn","Rachel","Samuel","Tina","Ulysses","Victoria","William","Xara",
                "Yasmin","Zachary"]

app = FastAPI()

def run_query(query: str, **params):
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
    )
    try:
        with driver.session() as session:
            return list(session.run(query, **params))
    finally:
        driver.close()

@app.post("/persons", response_model=Person)
def create_person():
    name = random.choice(RANDOM_NAMES)
    age = random.randint(18, 80)
    try:
        records = run_query(
            "CREATE (p:Person {name:$name, age:$age}) "
            "RETURN p.name AS name, p.age AS age",
            name=name, age=age
        )
        rec = records[0] if records else None
        if not rec:
            raise HTTPException(status_code=500, detail="Failed to create person")
        return Person(name=rec["name"], age=rec["age"])
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e}")

@app.get("/persons", response_model=List[Person])
def list_persons():
    try:
        records = run_query("MATCH (p:Person) RETURN p.name AS name, p.age AS age")
        return [Person(name=r["name"], age=r["age"]) for r in records]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e}")

@app.get("/health")
def health_check():
    try:
        _ = run_query("RETURN 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
