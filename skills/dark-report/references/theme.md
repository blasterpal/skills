# dark-report theme

A warm, dark editorial theme for one long-form document at a time. It derives
its typography, palette, rules, and component treatments from
[looklouder.com](https://looklouder.com/) without reusing the homepage's
content, VU meter, project cards, track list, or employer copy.

## Source

| Field | Value |
|---|---|
| Source page | https://looklouder.com/ |
| Stylesheet at extraction | https://looklouder.com/_astro/Base.BGSi4hq3.css |
| Extracted | 2026-11-01 |
| Page reviewed | 1280 px and 390 px in Brave over CDP |
| Theme marker | `looklouder-2026-11-01` |

The stylesheet hash changes when the site is rebuilt. Re-extract the tokens
from the live CSS rather than assuming the URL above stays valid.

## Tokens

The site's core tokens are kept unchanged. The report adds only the semantic
colors, measure, and radius listed in the second table.

| Token | Value | Use |
|---|---|---|
| `--bg` | `#15120f` | Page background |
| `--surface` | `#1d1915` | Code, callouts, figure frames, table headers |
| `--line` | `#342c24` | Decorative hairlines |
| `--fg` | `#ede6da` | Body text, links, headings |
| `--muted` | `#9b9082` | Metadata, labels, captions, secondary text |
| `--accent` | `#f2a33a` | Links, focus, interactive borders, active TOC |
| `--peak` | `#e5484d` | Large danger accents only |
| `--display` | Big Shoulders Display, Oswald, Arial Narrow, sans-serif | Display headings |
| `--body` | IBM Plex Sans, Helvetica Neue, Arial, sans-serif | Body |
| `--mono` | IBM Plex Mono, SFMono-Regular, Menlo, monospace | Labels, metadata, code, tables |

| Report token | Value | Use |
|---|---|---|
| `--ok` | `#9bbf8a` | Success, tip |
| `--warn` | `#e0a45a` | Warning |
| `--danger` | `#ef6468` | Small danger text and labels |
| `--comment` | `#8b8175` | Code comments |
| `--measure` | `68ch` | Prose measure |
| `--radius` | `4px` | Code, callouts, figures |

`color-scheme: dark` is set on `:root`. Print overrides the tokens with light
values in the same stylesheet.

## Typography

- Big Shoulders Display 700/900 for display headings. Uppercase, tight leading
  (0.86 for the article title, 0.95 for H2), H3 at 1.4rem.
- Article title: `clamp(3rem, 8vw, 6rem)`. H2: `clamp(2rem, 4vw, 3rem)`.
- IBM Plex Sans 400/500 for body, 17px on small screens and 18px at 900px and
  above, line-height 1.65, measure 68ch.
- IBM Plex Mono 400/500 for labels, metadata, nav, tags, code, table headers,
  and captions. Labels are 0.72–0.8rem, uppercase, with 0.06–0.1em tracking.

The homepage's 11.5rem hero scale is intentionally not used.

## Layout and components

- Centered 1120px outer shell, 68ch prose, 3–3.5rem section spacing.
- 56px sticky header with a blurred dark background, hairline bottom, 9px
  amber LED dot, a short document label, and an optional Contents link.
- Two-column masthead on wide screens: title and dek left, metadata right.
  It stacks below 760px.
- Mono eyebrow with a hairline rule after it.
- Links are cream with an amber underline; hover and focus turn amber.
- Buttons are mono uppercase, transparent with a 1px amber border and 3px
  radius. Hover fills amber with dark text.
- Tags are mono lowercase with a `#` prefix, muted.
- Callouts use the surface background, a 2px semantic left border, and a mono
  label.
- Tables use mono uppercase headers, hairline row rules, tabular numerals, and
  an internal horizontal scroll wrapper.
- Code uses a surface background, hairline border, 4px radius, a mono language
  label, and a small warm syntax palette. No highlighter is bundled.
- Blockquotes use a 2px amber left border and muted text.
- Figures use a hairline frame and mono caption. Inline SVG is styled with the
  same tokens.
- Footnotes, task lists, details/summary, and inline SVG diagrams are styled.
- The TOC is mono links with hairline rules and an amber active state. It is
  built only when there are three or more H2s.
- The LED dot is the only glow. The sticky header's blur is the one translucent
  treatment; there are no gradients, other glass effects, neon, or purple accents.

## Accessibility

Measured WCAG 2.2 contrast ratios:

| Pair | Ratio | Result |
|---|---|---|
| Body `--fg` on `--bg` | 15.05:1 | AAA |
| Body `--fg` on `--surface` | 14.09:1 | AAA |
| `--muted` on `--bg` | 5.96:1 | AA |
| `--muted` on `--surface` | 5.58:1 | AA |
| `--accent` on `--bg` | 8.95:1 | AAA |
| `--accent` on `--surface` | 8.38:1 | AAA |
| `--bg` on `--accent` (button hover) | 8.95:1 | AAA |
| `--danger` on `--surface` | 5.57:1 | AA |
| `--ok` on `--surface` | 8.50:1 | AAA |
| `--warn` on `--surface` | 8.01:1 | AAA |
| `--comment` on `--surface` | 4.57:1 | AA |
| `--peak` on `--surface` | 4.46:1 | Below AA for small text |
| `--line` on `--surface` | 1.27:1 | Decorative only |

Intentional adjustments:

1. Small red text uses `--danger`, not `--peak`. `--peak` is 4.46:1 on
   `--surface`, just under the 4.5:1 AA threshold for small text. It is reserved
   for large accents such as the danger callout border.
2. `--muted` passes at 5.58:1 on the surface and is used for labels and
   secondary text.
3. `--comment` passes at 4.57:1 on the surface. It is not lightened further so
   comments stay subordinate to code.
4. `--line` is decorative. Text is never placed on `--line`, and interactive
   boundaries use `--accent` (8.95:1 on the page, 8.38:1 on the surface).
5. Focus uses a 2px `--accent` outline with a 3px offset. The theme also
   provides a skip link and a print stylesheet.

Print contrast:

| Pair | Ratio |
|---|---|
| Body `#14110e` on `#fbf8f2` | 17.75:1 |
| Muted `#4a4238` on `#fbf8f2` | 9.31:1 |
| Accent `#8a4b00` on `#fbf8f2` | 6.42:1 |
| Danger `#a51d24` on `#fbf8f2` | 7.07:1 |
| OK `#2f5d2a` on `#fbf8f2` | 7.28:1 |
| Warning `#7a4a00` on `#fbf8f2` | 7.06:1 |
| Comment `#5a5146` on `#fbf8f2` | 7.34:1 |

## Fonts and licenses

The Latin WOFF2 subsets are stored in `assets/fonts/` and inlined as base64
data URIs by `scripts/build.py`. The theme CSS references them with relative
paths, so the source stays readable; the built HTML has no remote font URLs.
If a font file is missing, the builder drops that `@font-face` rule and the
fallback stack in the token applies. `--no-fonts` disables embedding entirely.

**Big Shoulders Display**

Copyright 2019 The Big Shoulders Project Authors
(https://github.com/xotypeco/big_shoulders).
Licensed under the SIL Open Font License, Version 1.1.

**IBM Plex Sans and IBM Plex Mono**

Copyright 2017 IBM Corp.
Licensed under the SIL Open Font License, Version 1.1.

Both fonts are distributed under the SIL Open Font License, Version 1.1. The
full license text is at
https://openfontlicense.org/open-font-license-official-text/. The OFL permits
embedding and redistribution of the font software with the document. The
copyright and license notices above are retained here.

## Build and demo

The demo is an original long-form article, not the looklouder.com homepage. Its
source body is `assets/demo-body.html`; the standalone page is
`assets/demo.html`.

Rebuild the demo from the repository root:

```sh
python3 skills/dark-report/scripts/build.py \
  --body skills/dark-report/assets/demo-body.html \
  --title "The Room Is the Instrument" \
  --dek "A practical note on measuring a small room before buying another piece of gear." \
  --date "2026-11-01" \
  --author "Hank Beaver" \
  --status "Field note" \
  --tags "acoustics, monitoring, home-studio" \
  --label "Field Notes" \
  --eyebrow "Studio log" \
  --output skills/dark-report/assets/demo.html
```

The demo was rendered at 360px, 768px, and 1280px through the running Brave
session. At each width the document scroll width equals the viewport width, the
TOC anchors resolve, all six embedded fonts load, and there are no external
resource requests. The table and code block scroll inside their own containers
at 360px.

A generic Lorem Ipsum preview is at `assets/placeholder.html`, with its source
body at `assets/placeholder-body.html`. It uses the same theme and builder and
shows the component set with placeholder copy.

## Known limitations

1. The inline SVG diagram scales with its viewBox. Its labels are larger on
   mobile via a media query, but they remain smaller than body text at 360px.
   The figure caption carries the same information.
2. The header uses `color-mix()` with an opaque `--bg` fallback. Browsers
   without `color-mix()` get an opaque header rather than the blurred
   translucent treatment.
3. The theme has no JavaScript. A copy button or other enhancement is the
   document author's responsibility and must be progressive.
4. The theme is intentionally one document per output. It does not style a
   blog index or listing page.
5. The theme is not Tripleseat branding and must not be used for branded
   company documents.
