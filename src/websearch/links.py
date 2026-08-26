"""HTML 에서 <a href> 를 절대 http(s) URL 로 뽑는다. fragment 제거, 순서 유지 중복 제거."""
import html.parser
import urllib.parse

from websearch import urls


class _AnchorParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.hrefs.append(value)


def extract(base_url, html_text):
    parser = _AnchorParser()
    parser.feed(html_text)
    out = []
    seen = set()
    for href in parser.hrefs:
        absolute = urllib.parse.urljoin(base_url, href)
        absolute, _ = urllib.parse.urldefrag(absolute)
        if not absolute.startswith(("http://", "https://")):
            continue
        absolute = urls.to_ascii(absolute)  # 정규화가 seen 앞 — 두 표기가 1건으로 합쳐진다
        if absolute is None:
            continue
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out
