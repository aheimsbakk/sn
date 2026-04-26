import unittest

from grc.archive_index import discover_yearly_archive_urls, parse_archive_entries


SAMPLE_ARCHIVE = """
<html><body>
  <a href="securitynow.htm">Main</a>
  <a href="sn/sn-1074.txt">SN 1074 transcript</a>
  <a href="sn/sn-1074.htm">SN 1074 HTML</a>
  <a href="/sn/past/2025.htm">2025 archive</a>
  <a href="/sn/past/2005.htm">2005 archive</a>
</body></html>
"""


class ArchiveIndexTests(unittest.TestCase):
    def test_discovers_yearly_archives(self) -> None:
        urls = discover_yearly_archive_urls(
            "https://www.grc.com/securitynow.htm", SAMPLE_ARCHIVE
        )
        self.assertEqual(
            urls,
            [
                "https://www.grc.com/sn/past/2025.htm",
                "https://www.grc.com/sn/past/2005.htm",
            ],
        )

    def test_parses_archive_entries(self) -> None:
        entries = parse_archive_entries(
            "https://www.grc.com/securitynow.htm", SAMPLE_ARCHIVE
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].episode, 1074)
        transcript_txt_url = entries[0].transcript_txt_url
        self.assertIsNotNone(transcript_txt_url)
        self.assertTrue(str(transcript_txt_url).endswith("sn-1074.txt"))
