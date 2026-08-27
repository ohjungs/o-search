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
        try:
            absolute = urllib.parse.urljoin(base_url, href)
        except ValueError:
            continue  # 닫히지 않은 IPv6 리터럴 등. 링크 하나가 크롤을 죽이지 않는다
        if not absolute.startswith(("http://", "https://")):
            continue
        # 정규화가 seen 앞 — 여러 표기가 1건이 된다. fragment 도 저기서 뗀다
        # (여기서만 떼면 시드·리다이렉트 경로에는 그 보정이 없다)
        absolute = urls.normalize(absolute)
        if absolute is None:
            continue
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out
