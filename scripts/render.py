#!/usr/bin/env python3
"""Render a defuse synthesis into an escaped, offline HTML reader."""
import argparse
import html
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_markdown import SourceMarkdown


def esc(value):
    if not isinstance(value, str):
        raise ValueError('Expected a text string')
    return html.escape(value, quote=True)


def bullets(values):
    return '<ul>' + ''.join('<li>' + esc(v) + '</li>' for v in values) + '</ul>'


def render(data):
    sections = data['sections']
    ids = [s['id'] for s in sections]
    if not ids or len(ids) != len(set(ids)) or any(not re.fullmatch(r'[a-z][a-z0-9-]*', i) for i in ids):
        raise ValueError('Sections need unique lowercase slug IDs')
    titles = {s['id']: s['title'] for s in sections}
    original = data['original']
    original_ids = [block['id'] for block in original]
    if not original_ids or len(original_ids) != len(set(original_ids)) or any(not re.fullmatch(r'[a-z][a-z0-9-]*', i) for i in original_ids):
        raise ValueError('Original blocks need unique lowercase slug IDs')
    source_format = data.get('source_format', 'markdown')
    if source_format not in ('markdown', 'text'):
        raise ValueError('source_format must be markdown or text')
    markdown = SourceMarkdown(original) if source_format == 'markdown' else None
    original_html = ''
    for block in original:
        raw = block['text']
        spans = []
        for highlight in block.get('highlights', []):
            phrase = highlight['text']
            occurrence = highlight.get('occurrence', 1)
            if not phrase or type(occurrence) is not int or occurrence < 1:
                raise ValueError('Highlight needs nonempty exact text and a positive occurrence')
            start = -1
            for _ in range(occurrence):
                start = raw.find(phrase, start + 1)
                if start < 0:
                    raise ValueError('Highlight does not match original text')
            kind = highlight.get('kind', 'key')
            if kind not in ('key', 'uncertain'):
                raise ValueError('Unknown source highlight kind')
            spans.append((start, start + len(phrase), kind))
        cursor, marked = 0, ''
        for start, end, kind in sorted(spans):
            if start < cursor:
                raise ValueError('Source highlights must not overlap')
            label = 'Key point' if kind == 'key' else 'Unresolved'
            marked += esc(raw[cursor:start]) + f'<mark class="source-{kind}" title="{label}">' + esc(raw[start:end]) + '</mark>'
            cursor = end
        marked += esc(raw[cursor:])
        if markdown:
            formatted = markdown.render(raw, sorted(spans))
        else:
            tag = 'h3' if block.get('heading') else 'p'
            formatted = f'<{tag} class="plain-source">{marked}</{tag}>'
        original_html += (f'<div class="original-block" id="original-{esc(block["id"])}">'
                          + '<div class="source-rendered">' + formatted + '</div>'
                          + '<pre class="source-raw">' + marked + '</pre></div>')
    for section in sections:
        if not section['original_ids'] or any(ref not in original_ids for ref in section['original_ids']):
            raise ValueError('Every reading section must reference original block IDs')

    def source_link(refs, label):
        if not refs or any(ref not in original_ids for ref in refs):
            raise ValueError('Source location references must resolve to original blocks')
        targets = ' '.join('original-' + ref for ref in refs)
        return (f'<a class="source-ref" href="#original-{esc(refs[0])}" '
                f'data-source-refs="{esc(targets)}" aria-controls="{esc(targets)}">'
                + esc(label) + '</a>')

    def links(refs):
        if not refs or any(r not in titles for r in refs):
            raise ValueError('Section references must be nonempty and resolve')
        return ' · '.join(f'<a href="#section-{esc(r)}">{esc(titles[r])}</a>' for r in refs)

    def questions(items, closing=False):
        if not items:
            return ''
        out = '<h3>Questions to consider</h3><p class="label">Generated from the document</p><ul class="questions">'
        for item in items:
            out += '<li><p>' + esc(item['question']) + '</p><p class="muted">' + esc(item['basis']) + '</p>'
            if closing:
                out += '<p class="source-links">' + links(item['sections']) + '</p>'
            out += '</li>'
        return out + '</ul>'

    nav = '<details class="topic-nav"><summary>Topics <span class="toc-count">' + str(len(sections)) + ' sections</span><svg class="toc-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></summary><ol>'
    nav += '<li><a href="#overview">Overview &amp; themes</a></li>'
    nav += ''.join(f'<li><a href="#section-{esc(s["id"])}"><span class="toc-number">{n:02d}</span>{esc(s["title"])}</a></li>' for n, s in enumerate(sections, 1))
    nav += '<li><a href="#closing">What to take away</a></li></ol></details><span class="current-section-title" id="current-section-title" hidden>Overview &amp; themes</span>'
    content = '<section id="overview"><p class="eyebrow">/defuse · Reading edition</p><h1>' + esc(data['title']) + '</h1>'
    content += '<p class="muted source-name">' + esc(data['source']) + '</p><div id="mobile-original-slot"></div><div class="tldr"><h2>TL;DR</h2>' + bullets(data['tldr']) + '</div>'
    content += '<h2>The themes</h2><div class="themes">'
    for theme in data['themes']:
        content += '<article><h3>' + esc(theme['title']) + '</h3><p>' + esc(theme['description']) + '</p><p class="source-links">' + links(theme['sections']) + '</p></article>'
    content += '</div></section><div class="controls" hidden><span>Reading view</span><button type="button" id="expand">Expand all</button><button type="button" id="collapse">Collapse all</button><label><input type="checkbox" id="highlights" checked> Highlights</label></div>'
    for n, section in enumerate(sections, 1):
        if not section['sources']:
            raise ValueError('Each section needs a source location')
        content += f'<details class="reading-section" id="section-{esc(section["id"])}" open><summary><span class="section-number">{n:02d}</span><span><h2>{esc(section["title"])}</h2><span class="gist">{esc(section["gist"])}</span></span></summary><div class="section-body">'
        content += '<p class="original-links">Original: ' + ' · '.join(source_link([ref], f'Passage {original_ids.index(ref) + 1}') for ref in section['original_ids']) + '</p>'
        for block in section['blocks']:
            if 'example' in block:
                example = block['example']
                origin = example.get('origin')
                if origin not in ('source', 'illustration'):
                    raise ValueError('Example origin must be source or illustration')
                label = 'Example from the source' if origin == 'source' else 'Illustrative example'
                link_label = 'Source example' if origin == 'source' else 'Concept in the source'
                reference = source_link(example['original_ids'], link_label)
                content += ('<aside class="concept-example"><p class="example-label">' + label + '</p><h3>'
                            + esc(example['title']) + '</h3><p class="example-text">' + esc(example['text'])
                            + '</p><p class="example-source">' + reference + '</p></aside>')
            elif 'heading' in block:
                content += '<h3>' + esc(block['heading']) + '</h3>'
            elif 'items' in block:
                content += bullets(block['items'])
            else:
                kind = block.get('kind', '')
                if kind not in ('', 'key', 'uncertain'):
                    raise ValueError('Unknown paragraph kind')
                label = {'key': 'Key point', 'uncertain': 'Unresolved'}.get(kind)
                prefix = '<span class="annotation">' + label + '</span>' if label else ''
                content += '<p class="' + kind + '">' + prefix + esc(block['text']) + '</p>'
        if section['takeaways']:
            content += '<div class="takeaways"><h3>Take away</h3>' + bullets(section['takeaways']) + '</div>'
        content += questions(section['questions'])
        content += '<details class="sources"><summary>Source locations &amp; excerpts</summary>'
        for source in section['sources']:
            location = source_link(source.get('original_ids', section['original_ids']), source['location'])
            url = source.get('url', '')
            parsed = urlsplit(url)
            if parsed.scheme in ('http', 'https') and parsed.netloc:
                location += ' · <a href="' + esc(url) + '" rel="noreferrer">Open source</a>'
            content += '<p class="source-location">' + location + '</p>'
            if source.get('quote'):
                content += '<blockquote>' + esc(source['quote']) + '</blockquote>'
        content += '</details></div></details>'
    content += '<section id="closing"><p class="eyebrow">Across the document</p><h2>What to take away</h2>' + bullets(data['takeaways']) + questions(data['questions'], True) + '</section>'
    content += '<footer><h2>About this reading edition</h2><p>' + esc(data['coverage']) + '</p><p class="muted">A synthesis of the supplied source. Claims are attributed to that source and have not been independently verified.</p></footer>'
    assets = Path(__file__).resolve().parent.parent / 'assets'
    template = (assets / 'reader.html').read_text(encoding='utf-8')
    document_id = hashlib.sha256('\n\n'.join(b['text'] for b in original).encode('utf-8')).hexdigest()[:24]
    icon = (assets / 'defuse-icon.svg').read_text(encoding='utf-8').strip()
    brand_icon = icon.replace('<svg ', '<svg class="brand-icon" aria-hidden="true" focusable="false" ', 1)
    favicon = icon.replace('viewBox="0 0 204 350"', 'viewBox="-88 -15 380 380"').replace('fill="currentColor"', 'fill="#bd291d"')
    slots = {'ICON': brand_icon, 'FAVICON': 'data:image/svg+xml,' + quote(favicon, safe=''), 'TITLE': esc(data['title']), 'NAV': nav, 'CONTENT': content, 'ORIGINAL': original_html,
             'DOCUMENT_ID': document_id, 'COMMENTS_CSS': (assets / 'comments.css').read_text(encoding='utf-8'),
             'COMMENTS_JS': (assets / 'comments.js').read_text(encoding='utf-8')}
    return re.sub(r'@@(TITLE|NAV|CONTENT|ORIGINAL|DOCUMENT_ID|COMMENTS_CSS|COMMENTS_JS|ICON|FAVICON)@@', lambda m: slots[m.group(1)], template)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error('Input and output must be different files')
    try:
        result = render(json.loads(args.input.read_text(encoding='utf-8')))
    except (KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    args.output.write_text(result, encoding='utf-8')
    print(args.output.resolve())


if __name__ == '__main__':
    main()
