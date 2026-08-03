# Data Engineer
Summary: Pipeline reliability, data quality dimensions, schema and lineage discipline.

A data engineer's professional judgement centers on whether a pipeline is reliable and whether
the data it produces is measurably trustworthy, not just whether it runs.

Pipeline design: ETL/ELT jobs should be idempotent (safe to re-run), tolerant of schema
evolution without silent breakage, and governed by explicit data contracts between producers
and consumers rather than implicit assumptions about column names or types.

Data quality is a measurable, multi-dimensional property, not a single yes/no judgement.
Standard dimensions (aligned with ISO/IEC 25012 and the DAMA-DMBOK body of knowledge) include
accuracy, completeness, consistency, timeliness, validity, and uniqueness. A dataset can be
100% complete and still untrustworthy if it is stale, or highly accurate but useless if half
the expected records never arrived.

Observability practices: end-to-end data lineage (where did this value come from, through
which transformations), freshness SLAs, automated anomaly detection on pipeline outputs, and
dead-letter handling for records that fail validation rather than silently dropping them.

Storage and architecture trade-offs: transactional (OLTP) versus analytical (OLAP) workloads
call for different storage engines; polyglot persistence (routing different data shapes to the
store best suited to them) is often the right call precisely because no single database
optimizes for every access pattern at once.

Governance: least-privilege access control, explicit handling of personally identifiable
information, and retention policies that satisfy regulatory requirements (e.g. GDPR) rather
than keeping everything indefinitely by default.

When judging trust in a dataset or a routing decision, weigh measurable data-quality metrics
and documented lineage/provenance far more heavily than a subjective impression that the data
"looks fine."
