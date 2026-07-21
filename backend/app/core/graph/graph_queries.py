"""Cypher query library for Neo4j. All raw Cypher lives here."""


class GraphQueries:
    GET_ALL_NODES = """
        MATCH (n {repo_id: $repo_id})
        RETURN n, labels(n) AS labels
        LIMIT 1000
    """
    GET_ALL_RELATIONSHIPS = """
        MATCH (a {repo_id: $repo_id})-[r]->(b {repo_id: $repo_id})
        RETURN id(r) AS rel_id, a.id AS source_id, b.id AS target_id,
               type(r) AS rel_type, properties(r) AS rel_props
        LIMIT 2000
    """
    GET_NODE_WITH_NEIGHBORS = """
        MATCH (n {id: $node_id})
        OPTIONAL MATCH (n)-[out_edge]->(neighbor_out)
        OPTIONAL MATCH (neighbor_in)-[in_edge]->(n)
        RETURN n, labels(n) AS node_labels,
               collect(DISTINCT {rel: type(out_edge), node: neighbor_out, labels: labels(neighbor_out)}) AS outgoing,
               collect(DISTINCT {rel: type(in_edge), node: neighbor_in, labels: labels(neighbor_in)}) AS incoming
    """
    FIND_CIRCULAR_DEPS = """
        MATCH path = (start {repo_id: $repo_id})-[:IMPORTS|DEPENDS_ON*2..10]->(start)
        WITH [node IN nodes(path) | node.name] AS cycle_names
        WHERE ALL(name IN cycle_names WHERE name IS NOT NULL)
        RETURN cycle_names AS cycle
        LIMIT 20
    """
    FIND_HIGHLY_COUPLED = """
        MATCH (n {repo_id: $repo_id})-[r]-()
        WITH n, count(r) AS degree, labels(n) AS node_labels
        WHERE degree > $threshold
        RETURN n.id AS id, n.name AS name, degree, node_labels
        ORDER BY degree DESC
        LIMIT 50
    """
    FIND_DEAD_MODULES = """
        MATCH (m:Module {repo_id: $repo_id})
        WHERE NOT ()-[:IMPORTS|DEPENDS_ON|CALLS]->(m)
        AND NOT (m)<-[:CONTAINS]-(:Repository {repo_id: $repo_id})
        RETURN m.id AS id, m.name AS name
        LIMIT 100
    """
    DELETE_REPO_GRAPH = """
        MATCH (n {repo_id: $repo_id}) DETACH DELETE n
    """
