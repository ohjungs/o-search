"""URL 을 ASCII 표기 하나로 정규화한다. 못 바꾸면 None — 예외는 밖으로 내보내지 않는다."""
import urllib.parse

_STRIPPED = dict.fromkeys(map(ord, "\t\r\n"))  # urlsplit 이 URL 에서 떼어내는 문자


def _quoted(text):
    """비ASCII 문자만 하나씩 퍼센트 인코딩. ASCII 구분자(? & = / # %)는 그대로 둔다."""
    return "".join(c if c.isascii() else urllib.parse.quote(c) for c in text)


def _ascii_netloc(netloc):
    """userinfo@host:port 에서 host 만 IDNA. 호스트가 거부되면 UnicodeError 가 난다."""
    userinfo, at, hostport = netloc.rpartition("@")
    host, colon, port = hostport.partition(":")
    # ponytail: 비ASCII netloc 에만 온다 — IPv6 리터럴은 ASCII 라 여기까지 오지 않는다
    return _quoted(userinfo) + at + host.encode("idna").decode("ascii") + colon + port


def to_ascii(url):
    """URL 의 ASCII 표기. 바꿀 수 없으면 None.

    **ASCII 만 든 URL 은 한 글자도 바꾸지 않고 그대로 돌려준다** — 회귀 위험이 전부
    여기 있다. 덕분에 멱등이고, 이미 퍼센트 인코딩된 URL 을 다시 인코딩하는
    사고(`%` → `%25`)도 이 규칙 하나로 막힌다.

    비ASCII 도 같은 규칙을 따른다 — 원본 문자열 위에서 호스트와 비ASCII 문자만
    갈아끼운다. 분해 후 재조립(`urlunsplit`)이 아니라서 빈 `?`·`#` 처럼
    재조립이 삼키는 것이 없다.
    """
    if url.isascii():
        return url
    try:
        url = url.translate(_STRIPPED)  # urlsplit 이 떼는 것을 먼저 뗀다 — 아래 치환의 전제
        netloc = urllib.parse.urlsplit(url).netloc
        if not netloc.isascii():
            url = url.replace(netloc, _ascii_netloc(netloc), 1)
        return _quoted(url)
    except (UnicodeError, ValueError):
        # 서로게이트·IDNA 거부(빈 라벨·63자 초과). 크롤 루프를 죽이지 않는다
        return None
