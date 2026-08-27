"""URL 을 ASCII 표기 하나로 정규화한다. 못 바꾸면 None — 예외는 밖으로 내보내지 않는다."""
import urllib.parse

_STRIPPED = dict.fromkeys(map(ord, "\t\r\n"))  # urlsplit 이 URL 에서 떼어내는 문자
_DEFAULT_PORT = {"http": "80", "https": "443"}


def domain_key(url):
    """**예의 계약이 세는 단위.** 같은 서버는 한 칸이다.

    호스트는 대소문자 무관이고 `:80`/`:443` 은 각 스킴의 기본 포트라
    `http://b.test` · `http://B.test` · `http://b.test:80` 은 **같은 서버**다.
    날 `netloc` 으로 세면 칸이 셋으로 갈려, 3초를 요구한 서버가 2밀리초 안에
    요청 넷을 받는다(실측). 그것이 절대 조건 위반이라 이 함수가 있다.

    **URL 동일성이 아니다** — 위 셋은 이 뒤에도 각각 수집되고 각각 저장된다
    (digest `[5]` 의 URL 정규화는 별개의 수술이다). 여기서 같아지는 것은
    간격·in-flight·`Crawl-delay` 를 세는 칸 하나뿐이다.

    **문자열로만 가른다.** `urlsplit(...).port` 는 `:abc`·`:99999` 에 ValueError 를
    던지는데 지금 `netloc` 은 절대 안 던진다 — 열쇠를 만들다 크롤 루프를 죽이는 것은
    이 함수가 막으려는 것보다 나쁘다. 읽을 수 없는 포트는 **자기 칸에 그대로 둔다**.
    """
    try:
        split = urllib.parse.urlsplit(url)
    except ValueError:  # 닫히지 않은 IPv6 리터럴 — urlsplit 조차 못 읽는다
        return url.partition("://")[2].partition("/")[0].lower()
    netloc = split.netloc.rpartition("@")[2]  # userinfo 는 서버가 아니다
    host, colon, port = netloc.rpartition(":")
    if not colon or "]" in port:  # 포트가 아니라 IPv6 리터럴의 콜론이다
        host, port = netloc, ""
    if port == _DEFAULT_PORT.get(split.scheme):
        port = ""
    return host.lower() + (":" + port if port else "")


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
