import html
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/dark-report"
BUILD = SKILL / "scripts/build.py"
THEME = SKILL / "assets/theme.css"
TEMPLATE = SKILL / "assets/template.html"
FIXTURES = REPO / "tests/fixtures/dark-report"


def run_build(*args, code=0):
    result = subprocess.run(
        [sys.executable, str(BUILD), *[str(arg) for arg in args]],
        capture_output=True,
        text=True,
    )
    if result.returncode != code:
        raise AssertionError(
            f"build exited {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def visible_text(markup):
    markup = re.sub(r"<(script|style)\b.*?</\1>", " ", markup, flags=re.I | re.S)
    markup = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(markup)).strip()


def token(css, name):
    match = re.search(rf"--{re.escape(name)}\s*:\s*([^;]+);", css)
    if not match:
        raise AssertionError(f"missing token --{name}")
    return match.group(1).strip()


def luminance(color):
    color = color.lstrip("#")
    channels = [int(color[index : index + 2], 16) / 255 for index in (0, 2, 4)]

    def linear(channel):
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(channel) for channel in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(first, second):
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


class DarkReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.out = self.base / "article.html"

    def build_article(self, *extra):
        return run_build(
            "--body",
            FIXTURES / "article.html",
            "--output",
            self.out,
            "--title",
            "Test Article",
            "--author",
            "Test Author",
            "--date",
            "2026-11-01",
            "--status",
            "Published",
            "--tags",
            "one, two",
            "--label",
            "Test Report",
            "--quiet",
            *extra,
        )

    def test_content_is_preserved(self):
        self.build_article()
        markup = self.out.read_text(encoding="utf-8")
        text = visible_text(markup)

        for phrase in (
            "Intro with a content link",
            "strong text",
            "emphasis",
            "inline_code()",
            "Café",
            "naïve",
            "日本語",
            "3 × 4 — all preserved",
            "<tag>",
            "First heading",
            "Café & 日本語",
            "An H3 with an existing stable ID.",
            "Résumé 日本語",
            "First bullet",
            "Second bullet with strong",
            "First ordered item",
            "Second ordered item",
            "Done item",
            "Open item",
            "RT60",
            "The time for sound to decay by 60 dB.",
            "A note callout.",
            "A tip callout.",
            "A warning callout.",
            "A danger callout.",
            "Duplicate id",
            "The duplicate heading ID is deduplicated.",
            "Table 1. A small measurement table.",
            "Bare room",
            "0.75",
            "Treated room",
            "0.35",
            "# Sabine estimate",
            "def rt60",
            "0.161",
            "A measurement you cannot repeat is a story.",
            "Studio notebook",
            "Third heading",
            "The generated ID avoids the non-heading ID above.",
            "Figure 1. A small plan diagram.",
            "How the measurement was made",
            "With a measurement microphone and a sweep.",
            "A footnote reference.",
            "A footnote that must survive.",
        ):
            self.assertIn(phrase, text)

        for fragment in (
            '<div class="table-wrap">',
            '<figure class="code">',
            'class="callout callout--note"',
            'class="callout callout--tip"',
            'class="callout callout--warn"',
            'class="callout callout--danger"',
            'class="task-list"',
            'class="footnote-ref"',
            'class="footnotes"',
            '<details class="details" open>',
            '<svg class="diagram"',
            'href="https://example.com/source"',
        ):
            self.assertIn(fragment, markup)

    def test_toc_links_match_heading_ids(self):
        self.build_article()
        markup = self.out.read_text(encoding="utf-8")
        toc = re.search(r'<nav class="toc".*?</nav>', markup, re.S)
        self.assertIsNotNone(toc)
        hrefs = re.findall(r'href="#([^"]+)"', toc.group(0))
        self.assertEqual(hrefs, ["keep-me", "keep-me-2", "third-heading-2"])
        self.assertIn('id="contents"', markup)
        for anchor in hrefs:
            self.assertIn(f'id="{anchor}"', markup)
        self.assertNotIn("notes", hrefs)
        self.assertIn('href="#contents"', markup)

    def test_heading_ids_are_preserved_and_deduplicated(self):
        self.build_article()
        markup = self.out.read_text(encoding="utf-8")
        self.assertEqual(markup.count('id="keep-me"'), 1)
        self.assertIn('id="keep-me-2"', markup)
        self.assertIn('id="stable"', markup)
        self.assertEqual(markup.count('id="third-heading"'), 1)
        self.assertIn('id="third-heading-2"', markup)
        self.assertIn('id="resume-日本語"', markup)
        self.assertIn('id="notes"', markup)

    def test_generated_id_does_not_steal_a_later_existing_id(self):
        body = self.base / "later.html"
        body.write_text(
            "<h2>Alpha</h2><h2 id=\"alpha\">Alpha existing</h2><h2>Third</h2>",
            encoding="utf-8",
        )
        out = self.base / "later-out.html"
        run_build("--body", body, "--title", "Later", "--output", out, "--quiet")
        markup = out.read_text(encoding="utf-8")
        self.assertIn('id="alpha-2"', markup)
        self.assertIn('id="alpha"', markup)
        self.assertLess(markup.index('id="alpha-2"'), markup.index('id="alpha"'))

        body.write_text(
            '<div id="beta"></div><h2 id="beta">Beta</h2><h2>Two</h2><h2>Three</h2>',
            encoding="utf-8",
        )
        out = self.base / "beta-out.html"
        run_build("--body", body, "--title", "Beta", "--output", out, "--quiet")
        markup = out.read_text(encoding="utf-8")
        self.assertEqual(markup.count('id="beta"'), 1)
        self.assertIn('id="beta-2"', markup)

    def test_data_id_is_not_treated_as_an_id(self):
        body = self.base / "data-id.html"
        body.write_text(
            '<div data-id="alpha"></div><h2 data-id="x">Alpha</h2>'
            "<h2>Two</h2><h2>Three</h2>",
            encoding="utf-8",
        )
        out = self.base / "data-id-out.html"
        run_build("--body", body, "--title", "Data ID", "--output", out, "--quiet")
        markup = out.read_text(encoding="utf-8")
        self.assertIn('id="alpha"', markup)
        self.assertNotIn('id="alpha-2"', markup)
        self.assertIn('data-id="x"', markup)
        self.assertNotIn(' id="x"', markup)

    def test_repeated_generated_ids_are_unique(self):
        body = self.base / "same.html"
        body.write_text("<h2>Same</h2><h2>Same</h2><h2>Same</h2>", encoding="utf-8")
        out = self.base / "same-out.html"
        run_build("--body", body, "--title", "Same", "--output", out, "--quiet")
        markup = out.read_text(encoding="utf-8")
        self.assertEqual(markup.count('id="same"'), 1)
        self.assertEqual(markup.count('id="same-2"'), 1)
        self.assertEqual(markup.count('id="same-3"'), 1)
        toc = re.search(r'<nav class="toc".*?</nav>', markup, re.S).group(0)
        self.assertEqual(
            re.findall(r'href="#([^"]+)"', toc),
            ["same", "same-2", "same-3"],
        )

    def test_toc_is_only_built_for_three_h2s(self):
        body = self.base / "two.html"
        body.write_text("<h2>One</h2><h2>Two</h2><p>End.</p>", encoding="utf-8")
        out = self.base / "two-out.html"
        run_build("--body", body, "--title", "Two", "--output", out, "--quiet")
        markup = out.read_text(encoding="utf-8")
        self.assertNotIn("data-dark-report-toc", markup)
        self.assertNotIn('href="#contents"', markup)

        body.write_text("<h2>One</h2><h2>Two</h2><h2>Three</h2>", encoding="utf-8")
        out = self.base / "three-out.html"
        run_build("--body", body, "--title", "Three", "--output", out, "--quiet")
        markup = out.read_text(encoding="utf-8")
        self.assertIn("data-dark-report-toc", markup)
        self.assertEqual(len(re.findall(r'<li><a href="#', markup)), 3)

    def test_metadata_is_escaped_and_missing_metadata_stays_missing(self):
        out = self.base / "escaped.html"
        run_build(
            "--body",
            FIXTURES / "article.html",
            "--title",
            'Test <Title> & "Quote"',
            "--dek",
            "A & B < C",
            "--output",
            out,
            "--quiet",
        )
        markup = out.read_text(encoding="utf-8")
        self.assertIn("<title>Test &lt;Title&gt; &amp; &quot;Quote&quot;</title>", markup)
        self.assertIn('content="Test &lt;Title&gt; &amp; &quot;Quote&quot;"', markup)
        self.assertIn("A &amp; B &lt; C", markup)
        self.assertNotIn("<Title>", markup)

        out = self.base / "missing.html"
        run_build(
            "--body",
            FIXTURES / "article.html",
            "--title",
            "Only Title",
            "--output",
            out,
            "--quiet",
        )
        markup = out.read_text(encoding="utf-8")
        for key in ("author", "date", "status", "tags", "source", "dek"):
            self.assertNotIn(f"dark-report:{key}", markup)
        for label in ("Author", "Date", "Status", "Tags", "Source"):
            self.assertNotIn(f"<dt>{label}</dt>", markup)
        self.assertNotIn('<meta name="description"', markup)

    def test_title_falls_back_to_first_h1_and_filename(self):
        body = self.base / "fallback.html"
        body.write_text(
            "<h1>Fallback Title</h1><p>Body.</p><h2>One</h2><h2>Two</h2><h2>Three</h2>",
            encoding="utf-8",
        )
        out = self.base / "fallback-out.html"
        result = run_build("--body", body, "--output", out, "--quiet")
        self.assertIn("first H1", result.stderr)
        markup = out.read_text(encoding="utf-8")
        self.assertIn("<title>Fallback Title</title>", markup)
        self.assertIn('<h1 class="doc-title">Fallback Title</h1>', markup)
        self.assertEqual(markup.count("<h1"), 1)

        body = self.base / "my-note.html"
        body.write_text("<p>No heading here.</p>", encoding="utf-8")
        out = self.base / "my-note-out.html"
        result = run_build("--body", body, "--output", out, "--quiet")
        self.assertIn("filename 'my-note'", result.stderr)
        self.assertIn("<title>my-note</title>", out.read_text(encoding="utf-8"))

        body = self.base / "markup.html"
        body.write_text(
            "<h1>Plain <em>title</em></h1><p>Body.</p><h2>One</h2><h2>Two</h2><h2>Three</h2>",
            encoding="utf-8",
        )
        out = self.base / "markup-out.html"
        result = run_build("--body", body, "--output", out, "--quiet")
        self.assertIn("inline markup", result.stderr)
        self.assertIn("<title>Plain title</title>", out.read_text(encoding="utf-8"))

    def test_existing_html_removes_external_resources_and_keeps_inline_content(self):
        out = self.base / "page-out.html"
        result = run_build(
            "--input",
            FIXTURES / "page.html",
            "--label",
            "Existing",
            "--output",
            out,
            "--quiet",
        )
        markup = out.read_text(encoding="utf-8")
        self.assertNotIn("cdn.example.com", markup)
        self.assertIn("console.log('inline');", markup)
        self.assertIn("<svg", markup)
        self.assertIn('href="https://example.com"', markup)
        self.assertIn("Keep <strong>this</strong> content.", markup)
        self.assertIn("photo.png", markup)
        self.assertIn("remote resource left in place", result.stderr)
        self.assertNotRegex(markup, r"<script\b[^>]*\bsrc=")
        self.assertNotRegex(markup, r"<link\b")
        self.assertEqual(markup.count("<h1"), 1)
        self.assertIn("<title>Existing Page</title>", markup)

    def test_offline_output_and_embedded_fonts(self):
        self.build_article()
        markup = self.out.read_text(encoding="utf-8")
        style = re.search(r"<style>(.*?)</style>", markup, re.S)
        self.assertIsNotNone(style)
        css = style.group(1)
        self.assertNotRegex(css, r'url\(\s*["\']?https?://')
        self.assertNotIn("@import", css)
        self.assertNotIn('url("fonts/', css)
        self.assertEqual(css.count("data:font/woff2;base64,"), 6)
        self.assertNotRegex(markup, r"<link\b")
        self.assertNotRegex(markup, r"<script\b[^>]*\bsrc=")
        self.assertNotRegex(markup, r"<img\b[^>]*\bsrc=\"https?://")
        self.assertNotRegex(markup, r"\b(?:src|srcset|poster)=\"https?://")
        self.assertIn('href="https://example.com/source"', markup)

    def test_rebuild_is_idempotent(self):
        self.build_article()
        run_build("--input", self.out, "--quiet")
        markup = self.out.read_text(encoding="utf-8")
        for marker in (
            "data-dark-report-header",
            "data-dark-report-toc",
            "data-dark-report-footer",
        ):
            self.assertEqual(markup.count(marker), 1)
        self.assertEqual(markup.count("<h1"), 1)
        self.assertEqual(markup.count('id="keep-me"'), 1)
        self.assertEqual(markup.count('id="keep-me-2"'), 1)
        text = visible_text(markup)
        self.assertIn("First heading", text)
        self.assertIn("A footnote that must survive.", text)
        toc = re.search(r'<nav class="toc".*?</nav>', markup, re.S).group(0)
        for anchor in re.findall(r'href="#([^"]+)"', toc):
            self.assertIn(f'id="{anchor}"', markup)

        rebuilt = self.base / "rebuilt.html"
        run_build("--input", self.out, "--output", rebuilt, "--quiet")
        other = rebuilt.read_text(encoding="utf-8")
        for marker in (
            "data-dark-report-header",
            "data-dark-report-toc",
            "data-dark-report-footer",
        ):
            self.assertEqual(other.count(marker), 1)

    def test_core_theme_tokens_and_contrast(self):
        css = THEME.read_text(encoding="utf-8")
        expected = {
            "bg": "#15120f",
            "surface": "#1d1915",
            "line": "#342c24",
            "fg": "#ede6da",
            "muted": "#9b9082",
            "accent": "#f2a33a",
            "peak": "#e5484d",
            "ok": "#9bbf8a",
            "warn": "#e0a45a",
            "danger": "#ef6468",
            "comment": "#8b8175",
            "measure": "68ch",
            "radius": "4px",
        }
        for name, value in expected.items():
            self.assertIn(f"--{name}: {value};", css)
        self.assertIn("color-scheme: dark;", css)
        self.assertIn("--display: \"Big Shoulders Display\"", css)
        self.assertIn("--body: \"IBM Plex Sans\"", css)
        self.assertIn("--mono: \"IBM Plex Mono\"", css)

        pairs = (
            ("fg", "bg", 7.0),
            ("fg", "surface", 7.0),
            ("muted", "bg", 4.5),
            ("muted", "surface", 4.5),
            ("accent", "bg", 4.5),
            ("accent", "surface", 4.5),
            ("bg", "accent", 4.5),
            ("danger", "surface", 4.5),
            ("ok", "surface", 4.5),
            ("warn", "surface", 4.5),
            ("comment", "surface", 4.5),
        )
        for foreground, background, minimum in pairs:
            self.assertGreaterEqual(
                contrast(token(css, foreground), token(css, background)),
                minimum,
                f"{foreground} on {background}",
            )
        self.assertLess(contrast(token(css, "peak"), token(css, "surface")), 4.5)

        print_section = css[css.index("@media print") :]
        self.assertEqual(token(print_section, "bg"), "#fbf8f2")
        self.assertEqual(token(print_section, "fg"), "#14110e")
        self.assertGreaterEqual(
            contrast(token(print_section, "fg"), token(print_section, "bg")), 7.0
        )

    def test_placeholder_preview_is_self_contained(self):
        markup = (SKILL / "assets/placeholder.html").read_text(encoding="utf-8")
        self.assertIn("<title>Lorem Ipsum Dolor</title>", markup)
        self.assertEqual(markup.count("<h1"), 1)
        self.assertEqual(markup.count("data-dark-report-header"), 1)
        self.assertEqual(markup.count("data-dark-report-toc"), 1)
        self.assertEqual(markup.count("data-dark-report-footer"), 1)
        self.assertEqual(len(re.findall(r'<li><a href="#', markup)), 5)
        self.assertIn("data:font/woff2;base64,", markup)
        self.assertNotRegex(markup, r"<link\b")
        self.assertNotRegex(markup, r"<script\b[^>]*\bsrc=")
        self.assertNotRegex(markup, r"<img\b")

    def test_font_files_are_local_woff2(self):
        fonts = sorted((SKILL / "assets/fonts").glob("*.woff2"))
        self.assertEqual(len(fonts), 6)
        for font in fonts:
            self.assertEqual(font.read_bytes()[:4], b"wOF2", font.name)
        css = THEME.read_text(encoding="utf-8")
        for url in re.findall(r'url\(\s*["\']?([^"\')]+)', css):
            self.assertFalse(url.startswith(("http://", "https://", "//")), url)

    def test_template_and_skill_contract(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("{{THEME_COLOR}}", template)
        self.assertNotIn("#15120f", template)
        self.assertIn("data-dark-report-body", template)
        self.assertIn("data-dark-report-header", template)
        self.assertIn("{{FOOTER}}", template)
        builder = (SKILL / "scripts/build.py").read_text(encoding="utf-8")
        self.assertIn("data-dark-report-footer", builder)

        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = re.search(r"^---\n(.*?)\n---", skill, re.S)
        self.assertIsNotNone(frontmatter)
        description = re.search(r"^description: (.*)$", frontmatter.group(1), re.M)
        self.assertIsNotNone(description)
        self.assertTrue(description.group(1).startswith("Use when"))
        self.assertLessEqual(len(description.group(1)), 1024)
        self.assertIn("references/content-mapping.md", skill)
        self.assertIn("references/theme.md", skill)

        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("[dark-report](skills/dark-report/SKILL.md)", readme)


if __name__ == "__main__":
    unittest.main()
