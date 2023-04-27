import networkx as nx

# Initialize the graph
G = nx.DiGraph()

# Add tables and columns as nodes
G.add_node("table1", type="table")
G.add_node("table1_column1", type="column", data_type="integer", constraints="...")
G.add_node("table1_column2", type="column", data_type="varchar", constraints="...")
G.add_node("table2", type="table")
G.add_node("table2_column1", type="column", data_type="integer", constraints="...")

# Add relationships (edges)
G.add_edge("table1", "table1_column1")
G.add_edge("table1", "table1_column2")
G.add_edge("table2", "table2_column1")
G.add_edge("table1_column1", "table2_column1", relationship="foreign_key")