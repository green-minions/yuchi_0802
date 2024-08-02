import pandas as pd
from neo4j import GraphDatabase
import time
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
NEO4J_URI = "neo4j://localhost" 
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "vincent920622" 
NEO4J_DATABASE = "neo4j"
graph = Neo4jGraph()
llm = ChatOpenAI(temperature=0, model_name="gpt-4o")

kg_transformer = LLMGraphTransformer( llm=llm,
  allowed_nodes=["Person", "Country", "Company"],
  allowed_relationships=["LOCATED_IN","WORKED_AT"])
documents = "./test.txt"
results = kg_transformer.convert_to_graph_documents(documents)
graph.add_graph_documents(results)
