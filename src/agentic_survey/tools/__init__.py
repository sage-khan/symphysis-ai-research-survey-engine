"""Real, callable tools an Agent Card can grant to an agent (via its
`tools: [...]` list), beyond RAG over a static corpus: currently
`web_search`. Each tool module exposes a plain function that either
returns real results or raises a clear error -- nothing here ever
fabricates a plausible-looking result when the underlying service is
unavailable or unconfigured."""
