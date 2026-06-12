# ห้องสมุดสบายๆ — Design extraction notes

`index.html` is extracted and rebuilt from the Claude **design-code (dc)** artifact
`ห้องสมุดสบายๆ.html` (a self-contained "bundler" page).

## What the artifact actually contained

The downloaded `.html` was a Claude bundler package, not plain source. Decoding its
`<script type="__bundler/manifest">` (base64 + gzip per module) yielded **9 modules**:

| module | role |
|--------|------|
| `62e927b1…` | React (production min) — vendor |
| `22d9265b…` | ReactDOM (production min) — vendor |
| `b3e59e15…` | `dc-runtime` — renders `<x-dc>` markup |
| 6 × `*.woff2` | Noto Sans Thai font subsets |

The **actual design** is the markup inside the `<x-dc>…</x-dc>` block of the bundle
template (preserved verbatim in `_design_extracted/xdc_design_markup.html`). The dc-runtime
renders that markup, resolving `{{ … }}` bindings, `<sc-if>`, and `<sc-for>` at runtime.

## dc bindings → data model

The template drove two views (home / article) off these bindings:

- home: `isHome`, `totalLabel`, `featured.*`, `chips[]`, `visibleArticles[]`
- article: `isArticle`, `current.*` (title, excerpt, accent, catLabel, readLabel, owners,
  tags[]), `articleBody`, `related[]`

`index.html` reproduces the **exact inline styles** and re-implements this state machine in
plain vanilla JS (no React/build step needed) — home ↔ article navigation, category-chip
filtering, featured card, related-articles, and `#/a/<id>` deep links.

## Data seam → Supabase (next step, not yet wired)

Sample articles live in `loadArticles()` and are seeded from `cpg_book`'s knowledge
principles (Documented knowledge ≠ person, Summary ≠ source, Confidence ≠ evidence, …).
The UI makes no assumption about their origin. To connect Supabase, replace `loadArticles()`
with a fetch; a natural `articles` table shape:

```
articles(
  id text primary key,        -- slug, e.g. 'confidence-not-evidence'
  cat text,                   -- phil | know | exp | life | res
  title text,
  excerpt text,
  body_html text,             -- or body_md, rendered client-side
  tags text[],
  read_minutes int,
  featured bool default false,
  source text default 'cpg_book',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
)
```

Project ref (from `.mcp.json`): `ckvxuvkxctssyozscfbm`.

## Run locally

Any static server, e.g. `python -m http.server 4178 --directory cpg_bookweb`
(a `cpg_bookweb` config is already in `.claude/launch.json`).
