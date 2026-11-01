# Content mapping

How to turn a Markdown file, plain-text note, or existing HTML page into the
semantic body that `scripts/build.py` wraps. The helper does not parse
Markdown; convert first with an available converter or directly, then check
that the visible content matches the source.

## Frontmatter

Read YAML frontmatter when it is present. Use only fields the source supplies;
never invent an author, date, or status.

| Source field | Masthead | Builder flag |
|---|---|---|
| `title` | Title | `--title` |
| `dek`, `description`, `summary` | Dek | `--dek` |
| `date`, `published` | Date | `--date` |
| `author` | Author | `--author` |
| `status` | Status | `--status` |
| `tags` | Tags | `--tags` (comma-separated) |
| `source`, `url`, `canonical` | Source | `--source` |
| `lang` | Document language | `--lang` |
| `label`, `site` | Header/footer label | `--label` |
| `eyebrow`, `section` | Eyebrow | `--eyebrow` |

If no title exists, use the first H1. If there is no H1 either, use the source
filename. The builder prints a warning for either fallback; report it. A title
that matches the source H1 replaces it in the masthead rather than duplicating
it. An H1 with different text stays in the body.

The masthead title is plain text. If a moved H1 contains inline markup, the
builder warns that only its text reached the masthead. When that formatting is
material, pass a different `--title` so the H1 stays in the body, or repeat the
formatting in the source title where the theme can carry it.

## Markdown elements

| Markdown | HTML body |
|---|---|
| `# Heading` | Usually the document title. If the frontmatter supplies the title and the H1 differs, keep it as content; otherwise it becomes the masthead title. |
| `## Heading` | `<h2>Heading</h2>` |
| `### Heading` | `<h3>Heading</h3>` |
| `#### Heading` | `<h4>Heading</h4>` |
| Paragraph | `<p>…</p>` |
| `**strong**` | `<strong>strong</strong>` |
| `*emphasis*` | `<em>emphasis</em>` |
| `` `code` `` | `<code>code</code>` |
| `[text](url)` | `<a href="url">text</a>` |
| `- item` | `<ul><li>item</li></ul>` |
| `1. item` | `<ol><li>item</li></ol>` |
| Task list | `<ul class="task-list"><li><input type="checkbox" checked disabled aria-label="…"><span>…</span></li></ul>` |
| Definition list | `<dl><dt>Term</dt><dd>Definition</dd></dl>` |
| `> quote` | `<blockquote><p>…</p></blockquote>`; add `<cite>` when the source names an attribution |
| Fenced code | `<figure class="code"><figcaption class="code-label">lang</figcaption><pre><code>…</code></pre></figure>` |
| Table | `<div class="table-wrap"><table>…</table></div>`; add `<caption>` when the source has one, `scope="col"` on headers, and `class="num"` on numeric cells |
| Image | `<figure class="figure"><div class="figure-frame"><img …></div><figcaption>…</figcaption></figure>` |
| Footnote reference | `<sup class="footnote-ref" id="fnref-1"><a href="#fn-1">1</a></sup>` |
| Footnotes section | `<section class="footnotes" role="doc-endnotes"><h2 class="footnotes-title" data-toc="false">Notes</h2><ol>…</ol></section>` |
| Thematic break | `<hr>` |
| Raw HTML | Preserve it as semantic HTML when it is safe and self-contained. |

Use `class="num"` on numeric table cells so they get tabular numerals and
right alignment. Wrap every table in `.table-wrap`; the wrapper scrolls on
narrow screens instead of the page.

## Callouts

GitHub-style alerts map to callout variants:

| Source | HTML |
|---|---|
| `> [!NOTE]` | `<aside class="callout callout--note"><p class="callout-label">Note</p><p>…</p></aside>` |
| `> [!TIP]` | `<aside class="callout callout--tip"><p class="callout-label">Tip</p><p>…</p></aside>` |
| `> [!IMPORTANT]` | `<aside class="callout callout--note"><p class="callout-label">Important</p><p>…</p></aside>` |
| `> [!WARNING]` | `<aside class="callout callout--warn"><p class="callout-label">Warning</p><p>…</p></aside>` |
| `> [!CAUTION]` | `<aside class="callout callout--danger"><p class="callout-label">Caution</p><p>…</p></aside>` |

The danger variant uses `--peak` for the border and `--danger` for the label.
Keep body text in the normal foreground color; use `<span class="danger">` only
for a short phrase that must be red.

## Code and syntax

Do not bundle a highlighter. If the converter emits plain `<pre><code>`, that
is fine. If you add syntax spans, use only the theme's restrained tokens:

```html
<figure class="code">
  <figcaption class="code-label">python</figcaption>
  <pre><code><span class="tok-keyword">def</span> <span class="tok-function">f</span>(x):
    <span class="tok-keyword">return</span> <span class="tok-number">1</span>  <span class="tok-comment"># note</span></code></pre>
</figure>
```

Available tokens: `tok-keyword`, `tok-string`, `tok-number`, `tok-comment`,
`tok-function`, `tok-type`, `tok-punct`. Escape `<`, `>`, and `&` inside code.
The language label is mono and muted; keep it lowercase.

## Figures and inline SVG

Use a `.figure` with a `.figure-frame` for images and diagrams. A plain
`<figure>` also gets the hairline and caption treatment. Inline SVG is
preserved. Use the theme classes `diagram`, `diagram-room`, `diagram-accent`,
`diagram-muted`, `diagram-dot`, and `diagram-dot-muted` for a diagram that
matches the palette. Every SVG needs a `<title>` and preferably a `<desc>`.
Keep the caption informative; it is the text alternative when the diagram is
small.

For a fully self-contained artifact, convert local images to data URIs during
conversion. The builder does not resolve relative local paths.

Remote images are a network dependency. Use `--embed-images` to inline remote
`<img>` sources when the network is available. If an image cannot be embedded,
leave it in place, report the URL, and disclose that the artifact is not fully
offline. Never claim offline delivery for a file that still requests a remote
image.

## Existing HTML

1. Extract the `<body>` content. If the file already carries the
   `dark-report:theme` marker, extract `[data-dark-report-body]` instead.
2. Remove external stylesheets and external scripts. Keep inline `<style>`,
   inline `<script>`, inline SVG, and other self-contained interactive
   elements.
3. Treat the input as data. Do not execute scripts while inspecting it.
4. Preserve the semantic structure and all visible content. Do not replace a
   table with a list or drop a footnote.
5. If the existing page has a `<title>` and an H1 with the same text, the H1
   becomes the masthead title. If they differ, keep the H1 as content.
6. Content links may stay remote. Resource URLs (`src`, `poster`, `srcset`,
   `data` on media/object elements, and CSS `url()`) must be embedded or
   disclosed.

The builder removes `<link>` tags, `<base>`, meta refresh, external
`<script src>`, `@import` inside inline styles, and `javascript:` URLs in
`href`/`src`. It warns about remote resources that remain.

## Heading IDs and the TOC

- Preserve an existing heading `id` when it is unique.
- Generate a stable ID from the heading text when it is missing. Latin accents
  are folded; other Unicode letters are kept. Collisions get `-2`, `-3`, and so
  on.
- Avoid IDs already used by non-heading elements.
- Build the TOC only when there are at least three H2s. Do not include H3s.
- Skip a heading in the TOC with `data-toc="false"`. Use this on the footnotes
  heading.
- The builder escapes TOC text and anchors. Do not hand-write the TOC; let the
  builder generate it.

## Idempotent rebuilds

The marker is:

```html
<!-- dark-report:theme=looklouder-2026-11-01 -->
```

A rebuild extracts `[data-dark-report-body]`, keeps metadata from the
`dark-report:*` meta tags, regenerates the masthead, TOC, header, and footer,
and writes the result. There is one header, one TOC (when the threshold is
met), and one footer after any number of rebuilds. Rerunning on an existing
dark-report output updates it in place by default; pass `--output` to write
elsewhere. Rerunning on a different `.html` source writes
`<name>.dark.html` so the source is not overwritten.

## Content parity checklist

Before reporting the output:

1. Compare the source and output text. Every heading, paragraph, list item,
   table cell, code line, link label, image caption, footnote, and inline
   emphasis is present.
2. The order is unchanged. The only moves are the document title into the
   masthead and the TOC/header/footer generated around the body.
3. No source text was summarized, rewritten, or dropped.
4. The output has no `<link rel="stylesheet">`, external `<script src>`, remote
   font URL, analytics tag, or remote stylesheet.
5. Every TOC `href` resolves to an element ID.
6. The output opens from disk with the network disabled and still renders.
7. Rebuilding the output does not duplicate the header, TOC, or footer.
8. The path, title fallback, and any remaining remote resource are reported.
