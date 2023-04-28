import networkx as nx
import sqlalchemy
from sqlalchemy import MetaData, text
from sqlalchemy.schema import ForeignKeyConstraint
from testcontainers.mysql import MySqlContainer


def sql_to_graph(schema):
    with MySqlContainer("mysql:8.0") as mysql:
        metadata = MetaData()
        engine = sqlalchemy.create_engine(mysql.get_connection_url())
        # Split the schema into individual statements
        sql_statements = schema.strip().split(";")
        sql_statements = [stmt.strip() for stmt in sql_statements if stmt.strip()]

        with engine.connect() as conn:
            for statement in sql_statements:
                conn.execute(text(statement))

        metadata.reflect(bind=engine)

        G = nx.DiGraph()

        for table in metadata.tables.values():
            G.add_node(table.name, type="table")

            for column in table.columns:
                column_node = f"{table.name}_{column.name}"
                G.add_node(
                    column_node,
                    type="column",
                    data_type=str(column.type),
                    constraints=str(column.constraints),
                )
                G.add_edge(table.name, column_node)

            for constraint in table.constraints:
                if isinstance(constraint, ForeignKeyConstraint):
                    for fk_element in constraint.elements:
                        col = fk_element.parent
                        ref_col = fk_element.column
                        G.add_edge(
                            f"{table.name}_{col.name}",
                            f"{ref_col.table.name}_{ref_col.name}",
                            relationship="foreign_key",
                        )

        return G


def get_sub_graph(G, node, level=1):
    """
    Get a subgraph of `G` containing all nodes within the specified `level` of `node`.

    Args:
        G (networkx.Graph): The graph to extract the subgraph from.
        node (hashable): The node to start extracting the subgraph from.
        level (int): The number of levels of neighbors to include in the subgraph (default 1).

    Returns:
        networkx.Graph: A subgraph of `G` containing all nodes within the specified `level` of `node`.
    """
    # Get connected nodes within the specified level
    connected_nodes = set()  # type: set[str]
    for i in range(level + 1):
        # Expand the connected nodes set using neighbors
        neighbors = set().union(*(nx.neighbors(G, n) for n in connected_nodes | {node}))
        connected_nodes |= neighbors

    # Create a subgraph with the connected nodes
    subgraph = G.subgraph(connected_nodes).copy()
    return subgraph


def load(x):
    with open(x) as f:
        ret = f.read()
    return ret


# Read the file /tests/schema/ed.sql
sql_string = load("/Users/chakshugautam/Experiments/sql-graph/tests/schemas/ed.sql")


G = sql_to_graph(sql_string)
nx.draw(G)
PG = nx.nx_pydot.to_pydot(G)

# Save the PyDot graph as a PNG image
PG.write_png("graph.png")
