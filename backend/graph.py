# backend/graph.py
from langgraph import Graph, TaskNode
from extractor import extractor_agent
from dictionary_agent import dictionary_agent
from analyst_agent import analyst_agent
from query_runner import query_runner_agent

# 1. Define TaskNodes for each agent
extractor_node = TaskNode(
    name="extractor",
    func=extractor_agent,
    inputs=["table_name"],       # expects table_name
    outputs=[]
)

dictionary_node = TaskNode(
    name="dictionary_writer",
    func=dictionary_agent,
    inputs=["table_name"],
    outputs=[]
)

analyst_node = TaskNode(
    name="analyst",
    func=analyst_agent,
    inputs=["table_name"],
    outputs=[]
)

# Query Runner is event‐driven; will be triggered separately
query_runner_node = TaskNode(
    name="query_runner",
    func=query_runner_agent,
    inputs=["nl_query", "user"],
    outputs=["sql", "data"]
)

# 2. Build the ingestion subgraph: extractor → dictionary_writer → analyst
graph = Graph()
graph.add_node(extractor_node)
graph.add_node(dictionary_node)
graph.add_node(analyst_node)
graph.add_node(query_runner_node)

# Define dependencies: dictionary waits for extractor; analyst waits for dictionary
graph.set_dependency(parent="extractor", child="dictionary_writer")
graph.set_dependency(parent="dictionary_writer", child="analyst")

# Query_runner_node is not dependent on ingestion; it's run on‐demand
# We don't set dependencies for it in the initial pipeline.

# Now `graph.run()` can be called with different entrypoints:
#   • ingestion: pass {"table_name": "foo"} to extractor→dictionary→analyst
#   • NL query: pass {"nl_query": "...", "user": "bob"} to query_runner
