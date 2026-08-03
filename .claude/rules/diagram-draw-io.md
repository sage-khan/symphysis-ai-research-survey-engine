---
trigger: always_on
---

# Diagram Handling Rules . draw.io / diagrams.net Files  
`diagramming-draw.io-md`

These rules define safe, deterministic, and failure-resistant handling of diagram files created with **draw.io / diagrams.net**, especially large or complex diagrams. The goals are correctness, reversibility, structural integrity, and predictable rendering.

**File location in this repo:** every `.drawio` source and its current PNG/SVG export live
together in `docs/architecture/` (see `architecture-overview.md` in that same directory for
what each diagram covers). A diagram embedded in a specific paper this project's own research
also cites (for example a TrustRouter/BSI figure) instead follows that paper's own working
directory convention (a `figures/` subfolder next to the `.tex` source, build artifacts in
`extra/`), documented in `project-veritas`'s `software-directory-structure-guide.md`.

---

## What draw.io Files Are

- `.draw.io` files are **text-based XML documents**.
- They typically contain:
  - An `<mxfile>` root element
  - One or more `<diagram>` elements
  - Embedded **mxGraphModel** XML
- Files may be:
  - Plain XML
  - Compressed XML (base64 + deflate) when exported in certain modes

Important constraints:
- draw.io files are **data structures**, not free-form markup.
- Small structural errors will break rendering.
- Ordering, IDs, and attributes are critical.

Agents MUST treat draw.io files as **structured data**, not prose.

---

## Supported File Variants

Agents MUST detect the file variant before editing:

- Plain XML draw.io file
- Compressed draw.io file (base64 + deflate)
- Embedded draw.io XML inside another container

If compression is detected:
- Decompress to plain XML in a temporary directory
- Operate only on the decompressed form
- Recompress only after validation

---

## When to Use draw.io

Agents SHOULD create or modify `.draw.io` files when:
- A workflow, architecture, dependency graph, or system diagram is required
- Visual structure is more expressive than text
- The user explicitly requests a diagram

Agents MUST NOT replace diagrams with text unless explicitly instructed.

---

## Diagrams Show Concepts, Not Prose (mandatory scope limit)

A `.drawio` diagram used in a Symphysis architecture document, paper, or report is a **concept,
flowchart, or architecture diagram**: boxes, short labels, and arrows that show structure and
relationships. It is not a place to write sentences. Two specific text elements are forbidden on
the canvas itself:

1. **No embedded title.** Do not draw the figure's title, headline, or "what this figure shows"
   statement as a text node on the canvas (e.g. a large heading like "A governed data platform
   emerges where four literatures meet" sitting above the boxes). The title lives in the LaTeX
   `\caption{}`, not on the diagram. A diagram with a title baked in cannot be recaptioned,
   resized into a different section, or reused without re-editing the source image.
2. **No narrative, finding, or gap sentences.** Do not draw a full sentence stating a result,
   a limitation, or a research gap as a banner/callout inside the diagram (e.g. "No surveyed
   system treats these four literatures as one integrated, governed stack — that connective
   governance is this survey's research agenda"). That is argument, and argument belongs in the
   paper's prose paragraphs, not inside a figure. A diagram node label may name a concept
   ("Digital Trust & Provenance — the governance spine") but must not make a claim about the
   literature or the field.

**Why:** caught in P12 (`Towards-Trust-First-Agentic-Data-Operations-survey.tex`, fig5/digital-trust-pipeline) on
2026-07-26 — a diagram had grown a drawn title and a drawn gap-statement banner, duplicating
what the caption and body text already said, and reading as filler rather than a genuine concept
diagram. Reviewers judge a figure on whether the diagram itself teaches the structure at a
glance; a diagram that instead argues a thesis in its own text boxes reads as padding.

**How to apply:** when building or reviewing a `.drawio` diagram, the only text that belongs on
the canvas is: box/node labels naming a concept, component, or step; arrow labels naming a
relationship or transition; and, where genuinely useful, a short subsection/section-number tag
(e.g. "§2"). If a text element you're about to add states a fact about what the survey found, or
introduces/summarizes the figure, delete it from the canvas and put it in the caption or the
narrative paragraph around the figure instead — see this repo's `figures-and-tables-for-papers`
skill for the matching caption-brevity rule.

---

## Color Contrast: a Deliberate, Semantic Palette (not drawio's default swatches)

Copying draw.io's stock shape-picker swatches (its default light-blue `#dae8fc`/`#6c8ebf` and
light-yellow `#fff2cc`/`#d6b656` pairs) node after node produces a diagram where every box reads
as roughly the same washed-out pastel, and where fill/stroke/text were never chosen as a matched
set. Adopt this repo's own house palette instead (sourced from a working, repeatedly-used
diagram-generation script, `ec-council/2-netops-demystified/slides/scripts/make_diagrams.py`),
built around three semantic roles, each a matched fill/stroke/text triplet rather than a single
color reused everywhere:

```
NAVY  = "#1F4E79"   # strong neutral: headers, primary flow boxes, key arrows
L     = "#DDEBF7"   # lightest blue fill (low-emphasis / background-role boxes)
M     = "#BDD7EE"   # mid blue fill (standard boxes)
D     = "#9DC3E6"   # darker blue fill (emphasis boxes, still on the neutral hue)

# "Good" / positive-state role
GFILL, GSTK, GTXT = "#E2EFDA", "#538135", "#375623"

# "Warning" / legacy / attention-needed role
RFILL, RSTK, RTXT = "#FCE4D6", "#C55A11", "#833C00"
```

Rules for using this palette:

- **Pick the text color to match the fill's brightness, never default to plain black
  everywhere.** On a light fill (`L`, `M`, `GFILL`, `RFILL`), use that role's own darker text
  color (`GTXT` on `GFILL`, `RTXT` on `RFILL`; `NAVY` itself reads well on `L`/`M`). On a
  strongly saturated, dark fill (`NAVY`, `D` at full saturation, `GSTK`/`RSTK` used as a fill
  rather than a stroke), use white (`#FFFFFF`) text, not a dark color that will vanish.
- **Reserve `GFILL`/`GSTK`/`GTXT` and `RFILL`/`RSTK`/`RTXT` for their semantic meaning**
  (working correctly / needs attention, current / legacy, passing / failing) so a reader learns
  "green triplet always means the same kind of thing" across every diagram in this project,
  rather than color being decorative and inconsistent between figures.
- **Use the stroke color, not just the fill, to carry contrast.** A stroke one or two shades
  darker than its own fill (as every triplet above already is) keeps boxes visually distinct
  from the page background and from each other even in grayscale printing, where fill hue alone
  collapses.
- **Never rely on hue alone to distinguish two box types** if the diagram might be printed or
  viewed in grayscale (a real risk for a paper figure): the fill-vs-stroke lightness difference
  within each triplet above already provides a non-hue cue: preserve it rather than flattening
  every box to the same flat fill with only a thin, barely-different-toned border.

## Arrow Routing Must Not Cross Box Interiors or Tangle With Other Edges

A real, repeated defect: orthogonal-routed edges left to draw.io's automatic path calculation,
or given no explicit waypoints at all, can end up crossing straight through an unrelated shape's
interior, or several edges can converge on nearly the same corridor and visually merge into an
ambiguous tangle.

- **When 2+ edges must travel through the same general area** (several arrows converging on one
  node, or an edge whose straight path would pass behind an unrelated box sitting between its
  endpoints), give each edge **explicit, distinctly-separated waypoints** via a child
  `<Array as="points"><mxPoint x="…" y="…"/>…</Array>` inside its `<mxGeometry>`, rather than
  relying on `exitX`/`exitY`/`entryX`/`entryY` alone to keep them apart.
- **Check every edge whose straight-line source-to-target path would pass near or through a
  THIRD shape that is neither its source nor its target.** This is easy to miss by reading
  coordinates alone; render the diagram and look.
- **This must be checked by rendering, not by reasoning about coordinates on paper.** Export,
  view the actual image, and only then decide the routing is clean.

---

## Rules for Creating draw.io Files

When generating new `.draw.io` files:

- Always produce **valid mxGraph XML**
- Include:
  - `<mxfile>` root
  - At least one `<diagram>` element
  - `<mxGraphModel>` with required attributes
- Use deterministic IDs
- Maintain consistent layout geometry

### Mandatory escaping rule for multi-line / rich-text cell labels (`html=1`)

A cell with `style="...html=1..."` renders its `value` attribute as HTML, not plain text.
This has two consequences that cause real, hard-to-spot rendering bugs if ignored (hit and
fixed in `p12-theme-architecture.drawio`, 20 Jul 2026):

1. **A literal `\n` inside the value collapses to nothing** (standard HTML whitespace
   collapsing) — multi-line "bulleted" content written with plain newlines will silently
   render as one run-on line with a large empty area below it, not multiple lines. To force
   an actual line break, use `<b>`/`<br>` tags — but written **XML-single-escaped**
   (`&lt;b&gt;`, `&lt;/b&gt;`, `&lt;br&gt;`) so that XML parsing decodes them back to literal
   `<b>`/`<br>` characters, which drawio's HTML rendering layer then interprets as real tags.
   Writing the tags as raw, unescaped `<br>` in the XML attribute is **invalid XML** (a bare
   `<` inside an attribute value) and will fail to parse entirely.
2. **A literal `&` in ordinary label text must be double-escaped** (`&amp;amp;`), not
   single-escaped (`&amp;`) — the XML parser's one unescape pass turns `&amp;amp;` into
   `&amp;`, and drawio's HTML-render layer's second unescape pass turns that into a literal
   `&` on screen. Single-escaping only survives the XML pass and displays as the literal text
   `&amp;`, not `&`.

Practical pattern for a script generating many labelled boxes: keep one helper that
XML-escapes plain text content (`&`→`&amp;`, `<`/`>`→`&lt;`/`&gt;`, `"`→`&quot;`, for
non-`html=1` cells or attribute-safety generally) and a second helper for `html=1` cell
bodies that (a) escapes user text with the double-`&` rule above, and (b) joins lines with
the literal string `&lt;br&gt;` (typed directly in code, never passed through the plain-text
escaper a second time). Validate the resulting file with `xml.etree.ElementTree.parse()`
before rendering — a raw unescaped `<`/`>` inside an attribute value fails XML parsing
immediately, which is the fastest way to catch this class of mistake.

Agents MUST:
- Prefer simple shapes and connectors
- Avoid unnecessary styling
- Ensure all elements are visible within the canvas bounds

---

## Rules for Editing draw.io Files

### Pre-edit Analysis

Before editing:
- Validate XML well-formedness
- Identify:
  - Number of diagrams
  - Total line count
  - Compression state
- Back up the original file

Agents MUST NOT:
- Reformat XML arbitrarily
- Change IDs unless required
- Reorder nodes without intent

---

## Large draw.io File Handling

Large draw.io files are fragile and prone to corruption if edited monolithically.

### Chunking Rules

If a draw.io file exceeds safe thresholds (line count or size):

1. Create a temporary workspace:
   - `/tmp/windsurf/<operation-id>/`
2. Split the XML into **logical chunks**, not arbitrary slices:
   - Per `<diagram>` element
   - Or per large `<mxCell>` group
3. Store each chunk as a valid partial XML fragment
4. Record chunk ordering metadata

Agents MUST NOT:
- Split in the middle of XML tags
- Break ID references across chunks without tracking

---

### Chunk Editing Workflow

1. Load and validate each chunk independently
2. Apply modifications only to relevant chunks
3. Preserve all untouched chunks verbatim
4. Reassemble chunks in original order
5. Validate full XML integrity
6. Replace original file only after validation

Temporary chunks MUST be deleted after success unless debugging is required.

---

## Creating Large draw.io Files

When generating large diagrams:

- Build diagrams incrementally
- Generate separate logical diagram sections first
- Assemble into a final `.draw.io` file
- Validate after each assembly step

Agents MUST:
- Avoid generating thousands of nodes in one pass
- Prefer modular diagrams when possible

---

## Validation Rules

After creation or modification:

- Validate XML structure
- Confirm:
  - All referenced IDs exist
  - No duplicate IDs
  - All diagrams loadable by draw.io
- Ensure file remains text-based and readable

If validation fails:
- Abort replacement
- Restore from backup
- Log error details

---

## Temporary File Rules

- All intermediate files MUST be stored in:
  - `/tmp/windsurf/<operation-id>/`
- Never write intermediate XML next to the original
- Clean up temporary files after success

---

## Error Handling

- Any XML parsing error is a hard failure
- Never attempt auto-repair unless explicitly instructed
- Do not guess missing structures

Agents MUST log:
- Operation type
- Chunk count
- Validation results
- Failure reasons

---

## Security and Safety

- Do not execute embedded scripts
- Do not load external resources
- Do not follow external links
- Sanitize file paths

---

## Summary Principle

draw.io files are **structured diagrams, not documents**.

Treat them as:
- Structured XML
- Fragile
- Order-dependent
- ID-sensitive

All operations must be:
- Reversible
- Chunk-safe
- Strictly validated
- Deterministic

---

---

## CLI Export: Converting .drawio Files to PNG / PDF

A **.drawio file** (from draw.io / diagrams.net) can be converted to PNG or PDF via CLI. The `.drawio` extension is sometimes mistyped as `.draw.iko`, but it is the same format (XML or compressed XML).

### Recommended CLI tool

Use the official CLI provided by diagrams.net.

---

### Option 1. Using the diagrams.net CLI

#### Install (Linux)

```bash
sudo apt install drawio
```

Or download the AppImage from diagrams.net.

---

#### Convert to PNG

```bash
drawio --export --format png --output output.png input.drawio
```

---

#### Convert to PDF

```bash
drawio --export --format pdf --output output.pdf input.drawio
```

---

#### Useful flags

```bash
--scale 2              # higher resolution
--transparent         # PNG transparency
--page-index 0        # export specific page
--crop                # remove whitespace
```

---

### Option 2. Headless export (no GUI)

If you're running on a server:

```bash
drawio --export --format pdf --no-sandbox input.drawio
```

---

### Option 3. Docker (clean CI setup)

```bash
docker run --rm -v $PWD:/data rlespinasse/drawio \
  --export --format png --output /data/output.png /data/input.drawio
```

---

### Important caveats

- `.drawio` files are **XML**, sometimes compressed. No conversion without the draw.io engine
- Direct conversion via ImageMagick, etc., **won't work**
- If your file is actually `.draw.iko`, verify:

  ```bash
  file input.draw.iko
  ```

  It should report XML or compressed data

---

### Bottom line

- Fully supported via CLI
- Use `drawio --export`
- Works well in scripts, CI pipelines, and headless environments

---

## Citation Format — Never Cite by Catalogue Row Number (mandatory, all diagrams)

Node labels, annotations, and cited-work callouts on any `.drawio` diagram must never reference a literature-catalogue row number (e.g. "S#123", "[S123]", "S No 123"). The catalogue's `S No` column is an internal, mutable row index that gets renumbered and deduplicated over time, so a diagram annotation anchored to it silently points at the wrong source later. Annotate diagram nodes with `<short title>, <author> et al., <year>` (DOI/arXiv ID optional, add where space allows) instead.
