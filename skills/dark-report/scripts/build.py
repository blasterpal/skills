#!/usr/bin/env python3
"""Build one self-contained dark-report HTML file.

The helper takes semantic HTML, not Markdown. Convert Markdown to semantic HTML
first (with an available converter or directly), then pass the body here. The
helper wraps it in the looklouder-derived theme, inlines local fonts, generates
stable heading IDs and a Contents nav, and writes a standalone UTF-8 file.

Standard library only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import os
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = SKILL_DIR / "assets"
DEFAULT_THEME = ASSETS_DIR / "theme.css"
DEFAULT_TEMPLATE = ASSETS_DIR / "template.html"

THEME_ID = "looklouder-2026-11-01"
MARKER_RE = re.compile(r"<!--\s*dark-report:theme=([^\s]+)\s*-->")
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+)\}\}")
HEADING_RE = re.compile(r"<h([1-6])(\s[^>]*)?>(.*?)</h\1\s*>", re.I | re.S)
H1_RE = re.compile(r"<h1(\s[^>]*)?>(.*?)</h1\s*>", re.I | re.S)
ID_RE = re.compile(r"(?<![\w:-])id\s*=\s*([\"'])(.*?)\1", re.I | re.S)
DATA_TOC_FALSE_RE = re.compile(r"\bdata-toc\s*=\s*(?:[\"']?false[\"']?|false)", re.I)
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
REMOTE_RESOURCE_RE = re.compile(
    r"<(?:img|source|video|audio|iframe|embed|track|input|object|image|use)\b[^>]*"
    r"\b(?:src|srcset|poster|data|href|xlink:href)\s*=\s*([\"'])(https?://[^\"']+)\1",
    re.I,
)
REMOTE_STYLE_URL_RE = re.compile(r"url\(\s*([\"']?)(https?://[^\"')]+)\1\s*\)", re.I)
REMOTE_INLINE_STYLE_RE = re.compile(r"\bstyle\s*=\s*([\"'])(.*?)\1", re.I | re.S)
JS_URL_RE = re.compile(
    r"\b(href|src)\s*=\s*([\"'])\s*javascript:[^\"']*\2", re.I
)
LINK_RE = re.compile(r"<link\b[^>]*>", re.I)
BASE_RE = re.compile(r"<base\b[^>]*>", re.I)
REFRESH_RE = re.compile(r"<meta\b[^>]*http-equiv\s*=\s*[\"']?refresh[^>]*>", re.I)
SCRIPT_SRC_RE = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)[^>]*>"
    r".*?</script\s*>",
    re.I | re.S,
)
SCRIPT_SRC_SELF_RE = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)[^>]*/\s*>",
    re.I,
)
STYLE_RE = re.compile(r"(<style\b[^>]*>)(.*?)(</style\s*>)", re.I | re.S)
URL_RE = re.compile(r"url\(\s*([\"']?)([^\"')]+)\1\s*\)", re.I)
FONT_FACE_RE = re.compile(r"@font-face\s*\{.*?\}", re.I | re.S)


class InnerHTMLParser(HTMLParser):
    """Capture the inner HTML of the first element matching a predicate."""

    def __init__(self, predicate):
        super().__init__(convert_charrefs=False)
        self.predicate = predicate
        self.depth = 0
        self.capturing = False
        self.found = False
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text() or f"<{tag}>"
        if self.capturing:
            self.parts.append(raw)
            if tag not in VOID_ELEMENTS:
                self.depth += 1
        elif self.predicate(tag, dict(attrs)):
            self.found = True
            if tag in VOID_ELEMENTS:
                return
            self.capturing = True
            self.depth = 1

    def handle_startendtag(self, tag, attrs):
        raw = self.get_starttag_text() or f"<{tag} />"
        if self.capturing:
            self.parts.append(raw)
        elif self.predicate(tag, dict(attrs)):
            self.found = True

    def handle_endtag(self, tag):
        if not self.capturing or tag in VOID_ELEMENTS:
            return
        self.depth -= 1
        if self.depth == 0:
            self.capturing = False
        else:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if self.capturing:
            self.parts.append(data)

    def handle_entityref(self, name):
        if self.capturing:
            self.parts.append(f"&{name};")

    def handle_charref(self, name):
        if self.capturing:
            self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        if self.capturing:
            self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        if self.capturing:
            self.parts.append(f"<!{decl}>")

    def handle_pi(self, data):
        if self.capturing:
            self.parts.append(f"<?{data}>")

    def unknown_decl(self, data):
        if self.capturing:
            self.parts.append(f"<![{data}]>")

    def result(self):
        return "".join(self.parts)


class MetaParser(HTMLParser):
    """Read dark-report meta tags and the document title from a full document."""

    def __init__(self):
        super().__init__()
        self.meta: dict[str, str] = {}
        self._title_parts: list[str] = []
        self._in_head = False
        self._in_title = False

    def _read_meta(self, values):
        name = (values.get("name") or "").strip().lower()
        if name.startswith("dark-report:"):
            self.meta[name.split(":", 1)[1]] = values.get("content") or ""

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "head":
            self._in_head = True
        elif tag == "meta":
            self._read_meta(values)
        elif tag == "title" and self._in_head:
            self._in_title = True

    def handle_startendtag(self, tag, attrs):
        if tag == "meta":
            self._read_meta(dict(attrs))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "head":
            self._in_head = False

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)

    def title(self) -> str:
        return collapse_space("".join(self._title_parts))


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def collapse_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def escape(value: str) -> str:
    return html.escape(value or "", quote=True)


def strip_tags(fragment: str) -> str:
    fragment = re.sub(r"<sup\b[^>]*>.*?</sup\s*>", "", fragment, flags=re.I | re.S)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    return collapse_space(html.unescape(fragment))


def slugify(value: str) -> str:
    value = strip_tags(value)
    value = unicodedata.normalize("NFKD", value)
    value = re.sub(r"[\u0300-\u036f]", "", value)
    value = value.casefold()
    value = re.sub(r"[^\w]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"_+", "-", value)
    return value.strip("-")


def unique_id(base: str, used: set[str]) -> str:
    base = base or "section"
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _set_id(attrs: str, value: str) -> str:
    match = ID_RE.search(attrs)
    escaped = escape(value)
    if match:
        return attrs[: match.start()] + f'id="{escaped}"' + attrs[match.end() :]
    return f'{attrs} id="{escaped}"'


def process_headings(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Add or deduplicate heading IDs and collect H2 entries for the TOC."""
    matches = list(HEADING_RE.finditer(body))
    without_headings = HEADING_RE.sub("", body)
    non_heading_ids = {
        html.unescape(match.group(2)).strip()
        for match in ID_RE.finditer(without_headings)
    }
    heading_ids = []
    for match in matches:
        id_match = ID_RE.search(match.group(2) or "")
        heading_ids.append(html.unescape(id_match.group(2)).strip() if id_match else "")

    # Reserve every existing heading ID before generating new ones, so a
    # generated ID cannot take an ID that a later heading already owns.
    preserved_heading_ids = {value for value in heading_ids if value}
    reserved = non_heading_ids | preserved_heading_ids
    used: set[str] = set()
    toc: list[tuple[str, str]] = []
    output: list[str] = []
    last = 0

    for index, (match, existing) in enumerate(zip(matches, heading_ids), start=1):
        level = int(match.group(1))
        attrs = match.group(2) or ""
        inner = match.group(3)
        text = strip_tags(inner)

        if existing and existing in non_heading_ids:
            final_id = unique_id(existing, used | reserved)
        elif existing and existing not in used:
            final_id = existing
        elif existing:
            final_id = unique_id(existing, used | reserved)
        else:
            final_id = unique_id(slugify(text) or f"section-{index}", used | reserved)
        used.add(final_id)

        attrs = _set_id(attrs, final_id)
        output.append(body[last : match.start()])
        output.append(f"<h{level}{attrs}>{inner}</h{level}>")
        last = match.end()

        if level == 2 and not DATA_TOC_FALSE_RE.search(attrs):
            toc.append((final_id, text))

    output.append(body[last:])
    return "".join(output), toc


def make_toc(entries: list[tuple[str, str]]) -> str:
    if len(entries) < 3:
        return ""
    items = "\n".join(
        f'      <li><a href="#{escape(anchor)}"><span class="toc-num">{index:02d}</span>'
        f"<span>{escape(text)}</span></a></li>"
        for index, (anchor, text) in enumerate(entries, start=1)
    )
    return (
        '<nav class="toc" id="contents" aria-labelledby="toc-title" '
        'data-dark-report-toc>\n'
        '  <p class="toc-title" id="toc-title">Contents</p>\n'
        "  <ol>\n"
        f"{items}\n"
        "  </ol>\n"
        "</nav>"
    )


def extract_inner(text: str, predicate) -> str | None:
    parser = InnerHTMLParser(predicate)
    parser.feed(text)
    parser.close()
    return parser.result() if parser.found else None


def load_document(path: Path) -> tuple[str, dict[str, str], str, bool]:
    """Return body HTML, dark-report metadata, document title, already-themed."""
    text = path.read_text(encoding="utf-8")
    meta_parser = MetaParser()
    meta_parser.feed(text)
    already_themed = bool(MARKER_RE.search(text))

    body = None
    if already_themed:
        body = extract_inner(
            text,
            lambda tag, attrs: tag == "div" and "data-dark-report-body" in attrs,
        )
        if body is None:
            body = extract_inner(
                text,
                lambda tag, attrs: tag == "main" and "data-dark-report-content" in attrs,
            )
    if body is None:
        body = extract_inner(text, lambda tag, attrs: tag == "body")
    if body is None:
        body = text
    return body, meta_parser.meta, meta_parser.title(), already_themed


def sanitize_body(body: str) -> str:
    """Remove external stylesheets and scripts while keeping inline content."""
    body = LINK_RE.sub("", body)
    body = BASE_RE.sub("", body)
    body = REFRESH_RE.sub("", body)
    body = SCRIPT_SRC_RE.sub("", body)
    body = SCRIPT_SRC_SELF_RE.sub("", body)

    def clean_style(match):
        opening, content, closing = match.groups()
        content = re.sub(r"@import\s+(?:url\()?[^;]+;", "", content, flags=re.I)
        return f"{opening}{content}{closing}"

    body = STYLE_RE.sub(clean_style, body)
    body = JS_URL_RE.sub(lambda m: f'{m.group(1)}="#"', body)
    return body


def remote_resources(body: str) -> list[str]:
    found = [m.group(2) for m in REMOTE_RESOURCE_RE.finditer(body)]
    for match in STYLE_RE.finditer(body):
        found.extend(m.group(2) for m in REMOTE_STYLE_URL_RE.finditer(match.group(2)))
    for match in REMOTE_INLINE_STYLE_RE.finditer(body):
        found.extend(m.group(2) for m in REMOTE_STYLE_URL_RE.finditer(match.group(2)))
    return sorted(set(found))


def fetch_data_uri(url: str, max_bytes: int = 10 * 1024 * 1024) -> str:
    request = Request(url, headers={"User-Agent": "dark-report/1.0"})
    with urlopen(request, timeout=15) as response:
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("remote image is larger than 10 MB")
        content_type = response.headers.get_content_type()
    if not content_type or content_type == "application/octet-stream":
        content_type = mimetypes.guess_type(urlparse(url).path)[0] or "application/octet-stream"
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def embed_remote_images(body: str) -> str:
    tag_re = re.compile(r"<img\b[^>]*>", re.I)
    src_re = re.compile(r"(\bsrc\s*=\s*)([\"'])(https?://[^\"']+)\2", re.I)

    def replace_tag(tag_match):
        def replace_src(src_match):
            url = src_match.group(3)
            try:
                data_uri = fetch_data_uri(url)
            except Exception as error:  # network and size failures are reported, not fatal
                warn(f"could not embed remote image {url}: {error}")
                return src_match.group(0)
            return f"{src_match.group(1)}{src_match.group(2)}{data_uri}{src_match.group(2)}"

        return src_re.sub(replace_src, tag_match.group(0))

    return tag_re.sub(replace_tag, body)


def extract_css_token(css: str, name: str) -> str:
    match = re.search(rf"--{re.escape(name)}\s*:\s*([^;]+);", css)
    if not match:
        raise ValueError(f"theme is missing --{name}")
    return match.group(1).strip()


def strip_font_faces(css: str, assets_dir: Path, keep_fonts: bool) -> str:
    def replace(match):
        if not keep_fonts:
            return ""
        for url_match in URL_RE.finditer(match.group(0)):
            url = url_match.group(2)
            if url.startswith("data:") or re.match(r"^[a-z]+://", url, re.I) or url.startswith("//"):
                continue
            if not (assets_dir / url).is_file():
                warn(f"font file missing: {url}; using fallback stacks")
                return ""
        return match.group(0)

    return FONT_FACE_RE.sub(replace, css)


def inline_theme(css: str, assets_dir: Path, keep_fonts: bool = True) -> str:
    css = strip_font_faces(css, assets_dir, keep_fonts)
    if not keep_fonts:
        return css

    def replace(match):
        url = match.group(2)
        if url.startswith("data:"):
            return match.group(0)
        if re.match(r"^[a-z]+://", url, re.I) or url.startswith("//"):
            raise ValueError(f"theme references a remote resource: {url}")
        path = (assets_dir / url).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"theme asset not found: {url}")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'url("data:{mime};base64,{data}")'

    return URL_RE.sub(replace, css)


def safe_url(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme in ("http", "https", "mailto") or not parsed.scheme:
        return value
    return None


def render_date(value: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return f'<time datetime="{escape(value)}">{escape(value)}</time>'
    return escape(value)


def build_meta_items(
    date: str, author: str, status: str, tags: list[str], source: str
) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if date:
        items.append(("Date", render_date(date)))
    if author:
        items.append(("Author", escape(author)))
    if status:
        items.append(("Status", f'<span class="status">{escape(status)}</span>'))
    if tags:
        tag_html = "".join(f'<li class="tag">{escape(tag)}</li>' for tag in tags)
        items.append(("Tags", f'<ul class="tags">{tag_html}</ul>'))
    if source:
        href = safe_url(source)
        value = f'<a href="{escape(href)}">{escape(source)}</a>' if href else escape(source)
        items.append(("Source", value))
    return items


def build_masthead(
    title: str, dek: str, label: str, eyebrow: str, meta_items: list[tuple[str, str]]
) -> str:
    eyebrow_html = f'<p class="eyebrow">{escape(eyebrow)}</p>' if eyebrow else ""
    dek_html = f'<p class="dek">{escape(dek)}</p>' if dek else ""
    meta_html = ""
    if meta_items:
        rows = "\n".join(
            f'    <div class="meta-item"><dt>{escape(key)}</dt><dd>{value}</dd></div>'
            for key, value in meta_items
        )
        meta_html = f'  <dl class="meta">\n{rows}\n  </dl>'
    solo = "" if meta_items else " masthead--solo"
    return (
        f'<header class="masthead{solo}">\n'
        '  <div class="masthead-main">\n'
        f"    {eyebrow_html}\n"
        f'    <h1 class="doc-title">{escape(title)}</h1>\n'
        f"    {dek_html}\n"
        "  </div>\n"
        f"{meta_html}\n"
        "</header>"
    )


def build_footer(label: str, source: str) -> str:
    note = "Theme dark-report 2026-11-01"
    if source:
        href = safe_url(source)
        link = f'<a href="{escape(href)}">Source</a>' if href else escape(source)
        note = f"{link} · {note}"
    return (
        '<footer class="doc-footer" data-dark-report-footer>'
        f"<span>{escape(label)}</span><span>{note}</span>"
        "</footer>"
    )


def render_document(
    template: str,
    *,
    lang: str,
    title: str,
    dek: str,
    label: str,
    eyebrow: str,
    date: str,
    author: str,
    status: str,
    source: str,
    tags: list[str],
    body: str,
    theme_css: str,
    theme_color: str,
) -> str:
    meta_items = build_meta_items(date, author, status, tags, source)
    masthead = build_masthead(title, dek, label, eyebrow, meta_items)
    processed_body, toc_entries = process_headings(body)
    toc = make_toc(toc_entries)
    header_nav = (
        '<nav class="header-nav" aria-label="Document"><a href="#contents">Contents</a></nav>'
        if toc
        else ""
    )
    footer = build_footer(label, source)

    meta_tags = [
        f'<meta name="dark-report:{key}" content="{escape(value)}">'
        for key, value in (
            ("title", title),
            ("dek", dek),
            ("date", date),
            ("author", author),
            ("status", status),
            ("source", source),
            ("tags", ", ".join(tags)),
            ("label", label),
            ("eyebrow", eyebrow),
            ("lang", lang),
        )
        if value
    ]
    if dek:
        meta_tags.append(f'<meta name="description" content="{escape(dek)}">')
    if author:
        meta_tags.append(f'<meta name="author" content="{escape(author)}">')

    values = {
        "LANG": escape(lang),
        "TITLE": escape(title),
        "THEME_COLOR": escape(theme_color),
        "META": "\n".join(meta_tags),
        "MARKER": f"<!-- dark-report:theme={THEME_ID} -->",
        "LABEL": escape(label),
        "HEADER_NAV": header_nav,
        "MASTHEAD": masthead,
        "TOC": toc,
        "BODY": processed_body,
        "FOOTER": footer,
        "THEME": theme_css,
    }

    def replace(match):
        key = match.group(1)
        if key not in values:
            raise KeyError(f"unknown template placeholder: {key}")
        return values[key]

    return PLACEHOLDER_RE.sub(replace, template)


def first_h1(body: str) -> tuple[str, str | None, bool]:
    match = H1_RE.search(body)
    if not match:
        return body, None, False
    inner = match.group(2)
    text = strip_tags(inner)
    has_markup = bool(re.search(r"<[^>]+>", inner))
    return body[: match.start()] + body[match.end() :], text, has_markup


def default_output(path: Path) -> Path:
    if path.suffix.lower() in (".html", ".htm"):
        return path.with_name(f"{path.stem}.dark.html")
    return path.with_suffix(".html")


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temporary, path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wrap semantic HTML in the dark-report theme and write one offline HTML file."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path, help="Existing HTML document or fragment.")
    source.add_argument("--body", type=Path, help="Semantic HTML body fragment.")
    parser.add_argument("-o", "--output", type=Path, help="Output HTML path.")
    parser.add_argument("--title")
    parser.add_argument("--dek")
    parser.add_argument("--date")
    parser.add_argument("--author")
    parser.add_argument("--status")
    parser.add_argument("--source")
    parser.add_argument("--tags", help="Comma-separated tags.")
    parser.add_argument("--label", help="Short document label for the header and footer.")
    parser.add_argument("--eyebrow", help="Mono eyebrow above the title.")
    parser.add_argument("--lang", default=None)
    parser.add_argument("--theme", type=Path, default=DEFAULT_THEME)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument(
        "--no-fonts",
        action="store_true",
        help="Use the fallback font stacks instead of embedding the WOFF2 subsets.",
    )
    parser.add_argument(
        "--embed-images",
        action="store_true",
        help="Download remote <img> sources and inline them as data URIs.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress the output path line.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_path: Path | None = args.input or args.body
    already_themed = False
    meta: dict[str, str] = {}
    doc_title = ""
    body = ""

    if args.input:
        body, meta, doc_title, already_themed = load_document(args.input)
    elif args.body:
        body = args.body.read_text(encoding="utf-8")
    else:
        body = sys.stdin.read()

    body = sanitize_body(body)

    if args.embed_images:
        body = embed_remote_images(body)
    for url in remote_resources(body):
        warn(
            "remote resource left in place; embed it or disclose the network "
            f"dependency: {url}"
        )

    explicit_title = args.title or meta.get("title") or doc_title
    if explicit_title:
        body_without_h1, h1_text, h1_markup = first_h1(body)
        if h1_text and collapse_space(h1_text).casefold() == collapse_space(explicit_title).casefold():
            body = body_without_h1
            if h1_markup:
                warn("the first H1 contains inline markup; the masthead title uses only its text")
    else:
        body, h1_text, h1_markup = first_h1(body)
        if h1_text:
            if h1_markup:
                warn("the first H1 contains inline markup; the masthead title uses only its text")
            warn("no title supplied; using the first H1 as the title")
            explicit_title = h1_text
        elif source_path:
            warn(f"no title supplied; using the filename {source_path.stem!r} as the title")
            explicit_title = source_path.stem
        else:
            warn("no title supplied; using 'Untitled' as the title")
            explicit_title = "Untitled"

    title = collapse_space(explicit_title)
    dek = collapse_space(args.dek or meta.get("dek", ""))
    date = collapse_space(args.date or meta.get("date", ""))
    author = collapse_space(args.author or meta.get("author", ""))
    status = collapse_space(args.status or meta.get("status", ""))
    source = collapse_space(args.source or meta.get("source", ""))
    label = collapse_space(args.label or meta.get("label", "") or "Report")
    eyebrow = collapse_space(args.eyebrow or meta.get("eyebrow", "") or label)
    lang = collapse_space(args.lang or meta.get("lang", "") or "en")
    raw_tags = args.tags if args.tags is not None else meta.get("tags", "")
    tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]

    theme_source = args.theme.read_text(encoding="utf-8")
    theme_color = extract_css_token(theme_source, "bg")
    theme_css = inline_theme(theme_source, args.theme.parent, keep_fonts=not args.no_fonts)
    template = args.template.read_text(encoding="utf-8")

    output = args.output
    if output is None:
        if source_path and already_themed:
            output = source_path
        elif source_path:
            output = default_output(source_path)
        else:
            raise SystemExit("an output path is required when reading from stdin")

    document = render_document(
        template,
        lang=lang,
        title=title,
        dek=dek,
        label=label,
        eyebrow=eyebrow,
        date=date,
        author=author,
        status=status,
        source=source,
        tags=tags,
        body=body,
        theme_css=theme_css,
        theme_color=theme_color,
    )
    write_atomic(output, document)
    if not args.quiet:
        print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
