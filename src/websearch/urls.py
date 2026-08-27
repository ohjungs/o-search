"""URL 을 표기 하나로 모은다. 못 바꾸면 None — 예외는 밖으로 내보내지 않는다.

자가 셋이다. `to_ascii` 는 **표기를 ASCII 로**, `domain_key` 는 **어느 서버인가**를,
`normalize` 는 **어느 문서인가**를 정한다. 뒤의 둘은 앞의 것 위에 얹힌다.
"""
import re
import urllib.parse

_STRIPPED = dict.fromkeys(map(ord, "\t\r\n"))  # urlsplit 이 URL 에서 떼어내는 문자
_DEFAULT_PORT = {"http": "80", "https": "443"}
_TRIPLET = re.compile(r"%[0-9a-fA-F]{2}")  # 퍼센트 3연. `%` 하나나 `%zz` 는 안 걸린다


def _split(url):
    """`urlsplit` 이되 **던지지 않는다**. `(스킴, netloc)` 만 준다.

    `urlsplit` 은 닫히지 않은 IPv6 리터럴(`http://[::1/x`)에 ValueError 를 던진다.
    그런 URL 하나가 링크에 섞였다고 크롤 전체가 죽는 것이 이 함수가 막는 것이다.
    못 읽으면 문자열로 가른다 — 그 URL 은 자기 칸에 그대로 남는다.
    """
    try:
        split = urllib.parse.urlsplit(url)
        return split.scheme, split.netloc
    except ValueError:
        scheme, _, rest = url.partition("://")
        return scheme.lower(), rest.partition("/")[0]


def scheme_of(url):
    """`http`/`https`. 못 읽는 URL 에도 안 던진다 — `_split` 과 같은 자다."""
    return _split(url)[0]


def domain_key(url):
    """**예의 계약이 세는 단위.** 같은 서버는 한 칸이다.

    호스트는 대소문자 무관이고 `:80`/`:443` 은 각 스킴의 기본 포트라
    `http://b.test` · `http://B.test` · `http://b.test:80` 은 **같은 서버**다.
    날 `netloc` 으로 세면 칸이 셋으로 갈려, 3초를 요구한 서버가 2밀리초 안에
    요청 넷을 받는다(실측). 그것이 절대 조건 위반이라 이 함수가 있다.

    **URL 동일성이 아니다** — 여기서 같아지는 것은 간격·in-flight·`Crawl-delay` 를
    세는 칸 하나뿐이고, 어느 문서인가는 `normalize` 가 정한다. 018 이후로 위 셋은
    `normalize` 가 URL 이 태어나는 자리에서 먼저 접으므로 **이 함수까지 갈린 채로
    오지 않는다** — 그래도 여기 접기를 지우지 않는다. 정규화를 안 지나는 호출처가
    생기는 날 예의 계약을 지키는 것은 이 줄이다(두 번째 방어선).

    **문자열로만 가른다.** `urlsplit(...).port` 는 `:abc`·`:99999` 에 ValueError 를
    던지는데 `netloc` 은 안 던진다 — 열쇠를 만들다 크롤 루프를 죽이는 것은
    이 함수가 막으려는 것보다 나쁘다. 읽을 수 없는 포트는 **자기 칸에 그대로 둔다**.
    """
    scheme, netloc = _split(url)  # 던지지 않는 파싱은 저기 한 곳에서만 한다
    netloc = netloc.rpartition("@")[2]  # userinfo 는 서버가 아니다
    host, colon, port = netloc.rpartition(":")
    if not colon or "]" in port:  # 포트가 아니라 IPv6 리터럴의 콜론이다
        host, port = netloc, ""
    if port == _DEFAULT_PORT.get(scheme):
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


def normalize(url):
    """**같은 문서는 한 URL 이다.** 못 바꾸면 None.

    `domain_key` 가 도메인 열쇠에 한 일을 URL 전체에 한다 — 수집·저장·색인의
    열쇠가 이것이라 표기가 셋이면 같은 문서를 세 번 받고 세 번 저장하고 세 번
    색인한다. `to_ascii` 위에 얹는다: 저쪽 계약("ASCII 는 한 글자도 안 바꾼다")은
    멱등성과 이중 인코딩 방지를 한 규칙으로 사는 것이라 건드리지 않는다.

    거는 것은 **RFC 3986 6.2.2 가 의미를 안 바꾼다고 인정하는 것 중 다섯**이다:
    스킴 소문자 · 호스트 소문자 · 스킴별 기본 포트 제거 · 빈 경로 `/` ·
    퍼센트 3연 hex 대문자. **점 세그먼트(6.2.2.3)는 안 접는다** — 상대 링크는
    `urljoin` 이 이미 접고, 절대 href 의 `/a/../p` 는 실물에서 중복원으로 잰 적이
    없다(digest 후보). 여기에 **프래그먼트 제거**를 더한다: `#` 뒤는 요청에 안 실려
    서버가 주는 문서가 같다. `links` 만 자기 앞에서 떼고 있었는데, 시드와 리다이렉트
    최종 URL 은 그쪽을 안 지난다 — 열쇠를 정하는 자리는 여기 하나다.
    앞의 셋은 `domain_key` 가 이미 하므로 그것을 부른다
    (다만 `domain_key` 가 떼는 `userinfo@` 는 도로 붙인다 — URL 에서 떼면
    요청 내용이 바뀐다). **끝 슬래시 일반화(`/p/` ↔ `/p`)는 안 한다** — 동치가
    아니라 휴리스틱이고, 서버가 다른 문서를 낼 수 있다. 경로·질의의 대소문자도
    그대로 둔다.

    파싱은 `_split` 한 곳에서만 한다 — 못 읽는 URL 에도 안 던진다 (digest [7]).
    """
    url = to_ascii(url)
    if url is None:
        return None
    # `urlsplit` 이 떼는 것을 **자르기 전에** 뗀다. 안 떼면 `_split` 이 준 netloc 길이가
    # 원본보다 짧아 아래 자르기가 밀린다 — `http://a\tcom/p` 가 `http://acom/m/p`,
    # 즉 **다른 호스트**가 된다(실측). `to_ascii` 는 비ASCII 가지에서만 이것을 한다
    url = url.translate(_STRIPPED).partition("#")[0]
    mark = url.find("://")
    if mark < 0:  # 스킴 없는 상대 URL. 호출부가 절대 URL 만 넘기므로 도달하지 않는다
        return url
    scheme, netloc = _split(url)
    tail = url[mark + 3 + len(netloc):]
    userinfo, at, _ = netloc.rpartition("@")
    if not tail.startswith("/"):  # 빈 경로는 `/` 와 동치 (6.2.3). `?`·`#` 앞에도 붙는다
        tail = "/" + tail
    return "%s://%s%s%s" % (scheme, userinfo + at, domain_key(url),
                            _TRIPLET.sub(lambda m: m.group().upper(), tail))
