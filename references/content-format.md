# Reader content format

Author JSON using this structure. Synthesis strings are plain text, not Markdown or HTML. Original `text` accepts Markdown when `source_format` is `markdown` (the default); set `source_format` to `text` for literal originals. Markdown is rendered offline with bundled Mistune, while the Source text toggle preserves verbatim syntax. Required fields appear in the example. Empty question arrays are allowed. `kind` is optional and supports `key` or `uncertain`, rendered with a visible label and switchable color. Use it sparingly. A paragraph is `{ "text": "..." }`; a subsection heading is `{ "heading": "..." }`; a list is `{ "items": ["...", "..."] }`. Keep numerical tables in accurate readable rows or extend the template if a real table is essential; do not lose units or relationships.

Section IDs must be unique lowercase slugs. `original` is a required ordered array of full-source blocks with unique lowercase slug `id` and verbatim `text`; `heading: true` is optional. Together these blocks must contain the entire original text, including repetition removed from the synthesis. Preserve whitespace inside blocks. Do not split fenced code, tables, nested lists, blockquotes or reference definitions across blocks. Preserve their indentation; only split at complete Markdown block boundaries. For a finer highlight, use exact phrases inside a complete block rather than breaking the syntax. Optional `highlights` contain exact `text`, `kind` (`key` or `uncertain`), and a one-based `occurrence` when the text repeats within that block. Highlights must not overlap. Use meaningful visible text, not only formatting syntax or a hidden link destination. Exact highlight strings may include Markdown emphasis, links or code delimiters; the renderer maps them onto rendered text without corrupting tags. Every reading section needs a nonempty `original_ids` array referring to relevant original block IDs. This maps passage links; linked scrolling uses relative reading progress, since synthesis may reorder the source. Theme `sections` and closing-question `sections` must reference those IDs. Each section's `sources` must be nonempty and carry an accurate `location`; `quote`, `url`, and `original_ids` are optional. Provide source-level `original_ids` for precise source-location hover/focus highlighting; otherwise the reference highlights all original blocks mapped by its section. Source-location labels link into the original pane, with any external URL offered separately. Only absolute HTTP(S) URLs are clickable; local sources are identified by filename and location. `coverage` must state any missing source material and meaningful omissions. `source` identifies the supplied document. A question's `basis` explains its connection to the content. Closing questions also link back to relevant sections.

```json
{
  "title": "A readable title",
  "source_format": "markdown",
  "source": "Source filename or document title",
  "coverage": "Full supplied text reviewed. Repeated framing consolidated; sections grouped by theme.",
  "original": [{"id": "p1", "text": "The proposal includes a five-customer pilot. The launch date remains undecided.", "highlights": [{"text": "five-customer pilot", "kind": "key"}, {"text": "The launch date remains undecided.", "kind": "uncertain"}]}],
  "tldr": ["What the document covers and asks of the reader."],
  "themes": [{"title": "Scope", "description": "What is included and excluded.", "sections": ["scope"]}],
  "sections": [{
    "id": "scope",
    "title": "What the proposal includes",
    "original_ids": ["p1"],
    "gist": "One sentence explaining this section.",
    "blocks": [{"text": "Readable synthesis of the supplied content."}, {"text": "A consequential uncertainty.", "kind": "uncertain"}],
    "takeaways": ["A conclusion supported by this section."],
    "questions": [{"question": "Which specific unresolved choice needs an answer?", "basis": "The source describes the alternatives but does not select one."}],
    "sources": [{"location": "Source heading, paragraph 2", "original_ids": ["p1"], "quote": "A short, exact excerpt when useful."}]
  }],
  "takeaways": ["A document-wide conclusion."],
  "questions": [{"question": "What decision is needed before proceeding?", "basis": "Why this question arises from the supplied text.", "sections": ["scope"]}]
}
```

Reader comments are separate from this synthesis JSON. The renderer embeds a stable hash of the ordered original text to namespace local browser storage. Keep original block and reading-section IDs stable across revisions so existing anchors can resolve. Annotations store the selected text, offsets, nearby context, view (formatted/raw/reading), and comment text. They are exportable/importable as a separate JSON file; sharing the HTML alone does not share browser-saved comments. A changed source yields a new document identity.

For a difficult concept, insert an example block near its explanation:

```json
{"example": {"title": "A repeated stop request", "origin": "illustration", "text": "Suppose a stop request succeeds, but its reply is lost. A retry must not repeat the effect of that same request.", "original_ids": ["p1"]}}
```

`title`, `text`, `origin`, and a nonempty `original_ids` array are required. The IDs must identify real source passages supporting the concept. Use `origin: "source"` for a scenario supplied by the source; use `"illustration"` for a hypothetical explanation you add. The latter renders with a “Concept in the source” link, so the citation does not imply that the source contains the invented scenario. All example text is escaped plain text and remains selectable for comments. Follow [the writing guidance](writing-style.md) for all generated prose.
