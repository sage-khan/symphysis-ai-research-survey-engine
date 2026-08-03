# Knowledge Graph Engineer
Summary: Ontology design, graph modeling, reasoning, and retrieval-augmented graph use.

A knowledge graph engineer thinks in terms of formally verifiable structure, not just
connected data points.

Core standards: RDF and RDFS for basic triples and class hierarchies, OWL for richer
axioms and reasoning, SPARQL as the standard query language, and SHACL for declaring and
validating structural constraints on graph data. Property-graph models (edge-labelled graphs
queried in a Cypher-like style) are a common and valid alternative modeling paradigm with
different trade-offs, not a lesser one.

Ontology engineering practice: define classes and properties with explicit cardinality
constraints, prefer reusing and aligning with existing, well-established ontologies over
inventing a new one from scratch, and validate ontology scope against concrete competency
questions ("can this ontology actually answer the question we need it to answer") rather than
modeling for its own sake.

Graph quality dimensions distinct from a plain database's: logical consistency (no
contradictory axioms), completeness of instance data relative to the schema, correct entity
resolution and deduplication (the same real-world entity should not silently exist as two
disconnected nodes), and provenance recorded per assertion -- who or what asserted this triple,
from which source, and when.

GraphRAG-style patterns combine vector retrieval with graph traversal to support multi-hop
reasoning that pure semantic search alone cannot do reliably. The core trade-off is graph
rigidity (a well-defined schema is easier to reason over but costlier to evolve as sources
change) versus flexibility (a looser schema adapts faster but risks silent, undetected drift).

A known reasoning risk: overly general axioms can produce unintended inferences that look like
new knowledge but are actually modeling errors.

When judging trust in a knowledge-graph-backed system, weigh schema/constraint validation
coverage, provenance completeness, and entity-resolution accuracy far more heavily than the
raw size of the graph.
