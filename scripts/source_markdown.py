"""Offline Markdown rendering with escaped HTML and source-aligned highlights."""
import difflib
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent / '_vendor'))
import mistune


class ReaderRenderer(mistune.HTMLRenderer):
    def __init__(self):
        super().__init__(escape=True)
        self.heading_counts = {}

    def link(self, text, url, title=None):
        # Decode before checking, to reject encoded schemes/control characters.
        normalized = html.unescape(unquote(url)).strip()
        try:
            scheme = urlsplit(re.sub(r'[\x00-\x20\x7f]', '', normalized)).scheme.lower()
        except ValueError:
            return text
        if scheme not in ('', 'https', 'http', 'mailto') or normalized.startswith('//'):
            return text
        safe = html.escape(url, quote=True)
        if url.startswith('#'):
            safe = '#source-heading-' + html.escape(url[1:], quote=True)
        attrs = ' rel="noreferrer noopener"'
        if scheme in ('http', 'https'):
            attrs += ' target="_blank"'
        if title:
            attrs += ' title="' + html.escape(title, quote=True) + '"'
        return '<a href="' + safe + '"' + attrs + '>' + text + '</a>'

    def image(self, text, url, title=None):
        # Preserve image references without making remote requests on document open.
        return '<span class="source-image">Image: ' + self.link(text or 'image reference', url, title) + '</span>'

    def heading(self, text, level, **attrs):
        plain = Fragment(text).text
        slug = re.sub(r'[^\w\- ]', '', plain.lower()).strip().replace(' ', '-') or 'heading'
        count = self.heading_counts.get(slug, 0)
        self.heading_counts[slug] = count + 1
        suffix = '-' + str(count) if count else ''
        return f'<h{level} id="source-heading-{html.escape(slug + suffix, quote=True)}">{text}</h{level}>\n'

    def table(self, text):
        head = text.split('</thead>', 1)[0]
        classes = ['markdown-table']
        if re.search(r'<th[^>]*>\s*#\s*</th>', head):
            classes.append('numbered-table')
        if len(re.findall(r'<th(?:\s|>)', head)) > 3:
            classes.append('wide-table')
        return ('<div class="table-scroll" role="region" tabindex="0" '
                'aria-label="Original document table; scroll horizontally if needed">'
                '<table class="' + ' '.join(classes) + '">\n' + text + '</table></div>\n')


class Fragment(HTMLParser):
    """Separate trusted renderer tags and text, so highlighting cannot split tags."""
    def __init__(self, content):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.text = ''
        self.feed(content)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.parts.append(('tag', self.get_starttag_text(), 0))

    def handle_startendtag(self, tag, attrs):
        self.parts.append(('tag', self.get_starttag_text(), 0))

    def handle_endtag(self, tag):
        self.parts.append(('tag', '</' + tag + '>', 0))

    def handle_data(self, text):
        self.parts.append(('text', text, len(self.text)))
        self.text += text

    def highlighted(self, ranges):
        result = []
        for type_, value, offset in self.parts:
            if type_ == 'tag':
                result.append(value)
                continue
            cursor = 0
            for start, end, kind in ranges:
                left, right = max(0, start - offset), min(len(value), end - offset)
                if left >= right:
                    continue
                result.append(html.escape(value[cursor:left]))
                label = 'Key point' if kind == 'key' else 'Unresolved'
                result.append(f'<mark class="source-{kind}" title="{label}">' + html.escape(value[left:right]) + '</mark>')
                cursor = right
            result.append(html.escape(value[cursor:]))
        return ''.join(result)


class SourceMarkdown:
    def __init__(self, blocks):
        self.renderer = ReaderRenderer()
        self.md = mistune.create_markdown(renderer=self.renderer, plugins=['table', 'task_lists', 'strikethrough'])
        # Parse document context once so reference-style links can cross passage boundaries.
        _, state = self.md.parse('\n\n'.join(block['text'] for block in blocks))
        self.refs = state.env.get('ref_links', {})
        self.renderer.heading_counts.clear()

    def render(self, raw, spans):
        state = mistune.BlockState()
        state.env['ref_links'] = dict(self.refs)
        rendered, _ = self.md.parse(raw, state)
        fragment = Fragment(rendered)
        if not spans:
            return rendered
        # Align visible characters with the verbatim source, excluding Markdown delimiters
        # and link destinations. Marks are inserted in text nodes, never into HTML syntax.
        matches = difflib.SequenceMatcher(None, raw, fragment.text, autojunk=False).get_matching_blocks()
        projected = []
        for start, end, kind in spans:
            matched = []
            for a, b, size in matches:
                left, right = max(start, a), min(end, a + size)
                if left < right:
                    matched.append((b + left - a, b + right - a, kind))
            if not matched or not any(fragment.text[a:b].strip() for a, b, _ in matched):
                raise ValueError('Markdown highlight has no visible text; highlight its label rather than syntax or URL')
            projected.extend(matched)
        projected.sort()
        # Merge adjacent visible runs of the same highlight category.
        merged = []
        for start, end, kind in projected:
            if merged and merged[-1][1] == start and merged[-1][2] == kind:
                merged[-1] = (merged[-1][0], end, kind)
            else:
                merged.append((start, end, kind))
        return fragment.highlighted(merged)
