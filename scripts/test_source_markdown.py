"""Run with python3 test_source_markdown.py; no third-party test runner needed."""
import unittest
from html.parser import HTMLParser
from source_markdown import SourceMarkdown


class MarkedText(HTMLParser):
    def __init__(self, content):
        super().__init__(convert_charrefs=True)
        self.in_mark = False
        self.text = ''
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        if tag == 'mark': self.in_mark = True

    def handle_endtag(self, tag):
        if tag == 'mark': self.in_mark = False

    def handle_data(self, data):
        if self.in_mark: self.text += data


class MarkdownTests(unittest.TestCase):
    def render(self, text, phrase=None, occurrence=1, context=None):
        spans = []
        if phrase:
            start = -1
            for _ in range(occurrence): start = text.index(phrase, start + 1)
            spans = [(start, start+len(phrase), 'key')]
        md = SourceMarkdown(context or [{'text':text}])
        return md.render(text, spans)

    def test_markdown_structures(self):
        text = '# Heading\n\n**bold** and *italic* and ~~old~~.\n\n> quoted\n\n- [X] complete\n- [ ] pending\n\n1. one\n   - nested\n\n```python\nx = "<test>"\n```\n\n| A | B |\n|---|---|\n| 1 | 2 |'
        result = self.render(text)
        for tag in ['<h1 ', '<strong>bold</strong>', '<em>italic</em>', '<del>old</del>', '<blockquote>', 'type="checkbox" disabled checked', '<ol>', '<ul>', '<pre><code class="language-python">', '<table ', '<th>', '<td>']:
            self.assertIn(tag,result)
        self.assertIn('&lt;test&gt;',result)

    def test_highlight_across_inline_formatting(self):
        raw='A **very important** point with `code` and a [link](https://example.com).'
        phrase='**very important** point with `code`'
        result=self.render(raw,phrase)
        self.assertEqual(MarkedText(result).text,'very important point with code')
        self.assertIn('<strong>',result)
        self.assertIn('<code>',result)

    def test_repeat_after_link_destination(self):
        raw='[same](https://example.com/same) same same'
        result=self.render(raw,'same',occurrence=3)
        self.assertEqual(MarkedText(result).text,'same')
        self.assertIn('</a> <mark',result)
        self.assertNotIn('<a href="https://example.com/<mark',result)

    def test_reference_links_share_document_context(self):
        result=self.render('Read [the plan][p].',context=[{'text':'Read [the plan][p].'},{'text':'[p]: https://example.com/plan "Title"'}])
        self.assertIn('href="https://example.com/plan"',result)
        self.assertIn('title="Title"',result)

    def test_source_markup_is_inert(self):
        text='<script>alert(1)</script>\n\n[bad](javascript:alert%281%29) [bad](data:text/html,test)\n\n![diagram](https://example.com/tracker.png)'
        result=self.render(text)
        self.assertNotIn('<script>',result)
        self.assertNotIn('href="javascript:',result)
        self.assertNotIn('href="data:',result)
        self.assertNotIn('<img ',result)
        self.assertIn('&lt;script&gt;',result)
        self.assertIn('href="https://example.com/tracker.png"',result)

    def test_code_and_tables_keep_highlights(self):
        for text, phrase in [('```text\n**literal** <tag>\n```','**literal**'),('| A | B |\n|---|---|\n| key | **value** |','**value**')]:
            result=self.render(text,phrase)
            self.assertEqual(MarkedText(result).text,phrase if text.startswith('```') else 'value')

    def test_heading_fragments_are_namespaced(self):
        md=SourceMarkdown([{'text':'# Intro\n\n[Go](#intro)'}])
        result=md.render('# Intro\n\n[Go](#intro)',[])
        self.assertIn('id="source-heading-intro"',result)
        self.assertIn('href="#source-heading-intro"',result)


if __name__=='__main__':unittest.main()
