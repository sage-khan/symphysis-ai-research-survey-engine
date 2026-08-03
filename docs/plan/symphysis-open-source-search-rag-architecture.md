# Symphysis: an open-source web search and RAG architecture proposal

Prepared 2026-08-03. A proposal for review, not a finished implementation. Follows the
open-source-by-default rule added to this project's own `.claude/rules/gitops.md`: default to a
fully open-source component end to end, and document the reasoning when one genuinely isn't
viable.

## What this replaces and extends

Symphysis currently has one optional agent tool, `web_search`
(`src/agentic_survey/tools/web_search.py`), built on Tavily, a closed-source, paid API. It
raises `WebSearchError` if `TAVILY_API_KEY` isn't set, which is why the tool has been unusable
in every real survey run this session: no Tavily key exists on the veritas server. Separately,
`rag/retriever.py` is a small, from-scratch retriever (sentence-transformers cosine similarity
when available, a dependency-free TF-IDF fallback otherwise) over local `.txt`/`.md` files,
never a proper vector database, and there is no reranking step anywhere in the pipeline.

## Web search: what was actually researched

**SearXNG.** A free, self-hostable metasearch engine (aggregates results from other search
engines rather than running its own crawler or index) with a JSON API, run via Docker. It needs
the JSON output format explicitly enabled in its settings (disabled by default; only HTML is on
out of the box). Because it's a metasearch aggregator, its own result quality and uptime depend
on the upstream engines it queries, and those upstream engines can throttle or block scraping
traffic, a real operational fragility Tavily's own paid infrastructure absorbs on your behalf.
Its results are search-result-page style: title, URL, and a short snippet, not full page
content, so a second component is needed to fill in `content` the way Tavily's response does.

**Firecrawl.** Genuinely open source (core engine AGPL-3.0, SDKs MIT), with an official
self-hosting guide. The catch: its anti-bot layer (Fire-Engine), the part that actually makes
the hosted product reliable against sites that resist scraping, is not open source. Self-hosted
Firecrawl is real but, by multiple independent sources, operationally harder than the hosted
product specifically because that layer is missing; you're left managing your own proxy pool and
headless-browser fleet. Its AGPL-3.0 license also means any product built on top and served to
users must itself be open-sourced, a real constraint if Symphysis ever offers a hosted version.

**Crawl4AI.** Apache-2.0, actively developed (real, large community by star count and ongoing
releases), local-first, no API keys, and it already outputs clean, LLM-ready Markdown, exactly
the shape RAG pipelines want. Its role is different from SearXNG's: it is a crawler/scraper for
URLs you already have, not a search engine that discovers URLs from a query. It complements a
search backend rather than replacing one.

**Apache Nutch and YaCy.** Both real, both open source, both far bigger commitments than the
others: each builds and maintains its *own* crawl index over time (Nutch pairs with Solr or
Elasticsearch; YaCy is a peer-to-peer network where each node crawls and shares its own index).
Appropriate for a dedicated, narrow, self-controlled search domain (an intranet, a fixed set of
sites), not a drop-in general web search replacement for occasional agent queries. Not
recommended for Symphysis's actual use case (occasional, broad, ad hoc web lookups triggered by
an agent), given the infrastructure and crawl-maturation time both require before they're useful.

**Jina Reader.** Two components under one Apache-2.0 open-source repository
(`jina-ai/reader`): `r.jina.ai` (any URL to clean Markdown, handles JS-rendered pages, PDFs,
Office documents) and `s.jina.ai` (search, which internally fetches and reads the top 5 results
via the same `r.jina.ai` mechanism). The open-source branch was resynced with the production
SaaS codebase in April 2026 and runs in a stateless mode via Docker, no MongoDB dependency,
which is a genuinely current, actively maintained project. The important caveat, confirmed by
reading the repository's own documentation directly rather than assuming: the self-hosted
open-source release documents `r.jina.ai` (content extraction) thoroughly, but does not document
how to self-host `s.jina.ai`'s search step or which search backend it queries under the hood.
Treat Jina Reader as a strong, verified open-source **content-extraction** component
(URL to Markdown), not as a verified self-hostable **search-discovery** component.

## The two-stage pattern this converges on

Every real precedent found (an existing production pattern called "RAG with fallback web," and
a published reference implementation, OpenDeepSearch, which explicitly supports SearXNG as its
search backend with a Jina reranker) splits web search into two distinct stages rather than
looking for one tool that does both:

1. **Discovery**: given a query, find candidate URLs and short snippets. SearXNG's job.
2. **Extraction**: given a URL, fetch and return clean, full page content. Crawl4AI's or Jina
   Reader's `r.jina.ai`'s job.

This is also, functionally, what Tavily itself already does behind one API call; splitting it
into two self-hosted stages is not inventing a new shape, it's unbundling an existing one.

### Recommendation: SearXNG for discovery, Crawl4AI for extraction

Both Apache-licensed-friendly (SearXNG is AGPL-3.0; Crawl4AI is Apache-2.0), both Docker-based,
both under active development. Crawl4AI over Jina Reader's `r.jina.ai` specifically because
Crawl4AI's self-hosting path is fully documented end to end today, while Jina Reader's is
verified-solid for extraction but has an unresolved gap in its own public documentation about
whether its search step can be self-hosted at all, an unnecessary open question when the
discovery stage is already being handled by SearXNG anyway.

### How this fits the existing interface

`web_search.py`'s public surface is `search(query, top_k) -> List[SearchResult]` and
`search_as_dicts(query, top_k) -> List[Dict]`, each dict shaped `{title, url, content}`. Nothing
outside this file (`agent.py`'s `_web_search_chunks`, the instrument prompts, the guardrails)
needs to change if a new implementation preserves that exact shape:

- Query SearXNG's JSON API (`/search?q=...&format=json`) for `top_k` candidate URLs plus their
  titles and snippets.
- For each candidate URL, call Crawl4AI (self-hosted, Docker, its own REST API) to fetch and
  return clean Markdown content.
- Assemble `{title, url, content}` per result and return exactly as `search_as_dicts` does now.
- Raise the same `WebSearchError` (not a silent empty list) if SearXNG or Crawl4AI is
  unreachable or misconfigured, preserving the existing "an agent that can't search should say
  so, never proceed as if it had real results" guarantee already documented in this file today.

## RAG: vector database and reranking

**Qdrant.** Confirmed genuinely open source (Apache-2.0 core, no feature gating between
self-hosted and cloud), written in Rust, official `qdrant/qdrant` Docker image, same HNSW engine
and API whether self-hosted or managed. This is the natural upgrade path for `rag/retriever.py`,
which today re-embeds and re-scores the entire corpus on every single query (fine for the small,
per-agent corpora this app currently ships, not a design that scales past that).

**BGE reranker (BAAI/FlagEmbedding).** Open source, Hugging Face-hosted weights, multiple sizes
(`bge-reranker-base`, `bge-reranker-large`, the newer `bge-reranker-v2-m3` and
`bge-reranker-v2.5-gemma2-lightweight`), runnable via `sentence-transformers` or
`FlagEmbedding` directly. `bge-reranker-v2-m3` is the current recommended general-purpose,
multilingual choice; it is a cross-encoder, meaning it re-scores each (query, candidate) pair
directly rather than comparing pre-computed embeddings, which is exactly what a reranking step
after a fast vector search is for. Cohere's reranker is the closed-source, paid alternative and
is not the open-source-by-default choice per this project's own new rule.

### Where reranking sits in the pipeline

Retrieve a wider top-k from Qdrant (say, top-20) by cheap vector similarity, then rerank that
candidate set down to the actual top-k (say, top-5) the agent receives, using BGE as a
cross-encoder over (query, chunk) pairs. This is the standard "retrieve wide, rerank narrow"
pattern: vector search alone is fast but position-insensitive at the margins; a cross-encoder
reranker is slower per pair but far better at judging genuine relevance, so applying it only to
an already-narrowed candidate set gets both speed and quality.

## Phased rollout (a proposal, not a mandate to build all of this at once)

1. **Fastest, lowest-risk first step**: replace `web_search.py`'s Tavily backend with
   SearXNG (discovery) + Crawl4AI (extraction), behind the exact same `search_as_dicts`
   interface. This alone fixes the concrete, currently-broken problem (no Tavily key exists, so
   the tool is dead weight today) and needs no change anywhere else in the codebase.
2. **Second step, larger scope**: introduce Qdrant as an *optional* backend for
   `rag/retriever.py`, selectable per survey or per agent (a new `rag.backend: "qdrant"` field
   alongside the existing default), rather than replacing the current TF-IDF/sentence-transformers
   retriever outright. The current retriever is genuinely adequate for the small, single-directory
   corpora every survey ships today (the knowledge bases created this session are a handful of
   files each); Qdrant's real value shows up once a corpus grows past what re-embedding on every
   query can comfortably handle, or once corpora need to be shared/queried across surveys rather
   than re-indexed per run.
3. **Third step**: add the BGE reranking step on top of whichever retriever backend is active
   (works with both the existing TF-IDF retriever's top-k and a future Qdrant top-k), since
   reranking is valuable regardless of which vector search step feeds it.

## Deployment implications for the veritas server

- **SearXNG**: one more Docker Compose service, lightweight (no GPU need, modest CPU/RAM), but
  needs its JSON API explicitly enabled in its settings file (off by default) and its own
  container-network access to the public internet (currently a question of what egress this
  server actually allows).
- **Crawl4AI**: Docker-based, uses a real (headless) browser under the hood for JS-rendered
  pages, so budget real CPU and RAM per concurrent crawl, though nothing like the GPU load an
  LLM needs; it explicitly does not need a GPU itself.
- **Qdrant**: Docker-based, CPU-bound for the HNSW index at the scale this project's corpora are
  currently at (a handful of small `.md` files per knowledge base); persistent storage for the
  index needs a volume, same pattern already used for `ollama-models` in `docker-compose.yml`.
- **BGE reranker**: runs via `sentence-transformers`/`FlagEmbedding` in the existing Python
  process (no new service needed); `bge-reranker-base` (278M parameters) is small enough to run
  on CPU for the batch sizes a single agent's retrieval step produces, so it does not need to
  compete with Ollama for the server's already GPU-constrained resources (see the separate
  finding that the RTX 5080 on this server only has 16GB VRAM, already tight for the LLM models
  in active use).

None of the four new components need GPU time. They add CPU, RAM, and disk footprint, not
contention with the LLM inference that already dominates this server's GPU budget.

## Recommendation

Adopt the two-stage SearXNG (discovery) plus Crawl4AI (extraction) pattern for `web_search.py`
as the first, fast, low-risk step: it is a drop-in replacement behind the existing interface,
fixes a tool that is currently non-functional (no Tavily key exists anywhere in this
deployment), and both components are actively maintained, genuinely open source, and
Docker-deployable on the existing server without new GPU demand. Treat Qdrant plus a BGE
reranker as a real, worthwhile, but separate second phase for `rag/retriever.py`, not bundled
into the same change, since the current retriever is not actually broken for today's corpus
sizes, only unable to scale past them.

## Open questions for Dan

- **How much new self-hosting surface area is acceptable right now?** SearXNG plus Crawl4AI is
  two new Docker services on a server that already runs a fairly large stack (Postgres, Neo4j,
  Qdrant already for a different project, OpenSearch, Redis, MinIO, and more, per the earlier
  `docker ps` output from this session). Worth confirming there's appetite for two more before
  building this, versus deferring web search entirely until it's actually needed for a real
  survey run.
- **Does this server's network egress policy allow SearXNG to reach the public search engines
  it aggregates?** Not something that can be verified without checking the server's actual
  firewall/proxy configuration.
- **Is Qdrant already running on this server for another project** (it's mentioned as already
  in use for `project-veritas` elsewhere in this session's own context) **and, if so, should
  Symphysis share that same instance** (a new collection in the existing Qdrant) **or run its
  own separate instance?** Sharing reduces new footprint; a separate instance avoids any
  cross-project coupling or accidental collection-name collision.
- **Is the phased rollout's ordering right for Dan's actual priorities**, or does the RAG/Qdrant
  side matter more right now than fixing the currently-dead web-search tool?
