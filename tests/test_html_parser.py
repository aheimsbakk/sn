import unittest

from grc.html_parser import parse_html_transcript


SAMPLE_HTML = """
<html>
  <head>
    <title>Security Now! Episode 42 - Ancient Bugs</title>
    <meta name="description" content="HTML fallback description." />
  </head>
  <body>
    <nav>Home</nav>
    <h1>Security Now! Episode 42 - Ancient Bugs</h1>
    <p>Leo Laporte: Intro text.</p>
    <p>Steve Gibson: Deep dive.</p>
    <footer>Copyright GRC</footer>
  </body>
</html>
"""


class HtmlParserTests(unittest.TestCase):
    def test_parses_html_fallback(self) -> None:
        record = parse_html_transcript(
            SAMPLE_HTML, transcript_url="https://example.com/sn-0042.htm"
        )
        self.assertEqual(record.episode, 42)
        self.assertEqual(record.title, "Ancient Bugs")
        self.assertEqual(record.description, "HTML fallback description.")
        self.assertEqual(record.transcript_lines[0], "**Leo Laporte:** Intro text.")
